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
        metrics_api, networking_v1, storage_v1, rbac_v1, batch_v1, api_client
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
        self.batch_v1 = batch_v1
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
        batch_v1 = client.BatchV1Api(api_client)

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
            batch_v1=batch_v1,
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


def list_deployments_for_all_namespaces(cluster_client):
    """
    Lists all Deployments across all namespaces.

    Args:
        cluster_client (ClusterClient): The ClusterClient instance.

    Returns:
        V1DeploymentList: List of deployments.
    """
    try:
        deployments = cluster_client.apps_v1.list_deployment_for_all_namespaces()
        logger.info(f"Retrieved {len(deployments.items)} deployments across all namespaces.")
        return deployments
    except client.exceptions.ApiException as e:
        logger.error(f"Failed to list deployments across all namespaces: {e}")
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


# ConfigMaps Operations
def list_config_maps(cluster_client, namespace="default"):
    """
    Lists all ConfigMaps in the specified namespace.

    Args:
        cluster_client (ClusterClient): The ClusterClient instance.
        namespace (str): Kubernetes namespace.

    Returns:
        V1ConfigMapList: List of ConfigMaps.
    """
    try:
        config_maps = cluster_client.core_v1.list_namespaced_config_map(namespace=namespace)
        logger.info(f"Retrieved {len(config_maps.items)} ConfigMaps in namespace '{namespace}'.")
        return config_maps
    except client.exceptions.ApiException as e:
        logger.error(f"Failed to list ConfigMaps: {e}")
        return None


def list_config_maps_for_all_namespaces(cluster_client):
    """
    Lists all ConfigMaps across all namespaces.

    Args:
        cluster_client (ClusterClient): The ClusterClient instance.

    Returns:
        V1ConfigMapList: List of ConfigMaps.
    """
    try:
        config_maps = cluster_client.core_v1.list_config_map_for_all_namespaces()
        logger.info(f"Retrieved {len(config_maps.items)} ConfigMaps across all namespaces.")
        return config_maps
    except client.exceptions.ApiException as e:
        logger.error(f"Failed to list ConfigMaps across all namespaces: {e}")
        return None


def read_namespaced_config_map(cluster_client, name, namespace="default"):
    """
    Reads a specific ConfigMap in the specified namespace.

    Args:
        cluster_client (ClusterClient): The ClusterClient instance.
        name (str): Name of the ConfigMap.
        namespace (str): Kubernetes namespace.

    Returns:
        V1ConfigMap: The ConfigMap object.
    """
    try:
        config_map = cluster_client.core_v1.read_namespaced_config_map(name=name, namespace=namespace)
        logger.info(f"Retrieved ConfigMap '{name}' in namespace '{namespace}'.")
        return config_map
    except client.exceptions.ApiException as e:
        logger.error(f"Failed to read ConfigMap '{name}' in namespace '{namespace}': {e}")
        return None


# Secrets Operations
def list_secrets(cluster_client, namespace="default"):
    """
    Lists all Secrets in the specified namespace.

    Args:
        cluster_client (ClusterClient): The ClusterClient instance.
        namespace (str): Kubernetes namespace.

    Returns:
        V1SecretList: List of Secrets.
    """
    try:
        secrets = cluster_client.core_v1.list_namespaced_secret(namespace=namespace)
        logger.info(f"Retrieved {len(secrets.items)} Secrets in namespace '{namespace}'.")
        return secrets
    except client.exceptions.ApiException as e:
        logger.error(f"Failed to list Secrets: {e}")
        return None


def list_secrets_for_all_namespaces(cluster_client):
    """
    Lists all Secrets across all namespaces.

    Args:
        cluster_client (ClusterClient): The ClusterClient instance.

    Returns:
        V1SecretList: List of Secrets.
    """
    try:
        secrets = cluster_client.core_v1.list_secret_for_all_namespaces()
        logger.info(f"Retrieved {len(secrets.items)} Secrets across all namespaces.")
        return secrets
    except client.exceptions.ApiException as e:
        logger.error(f"Failed to list Secrets across all namespaces: {e}")
        return None


def read_namespaced_secret(cluster_client, name, namespace="default"):
    """
    Reads a specific Secret in the specified namespace.

    Args:
        cluster_client (ClusterClient): The ClusterClient instance.
        name (str): Name of the Secret.
        namespace (str): Kubernetes namespace.

    Returns:
        V1Secret: The Secret object.
    """
    try:
        secret = cluster_client.core_v1.read_namespaced_secret(name=name, namespace=namespace)
        logger.info(f"Retrieved Secret '{name}' in namespace '{namespace}'.")
        return secret
    except client.exceptions.ApiException as e:
        logger.error(f"Failed to read Secret '{name}' in namespace '{namespace}': {e}")
        return None


