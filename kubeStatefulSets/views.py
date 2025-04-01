import json
from datetime import datetime, timezone

from django.http import HttpResponse
from django.shortcuts import render
from kubernetes.client import ApiException

# No direct functions for StatefulSets in kubeconfig.py, using the API directly
from appConfig.settings import logger
from appConfig.utils import get_cluster_client


def all_statefulsets_page(request):
    """
    Displays all StatefulSets across all namespaces in the selected Kubernetes cluster.
    """
    cluster, error = get_cluster_client(request)
    if error:
        return HttpResponse(error, status=500)

    try:
        # Get all namespaces
        all_namespaces = cluster.core_v1.list_namespace().items

        # Get all StatefulSets across all namespaces
        try:
            statefulsets = cluster.apps_v1.list_stateful_set_for_all_namespaces()
        except ApiException as e:
            logger.error(f"Failed to retrieve StatefulSets: {e}")
            statefulsets = None

        # Process statefulsets to add age and other useful information
        processed_statefulsets = []
        if statefulsets and statefulsets.items:
            for statefulset in statefulsets.items:
                creation_time = statefulset.metadata.creation_timestamp
                if creation_time:
                    age_timedelta = datetime.now(timezone.utc) - creation_time
                    age_hours = age_timedelta.total_seconds() / 3600
                    age_str = f"{int(age_hours)}h" if age_hours < 24 else f"{int(age_hours / 24)}d"
                else:
                    age_str = "N/A"

                # Calculate readiness
                ready_replicas = statefulset.status.ready_replicas or 0
                replicas = statefulset.status.replicas or 0
                readiness = f"{ready_replicas}/{replicas}"

                processed_statefulsets.append({
                    'name': statefulset.metadata.name,
                    'namespace': statefulset.metadata.namespace,
                    'replicas': replicas,
                    'ready': ready_replicas,
                    'readiness': readiness,
                    'age': age_str,
                    'details_url': f"/statefulsets/{statefulset.metadata.namespace}/{statefulset.metadata.name}/",
                })

        kubectl_command = {
            'get': "kubectl get statefulsets --all-namespaces",
            'yaml': "kubectl get statefulsets --all-namespaces -o yaml",
            'describe': "kubectl describe statefulsets --all-namespaces",
            'create': "kubectl create -f statefulset.yaml",
            'scale': "kubectl scale statefulset <statefulset-name> --replicas=<count> -n <namespace>",
            'edit': "kubectl edit statefulset <statefulset-name> -n <namespace>",
            'delete': "kubectl delete statefulset <statefulset-name> -n <namespace>",
        }

        context = {
            'namespaces': all_namespaces,
            'statefulsets': statefulsets.items if statefulsets else [],
            'processed_statefulsets': processed_statefulsets,
            'kubectl_command': kubectl_command,
        }

        return render(request, 'kubeStatefulSets/all-statefulsets.html', context)

    except ApiException as e:
        error_message = f"API Error: {e.reason or 'An unknown API error occurred.'}"
        logger.error(f"API Exception in all_statefulsets_page: {error_message}")
        return HttpResponse(error_message, status=e.status if e.status else 500)
    except Exception as e:
        error_message = f"Unexpected Error: {str(e)}"
        logger.error(f"Unexpected Exception in all_statefulsets_page: {error_message}")
        return HttpResponse(error_message, status=500)


