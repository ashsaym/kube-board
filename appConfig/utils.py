# appConfig/utils.py

import threading
from pathlib import Path
from datetime import datetime, timezone
from typing import Tuple, Any, Dict, Optional

from django.http import HttpResponse
from kubernetes.client import ApiException

from appConfig.kubeconfig import load_kubeconfig, list_kubeconfigs
from appConfig.settings import logger

class KubernetesResourceView:
    """Base class for Kubernetes resource views with common functionality"""
    
    @staticmethod
    def format_age(creation_timestamp) -> str:
        if not creation_timestamp:
            return "N/A"
        age_timedelta = datetime.now(timezone.utc) - creation_timestamp
        age_hours = age_timedelta.total_seconds() / 3600
        return f"{int(age_hours)}h" if age_hours < 24 else f"{int(age_hours / 24)}d"

    @staticmethod
    def handle_api_error(e: ApiException, view_name: str) -> HttpResponse:
        if e.status == 404:
            return HttpResponse("Resource not found", status=404)
        error_message = f"API Error: {e.reason or 'An unknown API error occurred.'}"
        logger.error(f"API Exception in {view_name}: {error_message}")
        return HttpResponse(error_message, status=e.status if e.status else 500)

    @staticmethod
    def handle_general_error(e: Exception, view_name: str) -> HttpResponse:
        error_message = f"Unexpected Error: {str(e)}"
        logger.error(f"Unexpected Exception in {view_name}: {error_message}")
        return HttpResponse(error_message, status=500)

    @staticmethod
    def format_resource_overview(resource: Any) -> Dict[str, str]:
        """Format common resource information"""
        metadata = resource.metadata
        return {
            'name': metadata.name,
            'namespace': metadata.namespace,
            'creation_timestamp': metadata.creation_timestamp,
            'labels': metadata.labels or {},
            'annotations': metadata.annotations or {},
        }

    @staticmethod
    def format_event(event: Any) -> Dict[str, Any]:
        """Format a Kubernetes event"""
        first_seen = ""
        last_seen = ""
        if event.first_timestamp:
            first_seen = event.first_timestamp.strftime("%Y-%m-%d %H:%M:%S")
        if event.last_timestamp:
            last_seen = event.last_timestamp.strftime("%Y-%m-%d %H:%M:%S")

        return {
            'type': event.type,
            'reason': event.reason,
            'message': event.message,
            'count': event.count,
            'first_seen': first_seen,
            'last_seen': last_seen,
            'source_component': event.source.component if event.source else '',
            'source_host': event.source.host if event.source else '',
        }

# Define a semaphore with a maximum number of concurrent streams
MAX_CONCURRENT_STREAMS = 10  # Adjust based on your server's capacity
log_stream_semaphore = threading.Semaphore(MAX_CONCURRENT_STREAMS)

def acquire_stream_semaphore():
    """
    Acquires the semaphore for a new log stream.
    Returns True if acquired, False otherwise.
    """
    acquired = log_stream_semaphore.acquire(blocking=False)
    if not acquired:
        logger.warning("Failed to acquire semaphore for new log stream.")
    return acquired

def release_stream_semaphore():
    """
    Releases the semaphore when a log stream is closed.
    """
    log_stream_semaphore.release()

def get_cluster_client(request):
    """
    Retrieves the currently selected ClusterClient based on the user's session.

    Args:
        request (HttpRequest): The incoming HTTP request.

    Returns:
        ClusterClient: The selected ClusterClient instance.
        str: An error message if something goes wrong, otherwise None.
    """
    selected_kubeconfig = request.session.get('selected_kubeconfig')

    if not selected_kubeconfig:
        error_message = "No Kubernetes kubeconfig is selected."
        logger.error(error_message)
        return None, error_message

    kubeconfig_files = [kc.name for kc in list_kubeconfigs()]
    if selected_kubeconfig not in kubeconfig_files:
        error_message = f"Selected kubeconfig '{selected_kubeconfig}' is not available."
        logger.error(error_message)
        return None, error_message

    kubeconfig_path = Path("kubeConfigs") / selected_kubeconfig
    cluster = load_kubeconfig(kubeconfig_path)

    if not cluster:
        error_message = f"Failed to load kubeconfig '{selected_kubeconfig}'."
        logger.error(error_message)
        return None, error_message

    return cluster, None