import json

from django.http import HttpResponse
from django.shortcuts import render
from kubernetes.client import ApiException

from appConfig.kubeconfig import list_config_maps, list_config_maps_for_all_namespaces, read_namespaced_config_map
from appConfig.settings import logger
from appConfig.utils import get_cluster_client


def all_config_maps_page(request):
    """
    Displays all ConfigMaps across all namespaces in the selected Kubernetes cluster.
    """
    cluster, error = get_cluster_client(request)
    if error:
        return HttpResponse(error, status=500)

    try:
        # Get all namespaces
        all_namespaces = cluster.core_v1.list_namespace().items

        # Get all ConfigMaps across all namespaces
        config_maps = list_config_maps_for_all_namespaces(cluster)
        if not config_maps:
            config_maps = {"items": []}

        kubectl_command = {
            'get': "kubectl get configmaps --all-namespaces",
            'yaml': "kubectl get configmaps --all-namespaces -o yaml",
            'describe': "kubectl describe configmaps --all-namespaces",
            'create': "kubectl create configmap <configmap-name> --from-literal=key1=value1 --from-literal=key2=value2",
            'edit': "kubectl edit configmap <configmap-name> -n <namespace>",
            'delete': "kubectl delete configmap <configmap-name> -n <namespace>",
        }

        context = {
            'namespaces': all_namespaces,
            'config_maps': config_maps.items,
            'kubectl_command': kubectl_command,
        }

        return render(request, 'kubeConfigMaps/all-config-maps.html', context)

    except ApiException as e:
        error_message = f"API Error: {e.reason or 'An unknown API error occurred.'}"
        logger.error(f"API Exception in all_config_maps_page: {error_message}")
        return HttpResponse(error_message, status=e.status if e.status else 500)
    except Exception as e:
        error_message = f"Unexpected Error: {str(e)}"
        logger.error(f"Unexpected Exception in all_config_maps_page: {error_message}")
        return HttpResponse(error_message, status=500)


def config_map_details_page(request, namespace, config_map_name):
    """
    Displays detailed information about a specific ConfigMap.
    """
    cluster, error = get_cluster_client(request)
    if error:
        return HttpResponse(error, status=500)

    try:
        config_map = read_namespaced_config_map(cluster, config_map_name, namespace)
        if not config_map:
            return HttpResponse("ConfigMap not found", status=404)

        kubectl_commands = [
            {
                'command': f"kubectl get configmap {config_map_name} -n {namespace}",
                'explanation': "Lists details about the specified ConfigMap."
            },
            {
                'command': f"kubectl get configmap {config_map_name} -n {namespace} -o yaml",
                'explanation': "Outputs the ConfigMap's configuration in YAML format."
            },
            {
                'command': f"kubectl describe configmap {config_map_name} -n {namespace}",
                'explanation': "Provides detailed information about the ConfigMap."
            },
            {
                'command': f"kubectl edit configmap {config_map_name} -n {namespace}",
                'explanation': "Edits the ConfigMap's configuration."
            },
            {
                'command': f"kubectl delete configmap {config_map_name} -n {namespace}",
                'explanation': "Deletes the specified ConfigMap."
            },
        ]

        context = {
            'config_map': config_map,
            'selected_namespace': namespace,
            'config_map_name': config_map_name,
            'kubectl_commands': kubectl_commands,
        }

        return render(request, 'kubeConfigMaps/config-map-details.html', context)

    except ApiException as e:
        if e.status == 404:
            return HttpResponse("ConfigMap not found", status=404)
        else:
            error_message = f"An error occurred: {e.reason or 'Unknown error'}"
            logger.error(f"API Exception in config_map_details_page: {error_message}")
            return HttpResponse(error_message, status=e.status if e.status else 500)
    except Exception as e:
        error_message = f"Unexpected Error: {str(e)}"
        logger.error(f"Unexpected Exception in config_map_details_page: {error_message}")
        return HttpResponse(error_message, status=500)


def config_map_json_page(request, namespace, config_map_name):
    """
    Displays the JSON representation of a specific ConfigMap.
    """
    cluster, error = get_cluster_client(request)
    if error:
        return HttpResponse(error, status=500)

    try:
        config_map = read_namespaced_config_map(cluster, config_map_name, namespace)
        if not config_map:
            return HttpResponse("ConfigMap not found", status=404)

        api_client = cluster.core_v1.api_client
        serialized_config_map = api_client.sanitize_for_serialization(config_map)
        config_map_json = json.dumps(serialized_config_map, indent=4)

        context = {
            'config_map_json': config_map_json,
            'config_map_name': config_map_name,
            'namespace': namespace,
        }

        return render(request, 'kubeConfigMaps/config-map-details-json.html', context)

    except ApiException as e:
        if e.status == 404:
            return HttpResponse("ConfigMap not found", status=404)
        else:
            error_message = f"An error occurred: {e.reason or 'Unknown error'}"
            logger.error(f"API Exception in config_map_json_page: {error_message}")
            return HttpResponse(error_message, status=e.status if e.status else 500)
    except Exception as e:
        error_message = f"Unexpected Error: {str(e)}"
        logger.error(f"Unexpected Exception in config_map_json_page: {error_message}")
        return HttpResponse(error_message, status=500)