import json
import subprocess
from datetime import datetime, timezone

from django.http import HttpResponse
from django.shortcuts import render
from kubernetes.client import ApiException

from appConfig.settings import logger
from appConfig.utils import get_cluster_client


def all_namespaces_page(request):
    """
    Displays all Namespaces in the selected Kubernetes cluster.
    """
    cluster, error = get_cluster_client(request)
    if error:
        return HttpResponse(error, status=500)

    try:
        # Get all Namespaces
        try:
            namespaces = cluster.core_v1.list_namespace()
        except ApiException as e:
            logger.error(f"Failed to retrieve Namespaces: {e}")
            namespaces = None

        # Process namespaces to add age and other useful information
        processed_namespaces = []
        if namespaces and namespaces.items:
            for namespace in namespaces.items:
                creation_time = namespace.metadata.creation_timestamp
                if creation_time:
                    age_timedelta = datetime.now(timezone.utc) - creation_time
                    age_hours = age_timedelta.total_seconds() / 3600
                    age_str = f"{int(age_hours)}h" if age_hours < 24 else f"{int(age_hours / 24)}d"
                else:
                    age_str = "N/A"

                # Get status
                status = namespace.status.phase or "Unknown"

                processed_namespaces.append({
                    'name': namespace.metadata.name,
                    'status': status,
                    'age': age_str,
                    'details_url': f"/namespaces/{namespace.metadata.name}/",
                })

        # Get services across all namespaces
        try:
            services = cluster.core_v1.list_service_for_all_namespaces()
        except ApiException as e:
            logger.error(f"Failed to retrieve Services: {e}")
            services = None

        # Process services
        processed_services = []
        if services and services.items:
            for service in services.items:
                creation_time = service.metadata.creation_timestamp
                if creation_time:
                    age_timedelta = datetime.now(timezone.utc) - creation_time
                    age_hours = age_timedelta.total_seconds() / 3600
                    age_str = f"{int(age_hours)}h" if age_hours < 24 else f"{int(age_hours / 24)}d"
                else:
                    age_str = "N/A"

                # Get type and cluster IP
                service_type = service.spec.type or "ClusterIP"
                cluster_ip = service.spec.cluster_ip or "None"

                # Get external IP if available
                external_ip = "None"
                if service.spec.type == "LoadBalancer" and service.status.load_balancer.ingress:
                    for ingress in service.status.load_balancer.ingress:
                        if ingress.ip:
                            external_ip = ingress.ip
                            break
                        elif ingress.hostname:
                            external_ip = ingress.hostname
                            break

                # Get ports
                ports = []
                if service.spec.ports:
                    for port in service.spec.ports:
                        port_str = f"{port.port}"
                        if port.target_port:
                            port_str += f":{port.target_port}"
                        if port.node_port:
                            port_str += f":{port.node_port}"
                        if port.protocol:
                            port_str += f"/{port.protocol}"
                        ports.append(port_str)

                processed_services.append({
                    'name': service.metadata.name,
                    'namespace': service.metadata.namespace,
                    'type': service_type,
                    'cluster_ip': cluster_ip,
                    'external_ip': external_ip,
                    'ports': ", ".join(ports),
                    'age': age_str,
                })

        kubectl_command = {
            'get': "kubectl get namespaces",
            'yaml': "kubectl get namespaces -o yaml",
            'describe': "kubectl describe namespaces",
            'create': "kubectl create namespace <namespace-name>",
            'delete': "kubectl delete namespace <namespace-name>",
            'get_services': "kubectl get services --all-namespaces",
            'get_services_short': "kubectl get svc -A",
        }

        context = {
            'namespaces': namespaces.items if namespaces else [],
            'processed_namespaces': processed_namespaces,
            'services': services.items if services else [],
            'processed_services': processed_services,
            'kubectl_command': kubectl_command,
        }

        return render(request, 'kubeNamespaces/all-namespaces.html', context)

    except ApiException as e:
        error_message = f"API Error: {e.reason or 'An unknown API error occurred.'}"
        logger.error(f"API Exception in all_namespaces_page: {error_message}")
        return HttpResponse(error_message, status=e.status if e.status else 500)
    except Exception as e:
        error_message = f"Unexpected Error: {str(e)}"
        logger.error(f"Unexpected Exception in all_namespaces_page: {error_message}")
        return HttpResponse(error_message, status=500)


