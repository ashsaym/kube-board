import json
from datetime import datetime, timezone

from django.http import HttpResponse
from django.shortcuts import render
from kubernetes.client import ApiException

from appConfig.kubeconfig import list_deployments, list_deployments_for_all_namespaces
from appConfig.settings import logger
from appConfig.utils import get_cluster_client


def all_deployments_page(request):
    """
    Displays all Deployments across all namespaces in the selected Kubernetes cluster.
    """
    cluster, error = get_cluster_client(request)
    if error:
        return HttpResponse(error, status=500)

    try:
        # Get all namespaces
        all_namespaces = cluster.core_v1.list_namespace().items

        # Get all Deployments across all namespaces
        deployments = list_deployments_for_all_namespaces(cluster)
        if not deployments:
            deployments = {"items": []}

        # Process deployments to add age and other useful information
        processed_deployments = []
        for deployment in deployments.items:
            creation_time = deployment.metadata.creation_timestamp
            if creation_time:
                age_timedelta = datetime.now(timezone.utc) - creation_time
                age_hours = age_timedelta.total_seconds() / 3600
                age_str = f"{int(age_hours)}h" if age_hours < 24 else f"{int(age_hours / 24)}d"
            else:
                age_str = "N/A"

            # Calculate readiness
            ready_replicas = deployment.status.ready_replicas or 0
            replicas = deployment.status.replicas or 0
            readiness = f"{ready_replicas}/{replicas}"

            processed_deployments.append({
                'name': deployment.metadata.name,
                'namespace': deployment.metadata.namespace,
                'replicas': replicas,
                'ready': ready_replicas,
                'readiness': readiness,
                'age': age_str,
                'strategy': deployment.spec.strategy.type if deployment.spec.strategy else "N/A",
                'details_url': f"/deployments/{deployment.metadata.namespace}/{deployment.metadata.name}/",
            })

        kubectl_command = {
            'get': "kubectl get deployments --all-namespaces",
            'yaml': "kubectl get deployments --all-namespaces -o yaml",
            'describe': "kubectl describe deployments --all-namespaces",
            'create': "kubectl create deployment <deployment-name> --image=<image-name>",
            'scale': "kubectl scale deployment <deployment-name> --replicas=<count> -n <namespace>",
            'edit': "kubectl edit deployment <deployment-name> -n <namespace>",
            'delete': "kubectl delete deployment <deployment-name> -n <namespace>",
            'rollout': "kubectl rollout status deployment/<deployment-name> -n <namespace>",
        }

        context = {
            'namespaces': all_namespaces,
            'deployments': deployments.items,
            'processed_deployments': processed_deployments,
            'kubectl_command': kubectl_command,
        }

        return render(request, 'kubeDeployments/all-deployments.html', context)

    except ApiException as e:
        error_message = f"API Error: {e.reason or 'An unknown API error occurred.'}"
        logger.error(f"API Exception in all_deployments_page: {error_message}")
        return HttpResponse(error_message, status=e.status if e.status else 500)
    except Exception as e:
        error_message = f"Unexpected Error: {str(e)}"
        logger.error(f"Unexpected Exception in all_deployments_page: {error_message}")
        return HttpResponse(error_message, status=500)