def statefulset_details_page(request, namespace, statefulset_name):
    """
    Displays detailed information about a specific StatefulSet.
    """
    cluster, error = get_cluster_client(request)
    if error:
        return HttpResponse(error, status=500)

    try:
        statefulset = cluster.apps_v1.read_namespaced_stateful_set(statefulset_name, namespace)
        if not statefulset:
            return HttpResponse("StatefulSet not found", status=404)

        # Get pods managed by this statefulset
        selector = ""
        if statefulset.spec.selector and statefulset.spec.selector.match_labels:
            selector_parts = []
            for key, value in statefulset.spec.selector.match_labels.items():
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
                logger.error(f"Failed to list pods for statefulset '{statefulset_name}': {e}")

        # Get events related to this statefulset
        events = []
        try:
            event_list = cluster.core_v1.list_namespaced_event(
                namespace=namespace,
                field_selector=f"involvedObject.name={statefulset_name},involvedObject.kind=StatefulSet"
            )
            events = event_list.items
        except ApiException as e:
            logger.error(f"Failed to list events for statefulset '{statefulset_name}': {e}")

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

        # Get persistent volume claims associated with this statefulset
        pvcs = []
        try:
            pvc_list = cluster.core_v1.list_namespaced_persistent_volume_claim(namespace=namespace)
            for pvc in pvc_list.items:
                # Check if PVC is owned by this statefulset
                for owner_ref in pvc.metadata.owner_references or []:
                    if owner_ref.kind == "StatefulSet" and owner_ref.name == statefulset_name:
                        pvcs.append(pvc)
                        break
        except ApiException as e:
            logger.error(f"Failed to list PVCs for statefulset '{statefulset_name}': {e}")

        kubectl_commands = [
            {
                'command': f"kubectl get statefulset {statefulset_name} -n {namespace}",
                'explanation': "Lists details about the specified StatefulSet."
            },
            {
                'command': f"kubectl get statefulset {statefulset_name} -n {namespace} -o yaml",
                'explanation': "Outputs the StatefulSet's configuration in YAML format."
            },
            {
                'command': f"kubectl describe statefulset {statefulset_name} -n {namespace}",
                'explanation': "Provides detailed information about the StatefulSet."
            },
            {
                'command': f"kubectl scale statefulset {statefulset_name} --replicas=<count> -n {namespace}",
                'explanation': "Scales the StatefulSet to the specified number of replicas."
            },
            {
                'command': f"kubectl rollout status statefulset/{statefulset_name} -n {namespace}",
                'explanation': "Shows the status of the rollout for the StatefulSet."
            },
            {
                'command': f"kubectl rollout history statefulset/{statefulset_name} -n {namespace}",
                'explanation': "Shows the rollout history of the StatefulSet."
            },
            {
                'command': f"kubectl rollout undo statefulset/{statefulset_name} -n {namespace}",
                'explanation': "Rolls back to the previous revision of the StatefulSet."
            },
            {
                'command': f"kubectl edit statefulset {statefulset_name} -n {namespace}",
                'explanation': "Edits the StatefulSet's configuration."
            },
            {
                'command': f"kubectl delete statefulset {statefulset_name} -n {namespace}",
                'explanation': "Deletes the specified StatefulSet."
            },
        ]

        context = {
            'statefulset': statefulset,
            'pods': pods,
            'events': formatted_events,
            'pvcs': pvcs,
            'selected_namespace': namespace,
            'statefulset_name': statefulset_name,
            'kubectl_commands': kubectl_commands,
        }

        return render(request, 'kubeStatefulSets/statefulset-details.html', context)

    except ApiException as e:
        if e.status == 404:
            return HttpResponse("StatefulSet not found", status=404)
        else:
            error_message = f"An error occurred: {e.reason or 'Unknown error'}"
            logger.error(f"API Exception in statefulset_details_page: {error_message}")
            return HttpResponse(error_message, status=e.status if e.status else 500)
    except Exception as e:
        error_message = f"Unexpected Error: {str(e)}"
        logger.error(f"Unexpected Exception in statefulset_details_page: {error_message}")
        return HttpResponse(error_message, status=500)


def statefulset_json_page(request, namespace, statefulset_name):
    """
    Displays the JSON representation of a specific StatefulSet.
    """
    cluster, error = get_cluster_client(request)
    if error:
        return HttpResponse(error, status=500)

    try:
        statefulset = cluster.apps_v1.read_namespaced_stateful_set(statefulset_name, namespace)
        if not statefulset:
            return HttpResponse("StatefulSet not found", status=404)

        api_client = cluster.apps_v1.api_client
        serialized_statefulset = api_client.sanitize_for_serialization(statefulset)
        statefulset_json = json.dumps(serialized_statefulset, indent=4)

        context = {
            'statefulset_json': statefulset_json,
            'statefulset_name': statefulset_name,
            'namespace': namespace,
        }

        return render(request, 'kubeStatefulSets/statefulset-details-json.html', context)

    except ApiException as e:
        if e.status == 404:
            return HttpResponse("StatefulSet not found", status=404)
        else:
            error_message = f"An error occurred: {e.reason or 'Unknown error'}"
            logger.error(f"API Exception in statefulset_json_page: {error_message}")
            return HttpResponse(error_message, status=e.status if e.status else 500)
    except Exception as e:
        error_message = f"Unexpected Error: {str(e)}"
        logger.error(f"Unexpected Exception in statefulset_json_page: {error_message}")
        return HttpResponse(error_message, status=500)