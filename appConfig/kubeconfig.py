import logging
import os

from kubernetes import client, config

logger = logging.getLogger(__name__)
# Kubernetes Client Setup
def load_kube_config():
    config_file = os.getenv("KUBECONFIG_PATH", "kubeConfigs/config-3.yaml")
    logger.info(f"Loading Kubernetes config from {config_file}")
    try:
        config.load_kube_config(config_file=config_file)
    except Exception as e:
        logger.error(f"Failed to load Kubernetes config: {e}")
        raise


load_kube_config()
v1 = client.CoreV1Api()
custom_api = client.CustomObjectsApi()
apps_v1 = client.AppsV1Api()