# appConfig/kubeconfig.py

import logging
from pathlib import Path
import yaml

from kubernetes import client, config
from kubernetes.client import Configuration

# Configure logging
logger = logging.getLogger(__name__)

class ClusterClient:
    """
    Represents a Kubernetes cluster with its API clients.
    """
    def __init__(self, name, kubeconfig_file, core_v1, apps_v1, custom_api, metrics_api):
        self.name = name
        self.kubeconfig_file = kubeconfig_file
        self.core_v1 = core_v1
        self.apps_v1 = apps_v1
        self.custom_api = custom_api
        self.metrics_api = metrics_api

def load_kubeconfig(kubeconfig_path):
    """
    Loads a single kubeconfig file and initializes its API clients.

    Args:
        kubeconfig_path (Path): Path to the kubeconfig file.

    Returns:
        ClusterClient: An instance of ClusterClient.
    """
    try:
        with open(kubeconfig_path, 'r') as f:
            config_dict = yaml.safe_load(f)

        # Create a separate Configuration object
        configuration = Configuration()
        config.load_kube_config_from_dict(config_dict, client_configuration=configuration, context=None)

        # Initialize API clients with the specific configuration
        api_client = client.ApiClient(configuration)
        core_v1 = client.CoreV1Api(api_client)
        apps_v1 = client.AppsV1Api(api_client)
        custom_api = client.CustomObjectsApi(api_client)
        metrics_api = client.CustomObjectsApi(api_client)  # Metrics API is accessed via CustomObjectsApi

        # Extract cluster name from context
        current_context = config_dict.get('current-context')
        contexts = config_dict.get('contexts', [])
        cluster_name = "unknown-cluster"
        for context in contexts:
            if context.get('name') == current_context:
                cluster_name = context.get('context', {}).get('cluster', kubeconfig_path.stem)
                break

        logger.info(f"Successfully loaded cluster '{cluster_name}' from '{kubeconfig_path.name}'.")

        return ClusterClient(
            name=cluster_name,
            kubeconfig_file=kubeconfig_path.name,
            core_v1=core_v1,
            apps_v1=apps_v1,
            custom_api=custom_api,
            metrics_api=metrics_api
        )

    except Exception as e:
        logger.error(f"Failed to load kubeconfig '{kubeconfig_path}': {e}")
        return None

def list_kubeconfigs(kube_configs_dir="kubeConfigs/"):
    """
    Lists all kubeconfig files in the specified directory.

    Args:
        kube_configs_dir (str): Directory containing kubeconfig files.

    Returns:
        List[Path]: A list of Path objects pointing to kubeconfig files.
    """
    kube_dir = Path(kube_configs_dir)

    if not kube_dir.is_dir():
        logger.error(f"The path '{kube_configs_dir}' is not a directory.")
        return []

    kubeconfig_files = list(kube_dir.glob("*.yaml")) + list(kube_dir.glob("*.yml"))

    if not kubeconfig_files:
        logger.warning(f"No kubeconfig files found in '{kube_configs_dir}'.")

    return kubeconfig_files