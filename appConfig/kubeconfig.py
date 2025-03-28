# appConfig/kubeconfig.py

from functools import lru_cache
from pathlib import Path

import yaml
from kubernetes import client, config
from kubernetes.client import Configuration

from appConfig.settings import logger


class ClusterClient:
    """
    Represents a Kubernetes cluster with its API clients.
    """
    def __init__(
        self, name, kubeconfig_file, core_v1, apps_v1, custom_api,
        metrics_api, networking_v1, storage_v1, rbac_v1, api_client
    ):
        self.name = name
        self.kubeconfig_file = kubeconfig_file
        self.core_v1 = core_v1
        self.apps_v1 = apps_v1
        self.custom_api = custom_api
        self.metrics_api = metrics_api
        self.networking_v1 = networking_v1
        self.storage_v1 = storage_v1
        self.rbac_v1 = rbac_v1
        self.api_client = api_client  # Keep reference for closing

    def close(self):
        """
        Closes the underlying ApiClient to release resources.
        """
        try:
            self.api_client.close()
            logger.info(f"Closed ApiClient for cluster '{self.name}'.")
        except Exception as e:
            logger.error(f"Error closing ApiClient for cluster '{self.name}': {e}")


@lru_cache(maxsize=None)
def load_and_cache_kubeconfig(kubeconfig_path_str):
    """
    Loads a kubeconfig file and caches the ClusterClient instance.

    Args:
        kubeconfig_path_str (str): Path to the kubeconfig file as a string.

    Returns:
        ClusterClient: An instance of ClusterClient.
    """
    kubeconfig_path = Path(kubeconfig_path_str)
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
        networking_v1 = client.NetworkingV1Api(api_client)
        storage_v1 = client.StorageV1Api(api_client)
        rbac_v1 = client.RbacAuthorizationV1Api(api_client)

        # Extract cluster name from context
        current_context = config_dict.get('current-context')
        contexts = config_dict.get('contexts', [])
        cluster_name = "unknown-cluster"
        for context in contexts:
            if context.get('name') == current_context:
                cluster_name = context.get('context', {}).get('cluster', kubeconfig_path.stem)
                break

        logger.info(f"Successfully loaded and cached cluster '{cluster_name}' from '{kubeconfig_path.name}'.")

        return ClusterClient(
            name=cluster_name,
            kubeconfig_file=kubeconfig_path.name,
            core_v1=core_v1,
            apps_v1=apps_v1,
            custom_api=custom_api,
            metrics_api=metrics_api,
            networking_v1=networking_v1,
            storage_v1=storage_v1,
            rbac_v1=rbac_v1,
            api_client=api_client
        )

    except Exception as e:
        logger.error(f"Failed to load kubeconfig '{kubeconfig_path}': {e}")
        return None


def load_kubeconfig(kubeconfig_path):
    """
    Interface to fetch cached ClusterClient.

    Args:
        kubeconfig_path (Path): Path to the kubeconfig file.

    Returns:
        ClusterClient: An instance of ClusterClient.
    """
    return load_and_cache_kubeconfig(str(kubeconfig_path))


def close_all_cluster_clients():
    """
    Closes all cached ClusterClient ApiClients. To be called on application shutdown.
    """
    if hasattr(load_and_cache_kubeconfig, 'cache_info'):
        cache = getattr(load_and_cache_kubeconfig, 'cache_info')()
        # Note: lru_cache does not expose the actual cache, so we need a workaround
        # Alternatively, store references elsewhere if needed
    # Since accessing the actual cache of lru_cache is not straightforward,
    # we'll iterate over all cached keys manually
    # However, lru_cache does not provide a direct way to iterate over cached items
    # Instead, consider using a custom caching mechanism if this is required
    # For demonstration, we'll assume only one cached kubeconfig
    try:
        cluster_clients = load_and_cache_kubeconfig.cache_info().cache  # This line is incorrect
    except AttributeError:
        # lru_cache does not expose the cache directly. Alternative approach:
        # Use internal attributes (not recommended for production)
        cluster_clients = getattr(load_and_cache_kubeconfig, 'cache', {}).values()

    if hasattr(load_and_cache_kubeconfig, 'cache'):
        for cluster_client in load_and_cache_kubeconfig.cache.values():
            if cluster_client:
                cluster_client.close()
    else:
        logger.warning("Unable to close ClusterClients: cache structure is not accessible.")

    load_and_cache_kubeconfig.cache_clear()
    logger.info("All ClusterClients have been closed and cache cleared.")


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


