# kubeEvents/views.py

import json
from django.shortcuts import render
from kubernetes.client import ApiException

from appConfig.settings import logger
from appConfig.utils import get_cluster_client  # Import the helper function
from kubeBoard.views import format_event  # Ensure format_event accepts kubeconfig_file

def all_events_page(request):
    """
    Displays all Kubernetes events across all namespaces for the selected cluster.
    """
    try:
        # Retrieve the selected cluster client
        cluster, error = get_cluster_client(request)
        if error:
            return render(request, 'kubeEvents/all-events.html', {'error': error})

        # Fetch all events with an increased limit if necessary
        events = cluster.core_v1.list_event_for_all_namespaces(limit=1000).items

        # Format events for Tabulator
        events_data = [format_event(event, cluster.kubeconfig_file) for event in events]
        kubectl_command = "kubectl get events --all-namespaces"

        context = {
            'events_data_json': json.dumps(events_data),
            'kubectl_command': kubectl_command
        }

        return render(request, 'kubeEvents/all-events.html', context)
    except ApiException as e:
        error_message = f"API Error: {e.reason}"
        logger.error(f"API Exception in all_events_page: {error_message}")
        return render(request, 'kubeEvents/all-events.html', {'error': error_message})
    except Exception as e:
        error_message = f"Unexpected Error: {str(e)}"
        logger.error(f"Exception in all_events_page: {error_message}")
        return render(request, 'kubeEvents/all-events.html', {'error': error_message})


def event_detail_page(request, namespace, event_name):
    """
    Displays detailed information about a specific Kubernetes event.
    """
    try:
        # Retrieve the selected cluster client
        cluster, error = get_cluster_client(request)
        if error:
            return render(request, 'kubeEvents/event-detail.html', {'error': error})

        # Fetch the specific event
        event = cluster.core_v1.read_namespaced_event(name=event_name, namespace=namespace)

        # Extract additional properties
        additional_properties = {
            'reason': event.reason,
            'message': event.message,
            'source': event.source.to_dict() if event.source else {},
            'first_timestamp': event.first_timestamp,
            'last_timestamp': event.last_timestamp,
            'count': event.count,
            'type': event.type,
            'namespace': event.metadata.namespace,
            'involved_object': event.involved_object.to_dict() if event.involved_object else {},
            'event_time': getattr(event, 'event_time', None),  # Handle possible None
            'reporting_instance': getattr(event, 'reporting_instance', None),
            'action': getattr(event, 'action', None),
            'related': event.related,
            'metadata': event.metadata.to_dict(),
        }

        kubectl_command = f"kubectl get event {event_name} -n {namespace} -o yaml"

        context = {
            'event': event,
            'additional_properties': additional_properties,
            'kubectl_command': kubectl_command
        }

        return render(request, 'kubeEvents/event-detail.html', context)
    except ApiException as e:
        error_message = f"API Error: {e.reason}"
        logger.error(f"API Exception in event_detail_page: {error_message}")
        return render(request, 'kubeEvents/event-detail.html', {'error': error_message})
    except Exception as e:
        error_message = f"Unexpected Error: {str(e)}"
        logger.error(f"Exception in event_detail_page: {error_message}")
        return render(request, 'kubeEvents/event-detail.html', {'error': error_message})