def deployment_details_page(request, namespace, deployment_name):
    """
    Displays detailed information about a specific Deployment.
    """
    cluster, error = get_cluster_client(request)
    if error:
        return HttpResponse(error, status=500)

    try:
        deployment = cluster.apps_v1.read_namespaced_deployment(deployment_name, namespace)
        if not deployment:
            return HttpResponse("Deployment not found", status=404)

        # Get pods managed by this deployment
        selector = ""
        if deployment.spec.selector and deployment.spec.selector.match_labels:
            selector_parts = []
            for key, value in deployment.spec.selector.match_labels.items():
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
                logger.error(f"Failed to list pods for deployment '{deployment_name}': {e}")

        # Get events related to this deployment
        events = []
        try:
            event_list = cluster.core_v1.list_namespaced_event(
                namespace=namespace,
                field_selector=f"involvedObject.name={deployment_name},involvedObject.kind=Deployment"
            )
            events = event_list.items
        except ApiException as e:
            logger.error(f"Failed to list events for deployment '{deployment_name}': {e}")

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
                'command': f"kubectl get deployment {deployment_name} -n {namespace}",
                'explanation': "Lists details about the specified Deployment."
            },
            {
                'command': f"kubectl get deployment {deployment_name} -n {namespace} -o yaml",
                'explanation': "Outputs the Deployment's configuration in YAML format."
            },
            {
                'command': f"kubectl describe deployment {deployment_name} -n {namespace}",
                'explanation': "Provides detailed information about the Deployment."
            },
            {
                'command': f"kubectl scale deployment {deployment_name} --replicas=<count> -n {namespace}",
                'explanation': "Scales the Deployment to the specified number of replicas."
            },
            {
                'command': f"kubectl rollout status deployment/{deployment_name} -n {namespace}",
                'explanation': "Shows the status of the rollout for the Deployment."
            },
            {
                'command': f"kubectl rollout history deployment/{deployment_name} -n {namespace}",
                'explanation': "Shows the rollout history of the Deployment."
            },
            {
                'command': f"kubectl rollout undo deployment/{deployment_name} -n {namespace}",
                'explanation': "Rolls back to the previous revision of the Deployment."
            },
            {
                'command': f"kubectl edit deployment {deployment_name} -n {namespace}",
                'explanation': "Edits the Deployment's configuration."
            },
            {
                'command': f"kubectl delete deployment {deployment_name} -n {namespace}",
                'explanation': "Deletes the specified Deployment."
            },
        ]

        context = {
            'deployment': deployment,
            'pods': pods,
            'events': formatted_events,
            'selected_namespace': namespace,
            'deployment_name': deployment_name,
            'kubectl_commands': kubectl_commands,
        }

        return render(request, 'kubeDeployments/deployment-details.html', context)

    except ApiException as e:
        if e.status == 404:
            return HttpResponse("Deployment not found", status=404)
        else:
            error_message = f"An error occurred: {e.reason or 'Unknown error'}"
            logger.error(f"API Exception in deployment_details_page: {error_message}")
            return HttpResponse(error_message, status=e.status if e.status else 500)
    except Exception as e:
        error_message = f"Unexpected Error: {str(e)}"
        logger.error(f"Unexpected Exception in deployment_details_page: {error_message}")
        return HttpResponse(error_message, status=500)


def deployment_json_page(request, namespace, deployment_name):
    """
    Displays the JSON representation of a specific Deployment.
    """
    cluster, error = get_cluster_client(request)
    if error:
        return HttpResponse(error, status=500)

    try:
        deployment = cluster.apps_v1.read_namespaced_deployment(deployment_name, namespace)
        if not deployment:
            return HttpResponse("Deployment not found", status=404)

        api_client = cluster.apps_v1.api_client
        serialized_deployment = api_client.sanitize_for_serialization(deployment)
        deployment_json = json.dumps(serialized_deployment, indent=4)

        context = {
            'deployment_json': deployment_json,
            'deployment_name': deployment_name,
            'namespace': namespace,
        }

        return render(request, 'kubeDeployments/deployment-details-json.html', context)

    except ApiException as e:
        if e.status == 404:
            return HttpResponse("Deployment not found", status=404)
        else:
            error_message = f"An error occurred: {e.reason or 'Unknown error'}"
            logger.error(f"API Exception in deployment_json_page: {error_message}")
            return HttpResponse(error_message, status=e.status if e.status else 500)
    except Exception as e:
        error_message = f"Unexpected Error: {str(e)}"
        logger.error(f"Unexpected Exception in deployment_json_page: {error_message}")
        return HttpResponse(error_message, status=500)