def namespace_details_page(request, namespace_name):
    """
    Displays detailed information about a specific Namespace.
    """
    cluster, error = get_cluster_client(request)
    if error:
        return HttpResponse(error, status=500)

    try:
        namespace = cluster.core_v1.read_namespace(namespace_name)
        if not namespace:
            return HttpResponse("Namespace not found", status=404)

        # Get resource quotas for this namespace
        resource_quotas = []
        try:
            quota_list = cluster.core_v1.list_namespaced_resource_quota(namespace=namespace_name)
            resource_quotas = quota_list.items
        except ApiException as e:
            logger.error(f"Failed to list resource quotas for namespace '{namespace_name}': {e}")

        # Get limit ranges for this namespace
        limit_ranges = []
        try:
            limit_range_list = cluster.core_v1.list_namespaced_limit_range(namespace=namespace_name)
            limit_ranges = limit_range_list.items
        except ApiException as e:
            logger.error(f"Failed to list limit ranges for namespace '{namespace_name}': {e}")

        # Get network policies for this namespace
        network_policies = []
        try:
            network_policy_list = cluster.networking_v1.list_namespaced_network_policy(namespace=namespace_name)
            network_policies = network_policy_list.items
        except ApiException as e:
            logger.error(f"Failed to list network policies for namespace '{namespace_name}': {e}")

        # Get services in this namespace
        services = []
        try:
            service_list = cluster.core_v1.list_namespaced_service(namespace=namespace_name)
            services = service_list.items
        except ApiException as e:
            logger.error(f"Failed to list services for namespace '{namespace_name}': {e}")

        # Format services
        formatted_services = []
        for service in services:
            creation_time = service.metadata.creation_timestamp
            if creation_time:
                age_timedelta = datetime.now(timezone.utc) - creation_time
                age_hours = age_timedelta.total_seconds() / 3600
                age_str = f"{int(age_hours)}h" if age_hours < 24 else f"{int(age_hours / 24)}d"
            else:
                age_str = "N/A"

            # Get type and cluster IP
            service_type = service.spec.type or "ClusterIP"
            cluster_ip = service.spec.cluster_ip or "None"

            # Get external IP if available
            external_ip = "None"
            if service.spec.type == "LoadBalancer" and service.status.load_balancer.ingress:
                for ingress in service.status.load_balancer.ingress:
                    if ingress.ip:
                        external_ip = ingress.ip
                        break
                    elif ingress.hostname:
                        external_ip = ingress.hostname
                        break

            # Get ports
            ports = []
            if service.spec.ports:
                for port in service.spec.ports:
                    port_str = f"{port.port}"
                    if port.target_port:
                        port_str += f":{port.target_port}"
                    if port.node_port:
                        port_str += f":{port.node_port}"
                    if port.protocol:
                        port_str += f"/{port.protocol}"
                    ports.append(port_str)

            formatted_services.append({
                'name': service.metadata.name,
                'type': service_type,
                'cluster_ip': cluster_ip,
                'external_ip': external_ip,
                'ports': ", ".join(ports),
                'age': age_str,
            })

        # Get events related to this namespace
        events = []
        try:
            event_list = cluster.core_v1.list_namespaced_event(
                namespace=namespace_name,
                field_selector=f"involvedObject.name={namespace_name},involvedObject.kind=Namespace"
            )
            events = event_list.items
        except ApiException as e:
            logger.error(f"Failed to list events for namespace '{namespace_name}': {e}")

        # Format events
        formatted_events = []
        for event in events:
            first_seen = event.first_timestamp.replace(tzinfo=timezone.utc).astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S") if event.first_timestamp else ''
            last_seen = event.last_timestamp.replace(tzinfo=timezone.utc).astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S") if event.last_timestamp else ''
            formatted_events.append({
                'type': event.type,
                'reason': event.reason,
                'message': event.message,
                'first_seen': first_seen,
                'last_seen': last_seen,
            })

        kubectl_commands = [
            {
                'command': f"kubectl get namespace {namespace_name}",
                'explanation': "Lists details about the specified Namespace."
            },
            {
                'command': f"kubectl get namespace {namespace_name} -o yaml",
                'explanation': "Outputs the Namespace's configuration in YAML format."
            },
            {
                'command': f"kubectl describe namespace {namespace_name}",
                'explanation': "Provides detailed information about the Namespace."
            },
            {
                'command': f"kubectl get all -n {namespace_name}",
                'explanation': "Lists all resources in the Namespace."
            },
            {
                'command': f"kubectl get services -n {namespace_name}",
                'explanation': "Lists all services in the Namespace."
            },
            {
                'command': f"kubectl get pods -n {namespace_name}",
                'explanation': "Lists all pods in the Namespace."
            },
            {
                'command': f"kubectl get deployments -n {namespace_name}",
                'explanation': "Lists all deployments in the Namespace."
            },
            {
                'command': f"kubectl delete namespace {namespace_name}",
                'explanation': "Deletes the specified Namespace and all resources in it."
            },
        ]

        context = {
            'namespace': namespace,
            'resource_quotas': resource_quotas,
            'limit_ranges': limit_ranges,
            'network_policies': network_policies,
            'services': formatted_services,
            'events': formatted_events,
            'namespace_name': namespace_name,
            'kubectl_commands': kubectl_commands,
        }

        return render(request, 'kubeNamespaces/namespace-details.html', context)

    except ApiException as e:
        if e.status == 404:
            return HttpResponse("Namespace not found", status=404)
        else:
            error_message = f"An error occurred: {e.reason or 'Unknown error'}"
            logger.error(f"API Exception in namespace_details_page: {error_message}")
            return HttpResponse(error_message, status=e.status if e.status else 500)
    except Exception as e:
        error_message = f"Unexpected Error: {str(e)}"
        logger.error(f"Unexpected Exception in namespace_details_page: {error_message}")
        return HttpResponse(error_message, status=500)


def namespace_json_page(request, namespace_name):
    """
    Displays the JSON representation of a specific Namespace.
    """
    cluster, error = get_cluster_client(request)
    if error:
        return HttpResponse(error, status=500)

    try:
        namespace = cluster.core_v1.read_namespace(namespace_name)
        if not namespace:
            return HttpResponse("Namespace not found", status=404)

        api_client = cluster.core_v1.api_client
        serialized_namespace = api_client.sanitize_for_serialization(namespace)
        namespace_json = json.dumps(serialized_namespace, indent=4)

        context = {
            'namespace_json': namespace_json,
            'namespace_name': namespace_name,
        }

        return render(request, 'kubeNamespaces/namespace-details-json.html', context)

    except ApiException as e:
        if e.status == 404:
            return HttpResponse("Namespace not found", status=404)
        else:
            error_message = f"An error occurred: {e.reason or 'Unknown error'}"
            logger.error(f"API Exception in namespace_json_page: {error_message}")
            return HttpResponse(error_message, status=e.status if e.status else 500)
    except Exception as e:
        error_message = f"Unexpected Error: {str(e)}"
        logger.error(f"Unexpected Exception in namespace_json_page: {error_message}")
        return HttpResponse(error_message, status=500)