# appConfig/utils.py

import threading
from pathlib import Path

from appConfig.kubeconfig import load_kubeconfig, list_kubeconfigs
from appConfig.settings import logger

# Define a semaphore with a maximum number of concurrent streams
MAX_CONCURRENT_STREAMS = 10  # Adjust based on your server's capacity
log_stream_semaphore = threading.Semaphore(MAX_CONCURRENT_STREAMS)

def acquire_stream_semaphore():
    """
    Acquires the semaphore for a new log stream.
    Returns True if acquired, False otherwise.
    """
    return log_stream_semaphore.acquire(blocking=False)

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