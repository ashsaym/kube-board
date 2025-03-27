# appConfig/utils.py

from django.http import HttpResponse
from pathlib import Path
from appConfig.kubeconfig import load_kubeconfig, list_kubeconfigs
import logging

logger = logging.getLogger(__name__)


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