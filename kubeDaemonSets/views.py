import json
from datetime import datetime, timezone

from django.http import HttpResponse
from django.shortcuts import render
from kubernetes.client import ApiException

from appConfig.kubeconfig import list_daemon_sets, list_daemon_sets_for_all_namespaces, read_namespaced_daemon_set
from appConfig.settings import logger
from appConfig.utils import get_cluster_client


def all_daemon_sets_page(request):
    """
    Displays all DaemonSets across all namespaces in the selected Kubernetes cluster.
    """
    cluster, error = get_cluster_client(request)
    if error:
        return HttpResponse(error, status=500)

    try:
        # Get all namespaces
        all_namespaces = cluster.core_v1.list_namespace().items

        # Get all DaemonSets across all namespaces
        daemon_sets = list_daemon_sets_for_all_namespaces(cluster)
        if not daemon_sets:
            daemon_sets = {"items": []}

        # Process daemon_sets to add age and other useful information
        processed_daemon_sets = []
        for daemon_set in daemon_sets.items:
            creation_time = daemon_set.metadata.creation_timestamp
            if creation_time:
                age_timedelta = datetime.now(timezone.utc) - creation_time
                age_hours = age_timedelta.total_seconds() / 3600
                age_str = f"{int(age_hours)}h" if age_hours < 24 else f"{int(age_hours / 24)}d"
            else:
                age_str = "N/A"

            # Calculate readiness
            desired_count = daemon_set.status.desired_number_scheduled or 0
            current_count = daemon_set.status.current_number_scheduled or 0
            readiness = f"{current_count}/{desired_count}"

            processed_daemon_sets.append({
                'name': daemon_set.metadata.name,
                'namespace': daemon_set.metadata.namespace,
                'desired': desired_count,
                'current': current_count,
                'readiness': readiness,
                'age': age_str,
                'details_url': f"/daemonsets/{daemon_set.metadata.namespace}/{daemon_set.metadata.name}/",
            })

        kubectl_command = {
            'get': "kubectl get daemonsets --all-namespaces",
            'yaml': "kubectl get daemonsets --all-namespaces -o yaml",
            'describe': "kubectl describe daemonsets --all-namespaces",
            'create': "kubectl create -f daemonset.yaml",
            'edit': "kubectl edit daemonset <daemonset-name> -n <namespace>",
            'delete': "kubectl delete daemonset <daemonset-name> -n <namespace>",
            'rollout': "kubectl rollout status daemonset/<daemonset-name> -n <namespace>",
        }

        context = {
            'namespaces': all_namespaces,
            'daemon_sets': daemon_sets.items,
            'processed_daemon_sets': processed_daemon_sets,
            'kubectl_command': kubectl_command,
        }

        return render(request, 'kubeDaemonSets/all-daemon-sets.html', context)

    except ApiException as e:
        error_message = f"API Error: {e.reason or 'An unknown API error occurred.'}"
        logger.error(f"API Exception in all_daemon_sets_page: {error_message}")
        return HttpResponse(error_message, status=e.status if e.status else 500)
    except Exception as e:
        error_message = f"Unexpected Error: {str(e)}"
        logger.error(f"Unexpected Exception in all_daemon_sets_page: {error_message}")
        return HttpResponse(error_message, status=500)


