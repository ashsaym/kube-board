# kubeBoard/views.py

import json
from collections import defaultdict
from datetime import datetime, timezone

from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST
from kubernetes.client.exceptions import ApiException

from appConfig.kubeconfig import list_kubeconfigs
from appConfig.settings import logger
from appConfig.utils import get_cluster_client


def parse_cpu(cpu_str):
    """
    Parses CPU usage strings from Kubernetes metrics and converts to millicores.

    Args:
        cpu_str (str): CPU usage string (e.g., '500m', '1', '250n').

    Returns:
        float: CPU usage in millicores.
    """
    try:
        if cpu_str.endswith('n'):
            # nano cores
            return float(cpu_str[:-1]) / 1e6  # millicores
        elif cpu_str.endswith('u'):
            # micro cores
            return float(cpu_str[:-1]) / 1e3  # millicores
        elif cpu_str.endswith('m'):
            return float(cpu_str[:-1])  # millicores
        else:
            # assuming it's in cores
            return float(cpu_str) * 1000  # millicores
    except ValueError as e:
        logger.error(f"Error parsing CPU string '{cpu_str}': {e}")
        return 0.0


def parse_ram(ram_str):
    """
    Parses RAM usage strings from Kubernetes metrics and converts to MiB.

    Args:
        ram_str (str): RAM usage string (e.g., '256Mi', '1Gi', '512Ki').

    Returns:
        float: RAM usage in MiB.
    """
    try:
        if ram_str.endswith('Ki'):
            return float(ram_str[:-2]) / 1024
        elif ram_str.endswith('Mi'):
            return float(ram_str[:-2])
        elif ram_str.endswith('Gi'):
            return float(ram_str[:-2]) * 1024
        elif ram_str.endswith('Ti'):
            return float(ram_str[:-2]) * 1024 * 1024
        elif ram_str.endswith('n'):
            # Unlikely, set to 0
            return 0.0
        else:
            # Unknown unit, set to 0
            logger.warning(f"Unknown RAM unit in '{ram_str}'")
            return 0.0
    except ValueError as e:
        logger.error(f"Error parsing RAM string '{ram_str}': {e}")
        return 0.0


