# appName/views.py

import json
from django.http import HttpResponse
from django.shortcuts import render
from django.utils.encoding import escape_uri_path
from kubernetes.client import ApiException
from django.views.decorators.http import require_POST

from appConfig.utils import get_cluster_client  # Import the helper function

import logging
from collections import defaultdict
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# --- Existing Helper Functions (No Change Needed) ---
def parse_cpu(cpu_str):
    try:
        if cpu_str.endswith('n'):
            return float(cpu_str[:-1]) / 1e6
        elif cpu_str.endswith('u'):
            return float(cpu_str[:-1]) / 1e3
        elif cpu_str.endswith('m'):
            return float(cpu_str[:-1])
        else:
            return float(cpu_str) * 1000
    except ValueError as e:
        logger.error(f"Error parsing CPU string '{cpu_str}': {e}")
        return 0.0

def parse_ram(ram_str):
    try:
        if ram_str.endswith('Ki'):
            return float(ram_str[:-2]) / 1024
        elif ram_str.endswith('Mi'):
            return float(ram_str[:-2])
        elif ram_str.endswith('Gi'):
            return float(ram_str[:-2]) * 1024
        elif ram_str.endswith('Ti'):
            return float(ram_str[:-2]) * 1024 * 1024
        elif ram_str.endswith('n'):
            return 0.0
        else:
            logger.warning(f"Unknown RAM unit in '{ram_str}'")
            return 0.0
    except ValueError as e:
        logger.error(f"Error parsing RAM string '{ram_str}': {e}")
        return 0.0

def format_event(event, kubeconfig_file):
    namespace = event.metadata.namespace or 'default'
    event_name = event.metadata.name or 'unknown-event'
    object_name = (event.involved_object.name or 'unknown-object') if event.involved_object else 'unknown-object'
    kind = (event.involved_object.kind or 'UnknownKind') if event.involved_object else 'UnknownKind'
    details_url = f"/events/{namespace}/{event_name}/" if (namespace != 'default' and event_name != 'unknown-event') else "#"
    first_seen = event.first_timestamp.replace(tzinfo=timezone.utc).astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S") if event.first_timestamp else ''
    last_seen = event.last_timestamp.replace(tzinfo=timezone.utc).astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S") if event.last_timestamp else ''
    return {
        'event_name': event_name,
        'object_name': object_name,
        'namespace': namespace,
        'kind': kind,
        'type': event.type or '',
        'reason': event.reason or '',
        'message': event.message or '',
        'count': event.count or 0,
        'source_component': event.source.component or '',
        'source_host': event.source.host or '',
        'first_seen': first_seen,
        'last_seen': last_seen,
        'details_url': details_url,
    }

def format_pod_event(event):
    first_seen = event.first_timestamp.replace(tzinfo=timezone.utc).astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S") if event.first_timestamp else ''
    last_seen = event.last_timestamp.replace(tzinfo=timezone.utc).astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S") if event.last_timestamp else ''
    return {
        'type': event.type,
        'reason': event.reason,
        'message': event.message,
        'first_seen': first_seen,
        'last_seen': last_seen,
    }

# --- Updated View Functions ---
def all_pods_page(request):
    """
    Displays all pods across all namespaces in the selected Kubernetes cluster.
    Calculates how many containers are running in each pod and determines the maximum container count.
    """
    cluster, error = get_cluster_client(request)
    if error:
        return HttpResponse(error, status=500)

    try:
        # Get all namespaces
        all_namespaces = cluster.core_v1.list_namespace().items

        # Get all pods across all namespaces
        pods = cluster.core_v1.list_pod_for_all_namespaces().items

        max_container_count = 0
        for pod in pods:
            # Total containers for the pod
            container_count = len(pod.spec.containers) if pod.spec.containers else 0
            setattr(pod, "container_count", container_count)
            if container_count > max_container_count:
                max_container_count = container_count

            # Count running containers based on container statuses
            running_container_count = 0
            if pod.status.container_statuses:
                for status in pod.status.container_statuses:
                    if status.ready:
                        running_container_count += 1
            setattr(pod, "running_container_count", running_container_count)

        kubectl_command = {
            'get': "kubectl get pods --all-namespaces",
            'yaml': "kubectl get pods --all-namespaces -o yaml",
            'describe': "kubectl describe pods --all-namespaces",
            'logs': "kubectl logs <pod-name> -n <namespace>",
            'exec': "kubectl exec -it <pod-name> -n <namespace> -- /bin/bash",
            'port_forward': "kubectl port-forward <pod-name> 8080:80 -n <namespace>",
            'delete': "kubectl delete pod <pod-name> -n <namespace>",
            'edit': "kubectl edit pod <pod-name> -n <namespace>",
            'events': "kubectl get events --all-namespaces",
            'metrics': "kubectl top pods --all-namespaces",
        }

        context = {
            'namespaces': all_namespaces,
            'pods': pods,
            'kubectl_command': kubectl_command,
            'max_container_count': max_container_count,
        }

        return render(request, 'kubePods/all-pods.html', context)

    except ApiException as e:
        error_message = f"API Error: {e.reason or 'An unknown API error occurred.'}"
        logger.error(f"API Exception in all_pods_page: {error_message}")
        return HttpResponse(error_message, status=e.status if e.status else 500)
    except Exception as e:
        error_message = f"Unexpected Error: {str(e)}"
        logger.error(f"Unexpected Exception in all_pods_page: {error_message}")
        return HttpResponse(error_message, status=500)


