# views.py

import json
from collections import defaultdict
from datetime import datetime, timezone

from django.shortcuts import render
from kubernetes.client.exceptions import ApiException

from appConfig.kubeconfig import cluster_clients, cluster_clients_lock, loading_done, ClusterClient

import logging
logger = logging.getLogger(__name__)


def format_event(event, cluster_name):
    """Formats an event for general usage."""
    namespace = event.metadata.namespace or 'default'
    event_name = event.metadata.name or 'unknown-event'
    object_name = (event.involved_object.name or 'unknown-object') if event.involved_object else 'unknown-object'
    kind = (event.involved_object.kind or 'UnknownKind') if event.involved_object else 'UnknownKind'
    details_url = f"/events/{namespace}/{event_name}/" if (namespace != 'default' and event_name != 'unknown-event') else "#"
    first_seen = event.first_timestamp.replace(tzinfo=timezone.utc).astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S") if event.first_timestamp else ''
    last_seen = event.last_timestamp.replace(tzinfo=timezone.utc).astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S") if event.last_timestamp else ''
    return {
        'cluster': cluster_name,
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
    """Formats an event related to a pod."""
    first_seen = event.first_timestamp.replace(tzinfo=timezone.utc).astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S") if event.first_timestamp else ''
    last_seen = event.last_timestamp.replace(tzinfo=timezone.utc).astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S") if event.last_timestamp else ''
    return {
        'type': event.type,
        'reason': event.reason,
        'message': event.message,
        'first_seen': first_seen,
        'last_seen': last_seen,
    }


def index_page(request):
    """
    Renders the main dashboard page with aggregated data from all Kubernetes clusters.
    """
    try:
        # Wait for kubeconfig loading to complete, with a timeout of 10 seconds
        loading_complete = loading_done.wait(timeout=10)

        with cluster_clients_lock:
            if not cluster_clients:
                if not loading_complete:
                    error_message = "Kubeconfig loading is still in progress. Please try again shortly."
                else:
                    error_message = "No Kubernetes clusters could be loaded. Please check your kubeconfig files."
                logger.error(error_message)
                return render(request, 'kubeBoard/index.html', {'error': error_message})

            all_overviews = []
            all_pods_data = []
            all_events_data = []

            for cluster in cluster_clients:
                # Retrieve namespaces
                try:
                    all_namespaces = cluster.core_v1.list_namespace().items
                except ApiException as e:
                    logger.error(f"Failed to retrieve namespaces for cluster '{cluster.name}': {e}")
                    all_namespaces = []

                # Retrieve pods
                try:
                    all_pods = cluster.core_v1.list_pod_for_all_namespaces().items
                except ApiException as e:
                    logger.error(f"Failed to retrieve pods for cluster '{cluster.name}': {e}")
                    all_pods = []

                # Retrieve events
                try:
                    events = cluster.core_v1.list_event_for_all_namespaces(limit=1000).items
                except ApiException as e:
                    logger.error(f"Failed to retrieve events for cluster '{cluster.name}': {e}")
                    events = []

                # Compute summary statistics
                total_namespaces = len(all_namespaces)
                total_pods = len(all_pods)
                phase_counts = defaultdict(int)
                for pod in all_pods:
                    phase = pod.status.phase or "Unknown"
                    phase_counts[phase] += 1

                # Aggregate pod data
                for pod in all_pods:
                    creation_time = pod.metadata.creation_timestamp
                    if creation_time:
                        age_timedelta = datetime.now(timezone.utc) - creation_time
                        age_hours = age_timedelta.total_seconds() / 3600
                        age_str = f"{int(age_hours)}h" if age_hours < 24 else f"{int(age_hours / 24)}d"
                    else:
                        age_str = "N/A"

                    # Filter events related to this pod
                    pod_events = [
                        format_pod_event(event)
                        for event in events
                        if event.involved_object.kind == 'Pod' and event.involved_object.name == pod.metadata.name
                    ]

                    all_pods_data.append({
                        'cluster': cluster.name,
                        'name': pod.metadata.name,
                        'namespace': pod.metadata.namespace,
                        'status': pod.status.phase or 'Unknown',
                        'node': pod.spec.node_name or 'N/A',
                        'age': age_str,
                        'details_url': f"/pods/{pod.metadata.namespace}/{pod.metadata.name}/",
                        'events': pod_events,
                    })

                # Aggregate event data
                for event in events:
                    all_events_data.append(format_event(event, cluster.name))

                # Collect overview statistics, including kubeconfig file name
                all_overviews.append({
                    'cluster': cluster.name,
                    'kubeconfig_file': cluster.kubeconfig_file,  # Added field
                    'total_namespaces': total_namespaces,
                    'total_pods': total_pods,
                    'phase_counts': phase_counts,
                })

            # Prepare context for the template
            context = {
                'overviews': all_overviews,
                'pods_data_json': json.dumps(all_pods_data),
                'events_data_json': json.dumps(all_events_data),
            }

            return render(request, 'kubeBoard/index.html', context)

    except ApiException as e:
        error_message = f"API Error: {e.reason or 'An unknown API error occurred.'}"
        logger.error(f"API Exception: {error_message}")
        return render(request, 'kubeBoard/index.html', {'error': error_message})
    except Exception as e:
        error_message = f"Unexpected Error: {str(e)}"
        logger.error(f"Unexpected Exception: {error_message}")
        return render(request, 'kubeBoard/index.html', {'error': error_message})