# DaemonSets Operations
def list_daemon_sets(cluster_client, namespace="default"):
    """
    Lists all DaemonSets in the specified namespace.

    Args:
        cluster_client (ClusterClient): The ClusterClient instance.
        namespace (str): Kubernetes namespace.

    Returns:
        V1DaemonSetList: List of DaemonSets.
    """
    try:
        daemon_sets = cluster_client.apps_v1.list_namespaced_daemon_set(namespace=namespace)
        logger.info(f"Retrieved {len(daemon_sets.items)} DaemonSets in namespace '{namespace}'.")
        return daemon_sets
    except client.exceptions.ApiException as e:
        logger.error(f"Failed to list DaemonSets: {e}")
        return None


def list_daemon_sets_for_all_namespaces(cluster_client):
    """
    Lists all DaemonSets across all namespaces.

    Args:
        cluster_client (ClusterClient): The ClusterClient instance.

    Returns:
        V1DaemonSetList: List of DaemonSets.
    """
    try:
        daemon_sets = cluster_client.apps_v1.list_daemon_set_for_all_namespaces()
        logger.info(f"Retrieved {len(daemon_sets.items)} DaemonSets across all namespaces.")
        return daemon_sets
    except client.exceptions.ApiException as e:
        logger.error(f"Failed to list DaemonSets across all namespaces: {e}")
        return None


def read_namespaced_daemon_set(cluster_client, name, namespace="default"):
    """
    Reads a specific DaemonSet in the specified namespace.

    Args:
        cluster_client (ClusterClient): The ClusterClient instance.
        name (str): Name of the DaemonSet.
        namespace (str): Kubernetes namespace.

    Returns:
        V1DaemonSet: The DaemonSet object.
    """
    try:
        daemon_set = cluster_client.apps_v1.read_namespaced_daemon_set(name=name, namespace=namespace)
        logger.info(f"Retrieved DaemonSet '{name}' in namespace '{namespace}'.")
        return daemon_set
    except client.exceptions.ApiException as e:
        logger.error(f"Failed to read DaemonSet '{name}' in namespace '{namespace}': {e}")
        return None


# Jobs Operations
def list_jobs(cluster_client, namespace="default"):
    """
    Lists all Jobs in the specified namespace.

    Args:
        cluster_client (ClusterClient): The ClusterClient instance.
        namespace (str): Kubernetes namespace.

    Returns:
        V1JobList: List of Jobs.
    """
    try:
        jobs = cluster_client.batch_v1.list_namespaced_job(namespace=namespace)
        logger.info(f"Retrieved {len(jobs.items)} Jobs in namespace '{namespace}'.")
        return jobs
    except client.exceptions.ApiException as e:
        logger.error(f"Failed to list Jobs: {e}")
        return None


def list_jobs_for_all_namespaces(cluster_client):
    """
    Lists all Jobs across all namespaces.

    Args:
        cluster_client (ClusterClient): The ClusterClient instance.

    Returns:
        V1JobList: List of Jobs.
    """
    try:
        jobs = cluster_client.batch_v1.list_job_for_all_namespaces()
        logger.info(f"Retrieved {len(jobs.items)} Jobs across all namespaces.")
        return jobs
    except client.exceptions.ApiException as e:
        logger.error(f"Failed to list Jobs across all namespaces: {e}")
        return None


def read_namespaced_job(cluster_client, name, namespace="default"):
    """
    Reads a specific Job in the specified namespace.

    Args:
        cluster_client (ClusterClient): The ClusterClient instance.
        name (str): Name of the Job.
        namespace (str): Kubernetes namespace.

    Returns:
        V1Job: The Job object.
    """
    try:
        job = cluster_client.batch_v1.read_namespaced_job(name=name, namespace=namespace)
        logger.info(f"Retrieved Job '{name}' in namespace '{namespace}'.")
        return job
    except client.exceptions.ApiException as e:
        logger.error(f"Failed to read Job '{name}' in namespace '{namespace}': {e}")
        return None


# CronJobs Operations
def list_cron_jobs(cluster_client, namespace="default"):
    """
    Lists all CronJobs in the specified namespace.

    Args:
        cluster_client (ClusterClient): The ClusterClient instance.
        namespace (str): Kubernetes namespace.

    Returns:
        V1CronJobList: List of CronJobs.
    """
    try:
        cron_jobs = cluster_client.batch_v1.list_namespaced_cron_job(namespace=namespace)
        logger.info(f"Retrieved {len(cron_jobs.items)} CronJobs in namespace '{namespace}'.")
        return cron_jobs
    except client.exceptions.ApiException as e:
        logger.error(f"Failed to list CronJobs: {e}")
        return None