def pod_details_page(request, namespace, pod_name):
    """
    Displays detailed information about a specific pod.
    """
    cluster, error = get_cluster_client(request)
    if error:
        return HttpResponse(error, status=500)

    try:
        pod = cluster.core_v1.read_namespaced_pod(pod_name, namespace)
    except ApiException as e:
        if e.status == 404:
            return HttpResponse("Pod not found", status=404)
        else:
            error_message = f"An error occurred: {e.reason or 'Unknown error'}"
            logger.error(f"API Exception in pod_details_page: {error_message}")
            return HttpResponse(error_message, status=e.status if e.status else 500)
    except Exception as e:
        error_message = f"Unexpected Error: {str(e)}"
        logger.error(f"Unexpected Exception in pod_details_page: {error_message}")
        return HttpResponse(error_message, status=500)

    containers = [container.name for container in pod.spec.containers]
    init_containers = [container.name for container in pod.spec.init_containers] if pod.spec.init_containers else []

    kubectl_command = {
        'get': f"kubectl get pod {pod_name} -n {namespace}",
        'yaml': f"kubectl get pod {pod_name} -n {namespace} -o yaml",
        'logs': f"kubectl logs {pod_name} -n {namespace}",
        'describe': f"kubectl describe pod {pod_name} -n {namespace}",
        'exec': f"kubectl exec -it {pod_name} -n {namespace} -- /bin/bash",
        'delete': f"kubectl delete pod {pod_name} -n {namespace}",
        'edit': f"kubectl edit pod {pod_name} -n {namespace}",
        'events': f"kubectl get events -n {namespace} --field-selector=involvedObject.name={pod_name}",
        'metrics': f"kubectl top pod {pod_name} -n {namespace}",
    }

    # Explanations for each kubectl command
    kubectl_explanations = {
        'get': "Lists details about the specified pod.",
        'yaml': "Outputs the pod's configuration in YAML format.",
        'logs': "Retrieves the logs produced by the pod.",
        'describe': "Provides detailed information about the pod's state and events.",
        'exec': "Opens an interactive shell session inside the pod.",
        'delete': "Deletes the specified pod.",
        'edit': "Edits the pod's configuration.",
        'events': "Lists events related to the pod.",
        'metrics': "Displays resource (CPU/memory) usage metrics for the pod.",
    }

    # Generate port_forward commands dynamically
    port_forward_commands = []
    used_local_ports = set()

    # Function to assign a unique local port
    def assign_unique_local_port(desired_port):
        local_port = desired_port
        while local_port in used_local_ports:
            local_port += 1  # Increment to find an available port
        used_local_ports.add(local_port)
        return local_port

    # Iterate over containers and their ports
    for container in pod.spec.containers:
        for port in container.ports:
            pod_port = port.container_port
            local_port = assign_unique_local_port(pod_port)
            cmd = f"kubectl port-forward {pod_name} {local_port}:{pod_port} -n {namespace}"
            explanation = f"Forwards port <strong>{pod_port}</strong> on the pod to port <strong>{local_port}</strong> on your local machine."
            port_forward_commands.append({
                'command': cmd,
                'explanation': explanation,
            })

    # Similarly, handle init containers
    if pod.spec.init_containers:
        for init_container in pod.spec.init_containers:
            for port in init_container.ports:
                pod_port = port.container_port
                local_port = assign_unique_local_port(pod_port)
                cmd = f"kubectl port-forward {pod_name} {local_port}:{pod_port} -n {namespace}"
                explanation = f"Forwards port <strong>{pod_port}</strong> on the pod to port <strong>{local_port}</strong> on your local machine."
                port_forward_commands.append({
                    'command': cmd,
                    'explanation': explanation,
                })

    # Combine kubectl_command entries with explanations into a 'kubectl_commands' list
    kubectl_commands = []
    for cmd_name, cmd in kubectl_command.items():
        if cmd_name != 'port_forward':
            explanation = kubectl_explanations.get(cmd_name, "")
            kubectl_commands.append({
                'command': cmd,
                'explanation': explanation,
            })
    # Add port_forward_commands to kubectl_commands list
    kubectl_commands.extend(port_forward_commands)

    context = {
        'pod': pod,
        'selected_namespace': namespace,
        'pod_name': pod_name,
        'containers': containers,
        'init_containers': init_containers,
        'kubectl_commands': kubectl_commands,  # New list with all commands
    }

    return render(request, 'kubePods/pod-details.html', context)


