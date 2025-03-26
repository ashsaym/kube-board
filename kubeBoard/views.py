# views.py

import json
from collections import defaultdict
from datetime import datetime

from django.http import StreamingHttpResponse, HttpResponse
from django.shortcuts import render
from django.utils.encoding import escape_uri_path
from kubernetes import client
from kubernetes.client import ApiException

from appConfig.kubeconfig import v1  # Ensure this imports your CoreV1Api instance correctly


def format_event(event):
    """Helper function to format an event for general usage."""
    namespace = event.metadata.namespace if event.metadata.namespace else 'default'
    event_name = event.metadata.name if event.metadata.name else 'unknown-event'
    object_name = event.involved_object.name if (event.involved_object and event.involved_object.name) else 'unknown-object'
    kind = event.involved_object.kind if (event.involved_object and event.involved_object.kind) else 'UnknownKind'
    details_url = f"/events/{namespace}/{event_name}/" if (namespace != 'default' and event_name != 'unknown-event') else "#"
    return {
        'event_name': event_name,
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
        'details_url': details_url,
    }


def format_pod_event(event):
    """Helper function to format an event related to a pod."""
    return {
        'type': event.type,
        'reason': event.reason,
        'message': event.message,
        'first_seen': event.first_timestamp.strftime("%Y-%m-%d %H:%M:%S") if event.first_timestamp else '',
        'last_seen': event.last_timestamp.strftime("%Y-%m-%d %H:%M:%S") if event.last_timestamp else '',
    }


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
                format_pod_event(event)
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
                'events': pod_events,
            })

        # Prepare events data for Tabulator
        events_data = [format_event(event) for event in events]

        context = {
            'namespaces': all_namespaces,
            'total_namespaces': total_namespaces,
            'total_pods': total_pods,
            'phase_counts': phase_counts,
            'pods_data_json': json.dumps(pods_data),
            'events_data_json': json.dumps(events_data),
        }

        return render(request, 'kubeBoard/index.html', context)
    except ApiException as e:
        error_message = f"API Error: {e.reason}"
        return render(request, 'kubeBoard/index.html', {'error': error_message})
    except Exception as e:
        error_message = f"Unexpected Error: {str(e)}"
        return render(request, 'kubeBoard/index.html', {'error': error_message})