def format_event(event, kubeconfig_file):
    """Formats an event for general usage."""
    namespace = event.metadata.namespace or 'default'
    event_name = event.metadata.name or 'unknown-event'
    object_name = (event.involved_object.name or 'unknown-object') if event.involved_object else 'unknown-object'
    kind = (event.involved_object.kind or 'UnknownKind') if event.involved_object else 'UnknownKind'
    details_url = f"/events/{namespace}/{event_name}/" if (namespace != 'default' and event_name != 'unknown-event') else "#"
    first_seen = event.first_timestamp.replace(tzinfo=timezone.utc).astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S") if event.first_timestamp else ''
    last_seen = event.last_timestamp.replace(tzinfo=timezone.utc).astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S") if event.last_timestamp else ''
    return {
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
    Renders the main dashboard page with data from the selected Kubernetes cluster.
    """
    try:
        cluster, error = get_cluster_client(request)
        if error:
            return render(request, 'kubeBoard/index.html', {'error': error})

        # Retrieve namespaces
        try:
            all_namespaces = cluster.core_v1.list_namespace().items
        except ApiException as e:
            logger.error(f"Failed to retrieve namespaces for kubeconfig '{cluster.kubeconfig_file}': {e}")
            all_namespaces = []

        # Retrieve pods
        try:
            all_pods = cluster.core_v1.list_pod_for_all_namespaces().items
        except ApiException as e:
            logger.error(f"Failed to retrieve pods for kubeconfig '{cluster.kubeconfig_file}': {e}")
            all_pods = []

        # Retrieve events
        try:
            events = cluster.core_v1.list_event_for_all_namespaces(limit=1000).items
        except ApiException as e:
            logger.error(f"Failed to retrieve events for kubeconfig '{cluster.kubeconfig_file}': {e}")
            events = []

        # Retrieve nodes
        try:
            all_nodes = cluster.core_v1.list_node().items
        except ApiException as e:
            logger.error(f"Failed to retrieve nodes for kubeconfig '{cluster.kubeconfig_file}': {e}")
            all_nodes = []

        # Retrieve metrics (CPU and RAM)
        try:
            metrics = cluster.metrics_api.list_cluster_custom_object(
                group="metrics.k8s.io",
                version="v1beta1",
                plural="pods"
            )
            metrics_items = metrics.get('items', [])
        except ApiException as e:
            logger.error(f"Failed to retrieve metrics for kubeconfig '{cluster.kubeconfig_file}': {e}")
            metrics_items = []

        # Compute total cluster capacity
        total_cpu_capacity = 0  # in millicores
        total_ram_capacity = 0  # in MiB

        for node in all_nodes:
            capacity = node.status.capacity
            cpu = capacity.get('cpu', '0')
            ram_str = capacity.get('memory', '0')
            # Parse CPU
            try:
                cpu_cores = float(cpu)
                total_cpu_capacity += cpu_cores * 1000  # millicores
            except ValueError as e:
                logger.error(f"Error parsing node CPU '{cpu}': {e}")
            # Parse RAM
            try:
                ram_mi = parse_ram(ram_str)
                total_ram_capacity += ram_mi
            except ValueError as e:
                logger.error(f"Error parsing node RAM '{ram_str}': {e}")

        # Compute metrics
        total_cpu_usage = 0.0  # in millicores
        total_ram_usage = 0.0  # in MiB
        pod_metrics = {}

        for metric in metrics_items:
            namespace = metric.get('metadata', {}).get('namespace', 'default')
            name = metric.get('metadata', {}).get('name', 'unknown')
            containers = metric.get('containers', [])
            pod_cpu = 0.0
            pod_ram = 0.0
            for container in containers:
                cpu = container.get('usage', {}).get('cpu', '0m')
                ram = container.get('usage', {}).get('memory', '0Mi')
                # Parse CPU
                pod_cpu += parse_cpu(cpu)
                # Parse RAM
                pod_ram += parse_ram(ram)
            total_cpu_usage += pod_cpu
            total_ram_usage += pod_ram
            pod_metrics[(namespace, name)] = {
                'cpu_usage': f"{pod_cpu:.2f}m",
                'ram_usage': f"{pod_ram:.2f}Mi"
            }

        # Compute usage percentages
        cpu_percentage = (total_cpu_usage / total_cpu_capacity) * 100 if total_cpu_capacity > 0 else 0
        ram_percentage = (total_ram_usage / total_ram_capacity) * 100 if total_ram_capacity > 0 else 0

        # Compute summary statistics
        total_namespaces = len(all_namespaces)
        total_pods = len(all_pods)
        total_nodes = len(all_nodes)
        phase_counts = defaultdict(int)
        for pod in all_pods:
            phase = pod.status.phase or "Unknown"
            phase_counts[phase] += 1

        # Aggregate pod data
        all_pods_data = []
        for pod in all_pods:
            creation_time = pod.metadata.creation_timestamp
            if creation_time:
                age_timedelta = datetime.now(timezone.utc) - creation_time
                age_hours = age_timedelta.total_seconds() / 3600
                age_str = f"{int(age_hours)}h" if age_hours < 24 else f"{int(age_hours / 24)}d"
            else:
                age_str = "N/A"

            # Get pod metrics
            metrics = pod_metrics.get((pod.metadata.namespace, pod.metadata.name), {})
            cpu_usage = metrics.get('cpu_usage', '0.00m')
            ram_usage = metrics.get('ram_usage', '0.00Mi')

            # Filter events related to this pod
            pod_events = [
                format_pod_event(event)
                for event in events
                if event.involved_object.kind == 'Pod' and event.involved_object.name == pod.metadata.name
            ]

            all_pods_data.append({
                'name': pod.metadata.name,
                'namespace': pod.metadata.namespace,
                'status': pod.status.phase or 'Unknown',
                'node': pod.spec.node_name or 'N/A',
                'age': age_str,
                'cpu_usage': cpu_usage,
                'ram_usage': ram_usage,
                'details_url': f"/pods/{pod.metadata.namespace}/{pod.metadata.name}/",
            })

        # Aggregate event data
        all_events_data = []
        for event in events:
            all_events_data.append(format_event(event, cluster.kubeconfig_file))

        # ================== Ingresses Overview ==================

        # Retrieve Ingresses
        try:
            all_ingresses = cluster.networking_v1.list_ingress_for_all_namespaces().items
            logger.info(f"Retrieved {len(all_ingresses)} ingresses.")
        except ApiException as e:
            logger.error(f"Failed to retrieve ingresses for kubeconfig '{cluster.kubeconfig_file}': {e}")
            all_ingresses = []

        # Process ingresses
        all_ingresses_data = []
        for ingress in all_ingresses:
            name = ingress.metadata.name or 'Unnamed'
            namespace = ingress.metadata.namespace or 'default'
            rules = ingress.spec.rules if ingress.spec else []
            host = rules[0].host if rules else 'N/A'
            paths = []
            for rule in rules:
                if rule.http:
                    for path in rule.http.paths:
                        paths.append(path.path)
            creation_timestamp = ingress.metadata.creation_timestamp
            if creation_timestamp:
                age_timedelta = datetime.now(timezone.utc) - creation_timestamp
                age_hours = age_timedelta.total_seconds() / 3600
                age_str = f"{int(age_hours)}h" if age_hours < 24 else f"{int(age_hours / 24)}d"
            else:
                age_str = "N/A"

            all_ingresses_data.append({
                'name': name,
                'namespace': namespace,
                'host': host,
                'paths': ', '.join(paths),
                'age': age_str,
                'details_url': f"/ingresses/{namespace}/{name}/",
            })

        # Convert to JSON
        ingresses_data_json = json.dumps(all_ingresses_data)

        # ================== End Ingresses Overview ==================

        # ================== ConfigMaps Overview ==================

        # Retrieve ConfigMaps
        try:
            all_config_maps = cluster.core_v1.list_config_map_for_all_namespaces().items
            logger.info(f"Retrieved {len(all_config_maps)} ConfigMaps.")
        except ApiException as e:
            logger.error(f"Failed to retrieve ConfigMaps for kubeconfig '{cluster.kubeconfig_file}': {e}")
            all_config_maps = []

        # Process ConfigMaps
        all_config_maps_data = []
        for config_map in all_config_maps:
            name = config_map.metadata.name or 'Unnamed'
            namespace = config_map.metadata.namespace or 'default'
            data_count = len(config_map.data) if config_map.data else 0
            creation_timestamp = config_map.metadata.creation_timestamp
            if creation_timestamp:
                age_timedelta = datetime.now(timezone.utc) - creation_timestamp
                age_hours = age_timedelta.total_seconds() / 3600
                age_str = f"{int(age_hours)}h" if age_hours < 24 else f"{int(age_hours / 24)}d"
            else:
                age_str = "N/A"

            all_config_maps_data.append({
                'name': name,
                'namespace': namespace,
                'data_count': data_count,
                'age': age_str,
                'details_url': f"/configmaps/{namespace}/{name}/",
            })

        # Convert to JSON
        config_maps_data_json = json.dumps(all_config_maps_data)

        # ================== End ConfigMaps Overview ==================

        # ================== Deployments Overview ==================

        # Retrieve Deployments
        try:
            all_deployments = cluster.apps_v1.list_deployment_for_all_namespaces().items
            logger.info(f"Retrieved {len(all_deployments)} Deployments.")
        except ApiException as e:
            logger.error(f"Failed to retrieve Deployments for kubeconfig '{cluster.kubeconfig_file}': {e}")
            all_deployments = []

        # Process Deployments
        all_deployments_data = []
        for deployment in all_deployments:
            name = deployment.metadata.name or 'Unnamed'
            namespace = deployment.metadata.namespace or 'default'
            replicas = deployment.status.replicas or 0
            ready_replicas = deployment.status.ready_replicas or 0
            readiness = f"{ready_replicas}/{replicas}"
            creation_timestamp = deployment.metadata.creation_timestamp
            if creation_timestamp:
                age_timedelta = datetime.now(timezone.utc) - creation_timestamp
                age_hours = age_timedelta.total_seconds() / 3600
                age_str = f"{int(age_hours)}h" if age_hours < 24 else f"{int(age_hours / 24)}d"
            else:
                age_str = "N/A"

            all_deployments_data.append({
                'name': name,
                'namespace': namespace,
                'readiness': readiness,
                'age': age_str,
                'details_url': f"/deployments/{namespace}/{name}/",
            })

        # Convert to JSON
        deployments_data_json = json.dumps(all_deployments_data)

        # ================== End Deployments Overview ==================

        # ================== DaemonSets Overview ==================

        # Retrieve DaemonSets
        try:
            all_daemon_sets = cluster.apps_v1.list_daemon_set_for_all_namespaces().items
            logger.info(f"Retrieved {len(all_daemon_sets)} DaemonSets.")
        except ApiException as e:
            logger.error(f"Failed to retrieve DaemonSets for kubeconfig '{cluster.kubeconfig_file}': {e}")
            all_daemon_sets = []

        # Process DaemonSets
        all_daemon_sets_data = []
        for daemon_set in all_daemon_sets:
            name = daemon_set.metadata.name or 'Unnamed'
            namespace = daemon_set.metadata.namespace or 'default'
            desired_count = daemon_set.status.desired_number_scheduled or 0
            current_count = daemon_set.status.current_number_scheduled or 0
            readiness = f"{current_count}/{desired_count}"
            creation_timestamp = daemon_set.metadata.creation_timestamp
            if creation_timestamp:
                age_timedelta = datetime.now(timezone.utc) - creation_timestamp
                age_hours = age_timedelta.total_seconds() / 3600
                age_str = f"{int(age_hours)}h" if age_hours < 24 else f"{int(age_hours / 24)}d"
            else:
                age_str = "N/A"

            all_daemon_sets_data.append({
                'name': name,
                'namespace': namespace,
                'readiness': readiness,
                'age': age_str,
                'details_url': f"/daemonsets/{namespace}/{name}/",
            })

        # Convert to JSON
        daemon_sets_data_json = json.dumps(all_daemon_sets_data)

        # ================== End DaemonSets Overview ==================

        # Collect overview statistics
        all_overviews = [{
            'total_namespaces': total_namespaces,
            'total_pods': total_pods,
            'total_nodes': total_nodes,
            'phase_counts': phase_counts,
            'cpu_usage_percent': round(cpu_percentage, 2),
            'ram_usage_percent': round(ram_percentage, 2),
        }]

        # Define dynamic kubectl commands
        kube_commands = {
            'cluster_info': 'kubectl cluster-info',
            'get_namespaces': 'kubectl get namespaces',
            'get_pods': 'kubectl get pods --all-namespaces',
            'get_running_pods': 'kubectl get pods --all-namespaces --field-selector=status.phase=Running',
            'get_pending_pods': 'kubectl get pods --all-namespaces --field-selector=status.phase=Pending',
            'get_failed_pods': 'kubectl get pods --all-namespaces --field-selector=status.phase=Failed',
            'get_cpu_usage': 'kubectl top pods --all-namespaces',
            'get_ram_usage': 'kubectl top pods --all-namespaces',
            'get_nodes': 'kubectl get nodes',
            'get_all_pods': 'kubectl get pods --all-namespaces',
            'get_all_events': 'kubectl get events --all-namespaces',
            'get_ingresses': 'kubectl get ingress --all-namespaces',
            'get_configmaps': 'kubectl get configmaps --all-namespaces',
            'get_secrets': 'kubectl get secrets --all-namespaces',
            'get_deployments': 'kubectl get deployments --all-namespaces',
            'get_statefulsets': 'kubectl get statefulsets --all-namespaces',
            'get_daemonsets': 'kubectl get daemonsets --all-namespaces',
            'get_jobs': 'kubectl get jobs --all-namespaces',
            'get_cronjobs': 'kubectl get cronjobs --all-namespaces',
            'get_networkpolicies': 'kubectl get networkpolicies --all-namespaces',
            'get_storageclasses': 'kubectl get storageclasses',
        }

        # Prepare context for the template
        context = {
            'overviews': all_overviews,
            'pods_data_json': json.dumps(all_pods_data),
            'events_data_json': json.dumps(all_events_data),
            'ingresses_data_json': ingresses_data_json,
            'config_maps_data_json': config_maps_data_json,
            'deployments_data_json': deployments_data_json,
            'daemon_sets_data_json': daemon_sets_data_json,
            'kube_commands': kube_commands,
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


@require_POST
def select_kubeconfig(request):
    """
    Handles the selection of a kubeconfig file by the user.
    """
    selected_kubeconfig = request.POST.get('kubeconfig')

    # Validate the selected kubeconfig file
    kubeconfig_files = [kubeconfig_file.name for kubeconfig_file in list_kubeconfigs()]
    if selected_kubeconfig not in kubeconfig_files:
        logger.error(f"Invalid kubeconfig selection attempted: {selected_kubeconfig}")
        return redirect('index_page')  # Optionally, add an error message

    # Update the session with the selected kubeconfig
    request.session['selected_kubeconfig'] = selected_kubeconfig
    logger.info(f"User selected kubeconfig: {selected_kubeconfig}")

    return redirect('index_page')