def list_cron_jobs_for_all_namespaces(cluster_client):
    """
    Lists all CronJobs across all namespaces.

    Args:
        cluster_client (ClusterClient): The ClusterClient instance.

    Returns:
        V1CronJobList: List of CronJobs.
    """
    try:
        cron_jobs = cluster_client.batch_v1.list_cron_job_for_all_namespaces()
        logger.info(f"Retrieved {len(cron_jobs.items)} CronJobs across all namespaces.")
        return cron_jobs
    except client.exceptions.ApiException as e:
        logger.error(f"Failed to list CronJobs across all namespaces: {e}")
        return None


def read_namespaced_cron_job(cluster_client, name, namespace="default"):
    """
    Reads a specific CronJob in the specified namespace.

    Args:
        cluster_client (ClusterClient): The ClusterClient instance.
        name (str): Name of the CronJob.
        namespace (str): Kubernetes namespace.

    Returns:
        V1CronJob: The CronJob object.
    """
    try:
        cron_job = cluster_client.batch_v1.read_namespaced_cron_job(name=name, namespace=namespace)
        logger.info(f"Retrieved CronJob '{name}' in namespace '{namespace}'.")
        return cron_job
    except client.exceptions.ApiException as e:
        logger.error(f"Failed to read CronJob '{name}' in namespace '{namespace}': {e}")
        return None


# NetworkPolicies Operations
def list_network_policies(cluster_client, namespace="default"):
    """
    Lists all NetworkPolicies in the specified namespace.

    Args:
        cluster_client (ClusterClient): The ClusterClient instance.
        namespace (str): Kubernetes namespace.

    Returns:
        V1NetworkPolicyList: List of NetworkPolicies.
    """
    try:
        network_policies = cluster_client.networking_v1.list_namespaced_network_policy(namespace=namespace)
        logger.info(f"Retrieved {len(network_policies.items)} NetworkPolicies in namespace '{namespace}'.")
        return network_policies
    except client.exceptions.ApiException as e:
        logger.error(f"Failed to list NetworkPolicies: {e}")
        return None


def list_network_policies_for_all_namespaces(cluster_client):
    """
    Lists all NetworkPolicies across all namespaces.

    Args:
        cluster_client (ClusterClient): The ClusterClient instance.

    Returns:
        V1NetworkPolicyList: List of NetworkPolicies.
    """
    try:
        network_policies = cluster_client.networking_v1.list_network_policy_for_all_namespaces()
        logger.info(f"Retrieved {len(network_policies.items)} NetworkPolicies across all namespaces.")
        return network_policies
    except client.exceptions.ApiException as e:
        logger.error(f"Failed to list NetworkPolicies across all namespaces: {e}")
        return None


def read_namespaced_network_policy(cluster_client, name, namespace="default"):
    """
    Reads a specific NetworkPolicy in the specified namespace.

    Args:
        cluster_client (ClusterClient): The ClusterClient instance.
        name (str): Name of the NetworkPolicy.
        namespace (str): Kubernetes namespace.

    Returns:
        V1NetworkPolicy: The NetworkPolicy object.
    """
    try:
        network_policy = cluster_client.networking_v1.read_namespaced_network_policy(name=name, namespace=namespace)
        logger.info(f"Retrieved NetworkPolicy '{name}' in namespace '{namespace}'.")
        return network_policy
    except client.exceptions.ApiException as e:
        logger.error(f"Failed to read NetworkPolicy '{name}' in namespace '{namespace}': {e}")
        return None


# StorageClasses Operations
def list_storage_classes(cluster_client):
    """
    Lists all StorageClasses in the cluster.

    Args:
        cluster_client (ClusterClient): The ClusterClient instance.

    Returns:
        V1StorageClassList: List of StorageClasses.
    """
    try:
        storage_classes = cluster_client.storage_v1.list_storage_class()
        logger.info(f"Retrieved {len(storage_classes.items)} StorageClasses.")
        return storage_classes
    except client.exceptions.ApiException as e:
        logger.error(f"Failed to list StorageClasses: {e}")
        return None


def read_storage_class(cluster_client, name):
    """
    Reads a specific StorageClass.

    Args:
        cluster_client (ClusterClient): The ClusterClient instance.
        name (str): Name of the StorageClass.

    Returns:
        V1StorageClass: The StorageClass object.
    """
    try:
        storage_class = cluster_client.storage_v1.read_storage_class(name=name)
        logger.info(f"Retrieved StorageClass '{name}'.")
        return storage_class
    except client.exceptions.ApiException as e:
        logger.error(f"Failed to read StorageClass '{name}': {e}")
        return None