def pod_json_page(request, namespace, pod_name):
    """
    Displays the JSON representation of a specific pod. Optionally allows downloading the JSON.
    """
    cluster, error = get_cluster_client(request)
    if error:
        return HttpResponse(error, status=500)

    try:
        pod = cluster.core_v1.read_namespaced_pod(pod_name, namespace)
        api_client = cluster.core_v1.api_client
        serialized_pod = api_client.sanitize_for_serialization(pod)
        pod_json = json.dumps(serialized_pod, indent=4)
    except ApiException as e:
        if e.status == 404:
            return HttpResponse("Pod not found", status=404)
        else:
            error_message = f"An error occurred: {e.reason or 'Unknown error'}"
            logger.error(f"API Exception in pod_json_page: {error_message}")
            return HttpResponse(error_message, status=e.status if e.status else 500)
    except TypeError as e:
        error_message = f"Error serializing JSON: {str(e)}"
        logger.error(f"TypeError in pod_json_page: {error_message}")
        return HttpResponse(error_message, status=500)
    except Exception as e:
        error_message = f"An unexpected error occurred: {str(e)}"
        logger.error(f"Unexpected Exception in pod_json_page: {error_message}")
        return HttpResponse(error_message, status=500)

    if request.GET.get('download') == 'true':
        response = HttpResponse(pod_json, content_type='application/json')
        filename = f"{pod_name}.json"
        response['Content-Disposition'] = f'attachment; filename="{escape_uri_path(filename)}"'
        return response

    context = {
        'pod_json': pod_json,
        'pod_name': pod.metadata.name,
        'namespace': namespace,
    }

    return render(request, 'kubePods/pod-details-json.html', context)


def download_pod_json(request, namespace, pod_name):
    """
    Provides a downloadable JSON file of a specific pod.
    """
    # This view is now redundant since `pod_json_page` handles downloading via a GET parameter.
    # However, if you prefer to keep it separate, here's the updated version:

    cluster, error = get_cluster_client(request)
    if error:
        return HttpResponse(error, status=500)

    try:
        pod = cluster.core_v1.read_namespaced_pod(pod_name, namespace)
        api_client = cluster.core_v1.api_client
        serialized_pod = api_client.sanitize_for_serialization(pod)
        pod_json = json.dumps(serialized_pod, indent=4)
    except ApiException as e:
        if e.status == 404:
            return HttpResponse("Pod not found", status=404)
        else:
            error_message = f"An error occurred: {e.reason or 'Unknown error'}"
            logger.error(f"API Exception in download_pod_json: {error_message}")
            return HttpResponse(error_message, status=e.status if e.status else 500)
    except TypeError as e:
        error_message = f"Error serializing JSON: {str(e)}"
        logger.error(f"TypeError in download_pod_json: {error_message}")
        return HttpResponse(error_message, status=500)
    except Exception as e:
        error_message = f"An unexpected error occurred: {str(e)}"
        logger.error(f"Unexpected Exception in download_pod_json: {error_message}")
        return HttpResponse(error_message, status=500)

    response = HttpResponse(pod_json, content_type='application/json')
    filename = f"{pod_name}.json"
    response['Content-Disposition'] = f'attachment; filename="{escape_uri_path(filename)}"'
    return response