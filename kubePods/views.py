import json

from django.http import HttpResponse
from django.shortcuts import render
from django.utils.encoding import escape_uri_path
from kubernetes import client
from kubernetes.client import ApiException

from appConfig.kubeconfig import v1


# Create your views here.
def all_pods_page(request):
    # Get all namespaces
    all_namespaces = v1.list_namespace().items

    # Get all pods across all namespaces
    pods = v1.list_pod_for_all_namespaces().items
    kubectl_command = "kubectl get pods --all-namespaces"

    return render(request, 'kubePods/all-pods.html', {'namespaces': all_namespaces, 'pods': pods, 'kubectl_command': kubectl_command})

def pod_details_page(request, namespace, pod_name):
    try:
        pod = v1.read_namespaced_pod(pod_name, namespace)
    except ApiException as e:
        if e.status == 404:
            return HttpResponse("Pod not found", status=404)
        else:
            return HttpResponse("An error occurred", status=e.status)

    containers = [container.name for container in pod.spec.containers]
    init_containers = [container.name for container in pod.spec.init_containers] if pod.spec.init_containers else []
    kubectl_command = f"kubectl get pod {pod_name} -n {namespace} -o yaml"

    context = {
        'pod': pod,
        'selected_namespace': namespace,
        'pod_name': pod_name,
        'containers': containers,
        'init_containers': init_containers,
        'kubectl_command': kubectl_command,
    }

    return render(request, 'kubePods/pod-details.html', context=context)



def pod_json_page(request, namespace, pod_name):
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

    return render(request, 'kubePods/pod-details-json.html', context=context)


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