def daemon_set_details_page(request, namespace, daemon_set_name):
    """
    Displays detailed information about a specific DaemonSet.
    """
    cluster, error = get_cluster_client(request)
    if error:
        return HttpResponse(error, status=500)

    try:
        daemon_set = read_namespaced_daemon_set(cluster, daemon_set_name, namespace)
        if not daemon_set:
            return HttpResponse("DaemonSet not found", status=404)

        # Get pods managed by this daemon_set
        selector = ""
        if daemon_set.spec.selector and daemon_set.spec.selector.match_labels:
            selector_parts = []
            for key, value in daemon_set.spec.selector.match_labels.items():
                selector_parts.append(f"{key}={value}")
            selector = ",".join(selector_parts)

        pods = []
        if selector:
            try:
                pod_list = cluster.core_v1.list_namespaced_pod(
                    namespace=namespace,
                    label_selector=selector
                )
                pods = pod_list.items
            except ApiException as e:
                logger.error(f"Failed to list pods for daemon_set '{daemon_set_name}': {e}")

        # Get events related to this daemon_set
        events = []
        try:
            event_list = cluster.core_v1.list_namespaced_event(
                namespace=namespace,
                field_selector=f"involvedObject.name={daemon_set_name},involvedObject.kind=DaemonSet"
            )
            events = event_list.items
        except ApiException as e:
            logger.error(f"Failed to list events for daemon_set '{daemon_set_name}': {e}")

        # Format events
        formatted_events = []
        for event in events:
            first_seen = event.first_timestamp.replace(tzinfo=timezone.utc).astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S") if event.first_timestamp else ''
            last_seen = event.last_timestamp.replace(tzinfo=timezone.utc).astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S") if event.last_timestamp else ''
            formatted_events.append({
                'type': event.type,
                'reason': event.reason,
                'message': event.message,
                'first_seen': first_seen,
                'last_seen': last_seen,
            })

        kubectl_commands = [
            {
                'command': f"kubectl get daemonset {daemon_set_name} -n {namespace}",
                'explanation': "Lists details about the specified DaemonSet."
            },
            {
                'command': f"kubectl get daemonset {daemon_set_name} -n {namespace} -o yaml",
                'explanation': "Outputs the DaemonSet's configuration in YAML format."
            },
            {
                'command': f"kubectl describe daemonset {daemon_set_name} -n {namespace}",
                'explanation': "Provides detailed information about the DaemonSet."
            },
            {
                'command': f"kubectl rollout status daemonset/{daemon_set_name} -n {namespace}",
                'explanation': "Shows the status of the rollout for the DaemonSet."
            },
            {
                'command': f"kubectl rollout history daemonset/{daemon_set_name} -n {namespace}",
                'explanation': "Shows the rollout history of the DaemonSet."
            },
            {
                'command': f"kubectl rollout undo daemonset/{daemon_set_name} -n {namespace}",
                'explanation': "Rolls back to the previous revision of the DaemonSet."
            },
            {
                'command': f"kubectl edit daemonset {daemon_set_name} -n {namespace}",
                'explanation': "Edits the DaemonSet's configuration."
            },
            {
                'command': f"kubectl delete daemonset {daemon_set_name} -n {namespace}",
                'explanation': "Deletes the specified DaemonSet."
            },
        ]

        context = {
            'daemon_set': daemon_set,
            'pods': pods,
            'events': formatted_events,
            'selected_namespace': namespace,
            'daemon_set_name': daemon_set_name,
            'kubectl_commands': kubectl_commands,
        }

        return render(request, 'kubeDaemonSets/daemon-set-details.html', context)

    except ApiException as e:
        if e.status == 404:
            return HttpResponse("DaemonSet not found", status=404)
        else:
            error_message = f"An error occurred: {e.reason or 'Unknown error'}"
            logger.error(f"API Exception in daemon_set_details_page: {error_message}")
            return HttpResponse(error_message, status=e.status if e.status else 500)
    except Exception as e:
        error_message = f"Unexpected Error: {str(e)}"
        logger.error(f"Unexpected Exception in daemon_set_details_page: {error_message}")
        return HttpResponse(error_message, status=500)


def daemon_set_json_page(request, namespace, daemon_set_name):
    """
    Displays the JSON representation of a specific DaemonSet.
    """
    cluster, error = get_cluster_client(request)
    if error:
        return HttpResponse(error, status=500)

    try:
        daemon_set = read_namespaced_daemon_set(cluster, daemon_set_name, namespace)
        if not daemon_set:
            return HttpResponse("DaemonSet not found", status=404)

        api_client = cluster.apps_v1.api_client
        serialized_daemon_set = api_client.sanitize_for_serialization(daemon_set)
        daemon_set_json = json.dumps(serialized_daemon_set, indent=4)

        context = {
            'daemon_set_json': daemon_set_json,
            'daemon_set_name': daemon_set_name,
            'namespace': namespace,
        }

        return render(request, 'kubeDaemonSets/daemon-set-details-json.html', context)

    except ApiException as e:
        if e.status == 404:
            return HttpResponse("DaemonSet not found", status=404)
        else:
            error_message = f"An error occurred: {e.reason or 'Unknown error'}"
            logger.error(f"API Exception in daemon_set_json_page: {error_message}")
            return HttpResponse(error_message, status=e.status if e.status else 500)
    except Exception as e:
        error_message = f"Unexpected Error: {str(e)}"
        logger.error(f"Unexpected Exception in daemon_set_json_page: {error_message}")
        return HttpResponse(error_message, status=500)