import json

from django.shortcuts import render
from kubernetes.client import ApiException

from appConfig.kubeconfig import v1
from kubeBoard.views import format_event


# Create your views here.
def all_events_page(request):
    try:
        # Get all events across all namespaces with a higher limit if needed
        events = v1.list_event_for_all_namespaces(limit=1000).items

        # Prepare events data for Tabulator
        events_data = [format_event(event) for event in events]

        context = {
            'events_data_json': json.dumps(events_data),
        }

        return render(request, 'kubeEvents/all-events.html', context)
    except ApiException as e:
        error_message = f"API Error: {e.reason}"
        return render(request, 'kubeEvents/all-events.html', {'error': error_message})
    except Exception as e:
        error_message = f"Unexpected Error: {str(e)}"
        return render(request, 'kubeEvents/all-events.html', {'error': error_message})


def event_detail_page(request, namespace, event_name):
    try:
        # Retrieve the specific event based on event_name and namespace
        event = v1.read_namespaced_event(name=event_name, namespace=namespace)

        additional_properties = {}  # Optionally, extract additional properties if needed

        context = {
            'event': event,
            'additional_properties': additional_properties
        }

        return render(request, 'kubeEvents/event-detail.html', context)
    except ApiException as e:
        error_message = f"API Error: {e.reason}"
        return render(request, 'kubeEvents/event-detail.html', {'error': error_message})
    except Exception as e:
        error_message = f"Unexpected Error: {str(e)}"
        return render(request, 'kubeEvents/event-detail.html', {'error': error_message})