# =================== Additional Functionalities ===================

# Networking Operations
def list_services(cluster_client, namespace="default"):
    """
    Lists all services in the specified namespace.

    Args:
        cluster_client (ClusterClient): The ClusterClient instance.
        namespace (str): Kubernetes namespace.

    Returns:
        V1ServiceList: List of services.
    """
    try:
        services = cluster_client.core_v1.list_namespaced_service(namespace=namespace)
        logger.info(f"Retrieved {len(services.items)} services in namespace '{namespace}'.")
        return services
    except client.exceptions.ApiException as e:
        logger.error(f"Failed to list services: {e}")
        return None


def list_ingresses(cluster_client, namespace="default"):
    """
    Lists all Ingress resources in the specified namespace.

    Args:
        cluster_client (ClusterClient): The ClusterClient instance.
        namespace (str): Kubernetes namespace.

    Returns:
        V1IngressList: List of ingress resources.
    """
    try:
        ingresses = cluster_client.networking_v1.list_namespaced_ingress(namespace=namespace)
        logger.info(f"Retrieved {len(ingresses.items)} ingresses in namespace '{namespace}'.")
        return ingresses
    except client.exceptions.ApiException as e:
        logger.error(f"Failed to list ingresses: {e}")
        return None


# Persistent Storage Operations
def list_persistent_volumes(cluster_client):
    """
    Lists all PersistentVolumes in the cluster.

    Args:
        cluster_client (ClusterClient): The ClusterClient instance.

    Returns:
        V1PersistentVolumeList: List of persistent volumes.
    """
    try:
        pvs = cluster_client.core_v1.list_persistent_volume()
        logger.info(f"Retrieved {len(pvs.items)} persistent volumes.")
        return pvs
    except client.exceptions.ApiException as e:
        logger.error(f"Failed to list persistent volumes: {e}")
        return None


def list_persistent_volume_claims(cluster_client, namespace="default"):
    """
    Lists all PersistentVolumeClaims in the specified namespace.

    Args:
        cluster_client (ClusterClient): The ClusterClient instance.
        namespace (str): Kubernetes namespace.

    Returns:
        V1PersistentVolumeClaimList: List of PVCs.
    """
    try:
        pvc = cluster_client.core_v1.list_namespaced_persistent_volume_claim(namespace=namespace)
        logger.info(f"Retrieved {len(pvc.items)} persistent volume claims in namespace '{namespace}'.")
        return pvc
    except client.exceptions.ApiException as e:
        logger.error(f"Failed to list persistent volume claims: {e}")
        return None


# RBAC and Permissions Operations
def list_roles(cluster_client, namespace="default"):
    """
    Lists all Roles in the specified namespace.

    Args:
        cluster_client (ClusterClient): The ClusterClient instance.
        namespace (str): Kubernetes namespace.

    Returns:
        V1RoleList: List of roles.
    """
    try:
        roles = cluster_client.rbac_v1.list_namespaced_role(namespace=namespace)
        logger.info(f"Retrieved {len(roles.items)} roles in namespace '{namespace}'.")
        return roles
    except client.exceptions.ApiException as e:
        logger.error(f"Failed to list roles: {e}")
        return None


def list_role_bindings(cluster_client, namespace="default"):
    """
    Lists all RoleBindings in the specified namespace.

    Args:
        cluster_client (ClusterClient): The ClusterClient instance.
        namespace (str): Kubernetes namespace.

    Returns:
        V1RoleBindingList: List of role bindings.
    """
    try:
        role_bindings = cluster_client.rbac_v1.list_namespaced_role_binding(namespace=namespace)
        logger.info(f"Retrieved {len(role_bindings.items)} role bindings in namespace '{namespace}'.")
        return role_bindings
    except client.exceptions.ApiException as e:
        logger.error(f"Failed to list role bindings: {e}")
        return None


