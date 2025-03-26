# views.py

import json
from collections import defaultdict
from datetime import datetime
import threading

from django.shortcuts import render
from django.http import StreamingHttpResponse, HttpResponse
from django.utils.encoding import escape_uri_path

from appConfig.kubeconfig import v1  # Ensure this imports your CoreV1Api instance correctly
from kubernetes.client import ApiException
from kubernetes import client, watch


def index_page(request):
    try:
        # Get all namespaces
        all_namespaces = v1.list_namespace().items

        # Get all pods across all namespaces
        all_pods = v1.list_pod_for_all_namespaces().items

        # Get events across all namespaces
        events = v1.list_event_for_all_namespaces(limit=1000).items

        # Summary statistics
        total_namespaces = len(all_namespaces)
        total_pods = len(all_pods)
        phase_counts = defaultdict(int)
        for pod in all_pods:
            phase_counts[pod.status.phase] += 1

        # Prepare pods data for Tabulator
        pods_data = []
        for pod in all_pods:
            creation_time = pod.metadata.creation_timestamp
            age = (datetime.utcnow() - creation_time.replace(tzinfo=None)).total_seconds() / 3600  # Age in hours
            age_str = f"{int(age)}h" if age < 24 else f"{int(age/24)}d"

            # Filter events related to this pod
            pod_events = [
                {
                    'type': event.type,
                    'reason': event.reason,
                    'message': event.message,
                    'first_seen': event.first_timestamp.strftime("%Y-%m-%d %H:%M:%S") if event.first_timestamp else '',
                    'last_seen': event.last_timestamp.strftime("%Y-%m-%d %H:%M:%S") if event.last_timestamp else '',
                }
                for event in events
                if event.involved_object.kind == 'Pod' and event.involved_object.name == pod.metadata.name
            ]

            pods_data.append({
                'name': pod.metadata.name,
                'namespace': pod.metadata.namespace,
                'status': pod.status.phase,
                'node': pod.spec.node_name or 'N/A',
                'age': age_str,
                'details_url': f"/pods/{pod.metadata.namespace}/{pod.metadata.name}/",
                'events': pod_events,  # Add structured events data
            })

        # Prepare events data for Tabulator
        events_data = []
        for event in events:
            involved_object = event.involved_object

            # Ensure all required fields are present
            namespace = event.metadata.namespace if event.metadata.namespace else 'default'  # Event's namespace
            event_name = event.metadata.name if event.metadata.name else 'unknown-event'
            object_name = involved_object.name if involved_object.name else 'unknown-object'
            kind = involved_object.kind if involved_object.kind else 'UnknownKind'

            # Construct details_url using the event's actual name
            if namespace != 'default' and event_name != 'unknown-event':
                details_url = f"/events/{namespace}/{event_name}/"
            else:
                details_url = "#"

            events_data.append({
                'event_name': event_name,  # Event's actual name
                'object_name': object_name,
                'namespace': namespace,
                'kind': kind,
                'type': event.type if event.type else '',
                'reason': event.reason if event.reason else '',
                'message': event.message if event.message else '',
                'count': event.count if event.count else 0,
                'source_component': event.source.component if event.source and event.source.component else '',
                'source_host': event.source.host if event.source and event.source.host else '',
                'first_seen': event.first_timestamp.strftime("%Y-%m-%d %H:%M:%S") if event.first_timestamp else '',
                'last_seen': event.last_timestamp.strftime("%Y-%m-%d %H:%M:%S") if event.last_timestamp else '',
                'details_url': details_url,  # Use event's actual name in URL
            })

        context = {
            'namespaces': all_namespaces,
            'total_namespaces': total_namespaces,
            'total_pods': total_pods,
            'phase_counts': phase_counts,
            'pods_data_json': json.dumps(pods_data),       # Serialize pods data for Tabulator
            'events_data_json': json.dumps(events_data),   # Serialize events data for Tabulator
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


def all_events_page(request):
    try:
        # Get all events across all namespaces with a higher limit if needed
        events = v1.list_event_for_all_namespaces(limit=1000).items

        # Prepare events data for Tabulator
        events_data = []
        for event in events:
            involved_object = event.involved_object

            # Ensure all required fields are present
            namespace = event.metadata.namespace if event.metadata.namespace else 'default'  # Event's namespace
            event_name = event.metadata.name if event.metadata.name else 'unknown-event'
            object_name = involved_object.name if involved_object.name else 'unknown-object'
            kind = involved_object.kind if involved_object.kind else 'UnknownKind'

            # Construct details_url using the event's actual name
            if namespace != 'default' and event_name != 'unknown-event':
                details_url = f"/events/{namespace}/{event_name}/"
            else:
                details_url = "#"

            events_data.append({
                'event_name': event_name,  # Event's actual name
                'object_name': object_name,
                'namespace': namespace,
                'kind': kind,
                'type': event.type if event.type else '',
                'reason': event.reason if event.reason else '',
                'message': event.message if event.message else '',
                'count': event.count if event.count else 0,
                'source_component': event.source.component if event.source and event.source.component else '',
                'source_host': event.source.host if event.source and event.source.host else '',
                'first_seen': event.first_timestamp.strftime("%Y-%m-%d %H:%M:%S") if event.first_timestamp else '',
                'last_seen': event.last_timestamp.strftime("%Y-%m-%d %H:%M:%S") if event.last_timestamp else '',
                'details_url': details_url,  # Use event's actual name in URL
            })

        context = {
            'events_data_json': json.dumps(events_data),  # Serialize events data for Tabulator
        }

        return render(request, 'all-events.html', context)
    except ApiException as e:
        error_message = f"API Error: {e.reason}"
        return render(request, 'all-events.html', {'error': error_message})
    except Exception as e:
        error_message = f"Unexpected Error: {str(e)}"
        return render(request, 'all-events.html', {'error': error_message})


def event_detail_page(request, namespace, event_name):
    try:
        # Retrieve the specific event based on event_name and namespace
        event = v1.read_namespaced_event(name=event_name, namespace=namespace)

        # Optionally, extract additional properties if needed
        additional_properties = {}  # Fill this with any extra processing if required

        context = {
            'event': event,
            'additional_properties': additional_properties
        }

        return render(request, 'event-detail.html', context)
    except ApiException as e:
        error_message = f"API Error: {e.reason}"
        return render(request, 'event-detail.html', {'error': error_message})
    except Exception as e:
        error_message = f"Unexpected Error: {str(e)}"
        return render(request, 'event-detail.html', {'error': error_message})


def pod_details_page(request, namespace, pod_name):
    # Get the specific pod from the provided namespace and pod name
    try:
        pod = v1.read_namespaced_pod(pod_name, namespace)
    except ApiException as e:
        if e.status == 404:
            return HttpResponse("Pod not found", status=404)
        else:
            return HttpResponse("An error occurred", status=e.status)

    # Extract container names
    containers = [container.name for container in pod.spec.containers]
    init_containers = [container.name for container in pod.spec.init_containers] if pod.spec.init_containers else []

    context = {
        'pod': pod,
        'selected_namespace': namespace,
        'pod_name': pod_name,
        'containers': containers,
        'init_containers': init_containers,
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


def stream_pod_logs(request, namespace, pod_name, container_name):
    """
    Stream pod logs using Server-Sent Events (SSE) with container support.
    """
    try:
        # Establish a connection to the pod log stream
        pod_logs = v1.read_namespaced_pod_log(
            name=pod_name,
            namespace=namespace,
            container=container_name,  # Specify the container name
            follow=True,
            _preload_content=False
        )

        def event_stream():
            try:
                for log_line in pod_logs:
                    decoded_log = log_line.decode('utf-8').rstrip()
                    # Format the log line as an SSE message
                    yield f"data: {json.dumps({'log': decoded_log})}\n\n"
            except GeneratorExit:
                # Handle client disconnect
                v1.api_client.close()
            except Exception as e:
                # Send error message to client
                yield f"data: {json.dumps({'log': f'Error streaming logs: {str(e)}'})}\n\n"

        # Return a StreamingHttpResponse with the appropriate SSE headers
        response = StreamingHttpResponse(event_stream(), content_type='text/event-stream')
        response['Cache-Control'] = 'no-cache'
        response['X-Accel-Buffering'] = 'no'  # Disable buffering for Nginx or other proxies
        return response

    except ApiException as e:
        return HttpResponse(f"API Error: {e.reason}", status=e.status)
    except Exception as e:
        return HttpResponse(f"Unexpected Error: {str(e)}", status=500)