# appConfig/kubeconfig.py

import logging
import threading
from pathlib import Path
import yaml

from kubernetes import client, config
from kubernetes.client import Configuration

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class ClusterClient:
    """
    Represents a Kubernetes cluster with its API clients.
    """
    def __init__(self, name, kubeconfig_file, core_v1, apps_v1, custom_api):
        self.name = name
        self.kubeconfig_file = kubeconfig_file  # Added attribute
        self.core_v1 = core_v1
        self.apps_v1 = apps_v1
        self.custom_api = custom_api


# Global list to store ClusterClient instances
cluster_clients = []
cluster_clients_lock = threading.Lock()

# Event to signal that loading is complete
loading_done = threading.Event()


def load_single_kubeconfig(kubeconfig_path):
    """
    Loads a single kubeconfig file and initializes its API clients.

    Args:
        kubeconfig_path (Path): Path to the kubeconfig file.
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

        # Extract cluster name from context
        current_context = config_dict.get('current-context')
        contexts = config_dict.get('contexts', [])
        cluster_name = "unknown-cluster"
        for context in contexts:
            if context.get('name') == current_context:
                cluster_name = context.get('context', {}).get('cluster', kubeconfig_path.stem)
                break

        # Create and store the ClusterClient instance
        cluster_client = ClusterClient(
            name=cluster_name,
            kubeconfig_file=kubeconfig_path.name,  # Capture the file name
            core_v1=core_v1,
            apps_v1=apps_v1,
            custom_api=custom_api
        )

        with cluster_clients_lock:
            cluster_clients.append(cluster_client)

        logger.info(f"Successfully loaded cluster '{cluster_name}' from '{kubeconfig_path.name}'.")

    except Exception as e:
        logger.error(f"Failed to load kubeconfig '{kubeconfig_path}': {e}")


def load_all_kubeconfigs(kube_configs_dir="kubeConfigs/"):
    """
    Loads all kubeconfig files from the specified directory.

    Args:
        kube_configs_dir (str): Directory containing kubeconfig files.
    """
    kube_dir = Path(kube_configs_dir)

    if not kube_dir.is_dir():
        logger.error(f"The path '{kube_configs_dir}' is not a directory.")
        loading_done.set()
        return

    # Adjust the pattern if your kubeconfig files have different extensions
    kubeconfig_files = list(kube_dir.glob("*.yaml")) + list(kube_dir.glob("*.yml"))

    if not kubeconfig_files:
        logger.warning(f"No kubeconfig files found in '{kube_configs_dir}'.")
        loading_done.set()
        return

    for kubeconfig_file in kubeconfig_files:
        load_single_kubeconfig(kubeconfig_file)

    # Signal that loading is complete
    loading_done.set()


def background_loader(kube_configs_dir="kubeConfigs/"):
    """
    Runs the kubeconfig loader in a separate thread.
    """
    load_all_kubeconfigs(kube_configs_dir)


# Start the background loader thread
loader_thread = threading.Thread(target=background_loader, daemon=True)
loader_thread.start()