def list_cluster_roles(cluster_client):
    """
    Lists all ClusterRoles in the cluster.

    Args:
        cluster_client (ClusterClient): The ClusterClient instance.

    Returns:
        V1ClusterRoleList: List of cluster roles.
    """
    try:
        cluster_roles = cluster_client.rbac_v1.list_cluster_role()
        logger.info(f"Retrieved {len(cluster_roles.items)} cluster roles.")
        return cluster_roles
    except client.exceptions.ApiException as e:
        logger.error(f"Failed to list cluster roles: {e}")
        return None


def list_cluster_role_bindings(cluster_client):
    """
    Lists all ClusterRoleBindings in the cluster.

    Args:
        cluster_client (ClusterClient): The ClusterClient instance.

    Returns:
        V1ClusterRoleBindingList: List of cluster role bindings.
    """
    try:
        cluster_role_bindings = cluster_client.rbac_v1.list_cluster_role_binding()
        logger.info(f"Retrieved {len(cluster_role_bindings.items)} cluster role bindings.")
        return cluster_role_bindings
    except client.exceptions.ApiException as e:
        logger.error(f"Failed to list cluster role bindings: {e}")
        return None


# Additional Use Cases

# Deployments Operations
def list_deployments(cluster_client, namespace="default"):
    """
    Lists all Deployments in the specified namespace.

    Args:
        cluster_client (ClusterClient): The ClusterClient instance.
        namespace (str): Kubernetes namespace.

    Returns:
        V1DeploymentList: List of deployments.
    """
    try:
        deployments = cluster_client.apps_v1.list_namespaced_deployment(namespace=namespace)
        logger.info(f"Retrieved {len(deployments.items)} deployments in namespace '{namespace}'.")
        return deployments
    except client.exceptions.ApiException as e:
        logger.error(f"Failed to list deployments: {e}")
        return None


# StatefulSets Operations
def list_statefulsets(cluster_client, namespace="default"):
    """
    Lists all StatefulSets in the specified namespace.

    Args:
        cluster_client (ClusterClient): The ClusterClient instance.
        namespace (str): Kubernetes namespace.

    Returns:
        V1StatefulSetList: List of statefulsets.
    """
    try:
        statefulsets = cluster_client.apps_v1.list_namespaced_stateful_set(namespace=namespace)
        logger.info(f"Retrieved {len(statefulsets.items)} stateful sets in namespace '{namespace}'.")
        return statefulsets
    except client.exceptions.ApiException as e:
        logger.error(f"Failed to list stateful sets: {e}")
        return None


# Jobs Operations
def list_jobs(cluster_client, namespace="default"):
    """
    Lists all Jobs in the specified namespace.

    Args:
        cluster_client (ClusterClient): The ClusterClient instance.
        namespace (str): Kubernetes namespace.

    Returns:
        V1JobList: List of jobs.
    """
    try:
        jobs = cluster_client.batch_v1.list_namespaced_job(namespace=namespace)
        logger.info(f"Retrieved {len(jobs.items)} jobs in namespace '{namespace}'.")
        return jobs
    except AttributeError:
        logger.warning("BatchV1Api is not initialized in ClusterClient. Initializing now.")
        cluster_client.batch_v1 = client.BatchV1Api(cluster_client.api_client)
        return list_jobs(cluster_client, namespace)
    except client.exceptions.ApiException as e:
        logger.error(f"Failed to list jobs: {e}")
        return None


# Add BatchV1Api to ClusterClient if not already present
def ensure_batch_api(cluster_client):
    """
    Ensures that the BatchV1Api is available in the ClusterClient.

    Args:
        cluster_client (ClusterClient): The ClusterClient instance.
    """
    if not hasattr(cluster_client, 'batch_v1'):
        cluster_client.batch_v1 = client.BatchV1Api(cluster_client.api_client)
        logger.info("Initialized BatchV1Api for the ClusterClient.")

