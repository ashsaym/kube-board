# views.py
import json
from collections import defaultdict

from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.utils.encoding import escape_uri_path

from appConfig.kubeconfig import v1  # Ensure this imports your CoreV1Api instance correctly
from kubernetes.client import ApiException
from kubernetes import client

def index_page(request):
    try:
        # Handle GET parameters for filtering and searching
        selected_namespace = request.GET.get('namespace', '')
        search_query = request.GET.get('search', '').lower()

        # Get all namespaces
        all_namespaces = v1.list_namespace().items

        # Get all pods across all namespaces once
        all_pods = v1.list_pod_for_all_namespaces().items

        # Apply namespace filtering
        if selected_namespace:
            pods = [pod for pod in all_pods if pod.metadata.namespace == selected_namespace]
        else:
            pods = all_pods

        # Apply search filtering
        if search_query:
            pods = [
                pod for pod in pods
                if search_query in pod.metadata.name.lower() or
                   search_query in pod.metadata.namespace.lower() or
                   search_query in pod.status.phase.lower() or
                   (pod.spec.node_name and search_query in pod.spec.node_name.lower())
            ]

        # Get recent events (e.g., last 100)
        events = v1.list_event_for_all_namespaces(limit=100).items

        # Summary statistics
        total_namespaces = len(all_namespaces)
        total_pods = len(all_pods)
        running_pods = sum(1 for pod in all_pods if pod.status.phase == "Running")
        pending_pods = sum(1 for pod in all_pods if pod.status.phase == "Pending")
        failed_pods = sum(1 for pod in all_pods if pod.status.phase == "Failed")
        succeeded_pods = sum(1 for pod in all_pods if pod.status.phase == "Succeeded")

        # Pod status distribution for HTML table
        status_counts = defaultdict(int)
        for pod in all_pods:
            status = pod.status.phase
            status_counts[status] += 1

        # Convert to list of dictionaries for easy templating

        context = {
            'namespaces': all_namespaces,
            'pods': pods,
            'events': events,
            'total_namespaces': total_namespaces,
            'total_pods': total_pods,
            'running_pods': running_pods,
            'pending_pods': pending_pods,
            'failed_pods': failed_pods,
            'succeeded_pods': succeeded_pods,
            'selected_namespace': selected_namespace,
            'search_query': search_query,
        }

        return render(request, 'index.html', context)
    except ApiException as e:
        error_message = f"API Error: {e.reason}"
        return render(request, 'index.html', {'error': error_message})
    except Exception as e:
        error_message = f"Unexpected Error: {str(e)}"
        return render(request, 'index.html', {'error': error_message})
def all_pods_page(request):
    # Get all namespaces
    all_namespaces = v1.list_namespace().items

    # Get all pods across all namespaces
    pods = v1.list_pod_for_all_namespaces().items

    return render(request, 'all-pods.html', {'namespaces': all_namespaces, 'pods': pods})

def pod_details_page(request, namespace, pod_name):
    # Get the specific pod from the provided namespace and pod name
    try:
        pod = v1.read_namespaced_pod(pod_name, namespace)
    except ApiException as e:
        if e.status == 404:
            return HttpResponse("Pod not found", status=404)
        else:
            return HttpResponse("An error occurred", status=e.status)

    context = {
        'pod': pod,
        'selected_namespace': namespace,
        'pod_name': pod_name
    }

    return render(request, 'pod-details.html', context=context)

def pod_json_page(request, namespace, pod_name):
    """
    Render a new page displaying the JSON representation of a specific pod.
    If 'download=true' is present in query parameters, return the JSON as a downloadable file.
    """
    try:
        pod = v1.read_namespaced_pod(pod_name, namespace)
        api_client = client.ApiClient()
        serialized_pod = api_client.sanitize_for_serialization(pod)
        pod_json = json.dumps(serialized_pod, indent=4)
    except ApiException as e:
        if e.status == 404:
            return HttpResponse("Pod not found", status=404)
        else:
            return HttpResponse(f"An error occurred: {e.reason}", status=e.status)
    except TypeError as e:
        return HttpResponse(f"Error serializing JSON: {str(e)}", status=500)
    except Exception as e:
        return HttpResponse(f"An unexpected error occurred: {str(e)}", status=500)

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

    return render(request, 'pod-details-json.html', context=context)

def download_pod_json(request, namespace, pod_name):
    try:
        pod = v1.read_namespaced_pod(pod_name, namespace)
        api_client = client.ApiClient()
        serialized_pod = api_client.sanitize_for_serialization(pod)
        pod_json = json.dumps(serialized_pod, indent=4)
    except ApiException as e:
        if e.status == 404:
            return HttpResponse("Pod not found", status=404)
        else:
            return HttpResponse(f"An error occurred: {e.reason}", status=e.status)
    except TypeError as e:
        return HttpResponse(f"Error serializing JSON: {str(e)}", status=500)
    except Exception as e:
        return HttpResponse(f"An unexpected error occurred: {str(e)}", status=500)

    response = HttpResponse(pod_json, content_type='application/json')
    filename = f"{pod_name}.json"
    response['Content-Disposition'] = f'attachment; filename="{escape_uri_path(filename)}"'
    return response