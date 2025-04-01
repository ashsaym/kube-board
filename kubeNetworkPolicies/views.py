import json
from datetime import datetime, timezone

from django.http import HttpResponse
from django.shortcuts import render
from kubernetes.client import ApiException

from appConfig.kubeconfig import list_network_policies, list_network_policies_for_all_namespaces
from appConfig.settings import logger
from appConfig.utils import get_cluster_client


def all_network_policies_page(request):
    """
    Displays all NetworkPolicies across all namespaces in the selected Kubernetes cluster.
    """
    cluster, error = get_cluster_client(request)
    if error:
        return HttpResponse(error, status=500)

    try:
        # Get all namespaces
        all_namespaces = cluster.core_v1.list_namespace().items

        # Get all NetworkPolicies across all namespaces
        try:
            network_policies = cluster.networking_v1.list_network_policy_for_all_namespaces()
        except ApiException as e:
            logger.error(f"Failed to retrieve NetworkPolicies: {e}")
            network_policies = None

        # Process network_policies to add age and other useful information
        processed_network_policies = []
        if network_policies and network_policies.items:
            for network_policy in network_policies.items:
                creation_time = network_policy.metadata.creation_timestamp
                if creation_time:
                    age_timedelta = datetime.now(timezone.utc) - creation_time
                    age_hours = age_timedelta.total_seconds() / 3600
                    age_str = f"{int(age_hours)}h" if age_hours < 24 else f"{int(age_hours / 24)}d"
                else:
                    age_str = "N/A"

                # Get policy types
                policy_types = network_policy.spec.policy_types or []
                policy_types_str = ", ".join(policy_types)

                # Get pod selector
                pod_selector = "All pods"
                if network_policy.spec.pod_selector and network_policy.spec.pod_selector.match_labels:
                    selector_parts = []
                    for key, value in network_policy.spec.pod_selector.match_labels.items():
                        selector_parts.append(f"{key}={value}")
                    pod_selector = ", ".join(selector_parts)

                processed_network_policies.append({
                    'name': network_policy.metadata.name,
                    'namespace': network_policy.metadata.namespace,
                    'policy_types': policy_types_str,
                    'pod_selector': pod_selector,
                    'age': age_str,
                    'details_url': f"/networkpolicies/{network_policy.metadata.namespace}/{network_policy.metadata.name}/",
                })

        kubectl_command = {
            'get': "kubectl get networkpolicies --all-namespaces",
            'yaml': "kubectl get networkpolicies --all-namespaces -o yaml",
            'describe': "kubectl describe networkpolicies --all-namespaces",
            'create': "kubectl create -f networkpolicy.yaml",
            'delete': "kubectl delete networkpolicy <networkpolicy-name> -n <namespace>",
        }

        context = {
            'namespaces': all_namespaces,
            'network_policies': network_policies.items if network_policies else [],
            'processed_network_policies': processed_network_policies,
            'kubectl_command': kubectl_command,
        }

        return render(request, 'kubeNetworkPolicies/all-networkpolicies.html', context)

    except ApiException as e:
        error_message = f"API Error: {e.reason or 'An unknown API error occurred.'}"
        logger.error(f"API Exception in all_network_policies_page: {error_message}")
        return HttpResponse(error_message, status=e.status if e.status else 500)
    except Exception as e:
        error_message = f"Unexpected Error: {str(e)}"
        logger.error(f"Unexpected Exception in all_network_policies_page: {error_message}")
        return HttpResponse(error_message, status=500)


def network_policy_details_page(request, namespace, network_policy_name):
    """
    Displays detailed information about a specific NetworkPolicy.
    """
    cluster, error = get_cluster_client(request)
    if error:
        return HttpResponse(error, status=500)

    try:
        network_policy = cluster.networking_v1.read_namespaced_network_policy(network_policy_name, namespace)
        if not network_policy:
            return HttpResponse("NetworkPolicy not found", status=404)

        # Format ingress rules
        ingress_rules = []
        if network_policy.spec.ingress:
            for rule in network_policy.spec.ingress:
                formatted_rule = {
                    'from': [],
                    'ports': []
                }
                
                # Process 'from' field
                # Handle the 'from_' attribute safely
                from_items = getattr(rule, 'from_', None)
                if from_items:
                    for from_item in from_items:
                        if from_item.ip_block:
                            cidr = from_item.ip_block.cidr
                            except_cidrs = getattr(from_item.ip_block, 'except_', []) or []
                            formatted_rule['from'].append({
                                'type': 'IPBlock',
                                'value': f"CIDR: {cidr}, Except: {', '.join(except_cidrs) if except_cidrs else 'None'}"
                            })
                        elif from_item.namespace_selector:
                            if from_item.namespace_selector.match_labels:
                                selector_parts = []
                                for key, value in from_item.namespace_selector.match_labels.items():
                                    selector_parts.append(f"{key}={value}")
                                formatted_rule['from'].append({
                                    'type': 'NamespaceSelector',
                                    'value': ", ".join(selector_parts)
                                })
                            else:
                                formatted_rule['from'].append({
                                    'type': 'NamespaceSelector',
                                    'value': "All namespaces"
                                })
                        elif from_item.pod_selector:
                            if from_item.pod_selector.match_labels:
                                selector_parts = []
                                for key, value in from_item.pod_selector.match_labels.items():
                                    selector_parts.append(f"{key}={value}")
                                formatted_rule['from'].append({
                                    'type': 'PodSelector',
                                    'value': ", ".join(selector_parts)
                                })
                            else:
                                formatted_rule['from'].append({
                                    'type': 'PodSelector',
                                    'value': "All pods"
                                })
                
                # Process 'ports' field
                if rule.ports:
                    for port in rule.ports:
                        port_str = f"{port.port} ({port.protocol})" if port.protocol else f"{port.port}"
                        formatted_rule['ports'].append(port_str)
                
                ingress_rules.append(formatted_rule)

        # Format egress rules
        egress_rules = []
        if network_policy.spec.egress:
            for rule in network_policy.spec.egress:
                formatted_rule = {
                    'to': [],
                    'ports': []
                }
                
                # Process 'to' field
                if rule.to:
                    for to_item in rule.to:
                        if to_item.ip_block:
                            cidr = to_item.ip_block.cidr
                            except_cidrs = to_item.ip_block.except_ or []
                            formatted_rule['to'].append({
                                'type': 'IPBlock',
                                'value': f"CIDR: {cidr}, Except: {', '.join(except_cidrs) if except_cidrs else 'None'}"
                            })
                        elif to_item.namespace_selector:
                            if to_item.namespace_selector.match_labels:
                                selector_parts = []
                                for key, value in to_item.namespace_selector.match_labels.items():
                                    selector_parts.append(f"{key}={value}")
                                formatted_rule['to'].append({
                                    'type': 'NamespaceSelector',
                                    'value': ", ".join(selector_parts)
                                })
                            else:
                                formatted_rule['to'].append({
                                    'type': 'NamespaceSelector',
                                    'value': "All namespaces"
                                })
                        elif to_item.pod_selector:
                            if to_item.pod_selector.match_labels:
                                selector_parts = []
                                for key, value in to_item.pod_selector.match_labels.items():
                                    selector_parts.append(f"{key}={value}")
                                formatted_rule['to'].append({
                                    'type': 'PodSelector',
                                    'value': ", ".join(selector_parts)
                                })
                            else:
                                formatted_rule['to'].append({
                                    'type': 'PodSelector',
                                    'value': "All pods"
                                })
                
                # Process 'ports' field
                if rule.ports:
                    for port in rule.ports:
                        port_str = f"{port.port} ({port.protocol})" if port.protocol else f"{port.port}"
                        formatted_rule['ports'].append(port_str)
                
                egress_rules.append(formatted_rule)

        kubectl_commands = [
            {
                'command': f"kubectl get networkpolicy {network_policy_name} -n {namespace}",
                'explanation': "Lists details about the specified NetworkPolicy."
            },
            {
                'command': f"kubectl get networkpolicy {network_policy_name} -n {namespace} -o yaml",
                'explanation': "Outputs the NetworkPolicy's configuration in YAML format."
            },
            {
                'command': f"kubectl describe networkpolicy {network_policy_name} -n {namespace}",
                'explanation': "Provides detailed information about the NetworkPolicy."
            },
            {
                'command': f"kubectl delete networkpolicy {network_policy_name} -n {namespace}",
                'explanation': "Deletes the specified NetworkPolicy."
            },
        ]

        context = {
            'network_policy': network_policy,
            'ingress_rules': ingress_rules,
            'egress_rules': egress_rules,
            'selected_namespace': namespace,
            'network_policy_name': network_policy_name,
            'kubectl_commands': kubectl_commands,
        }

        return render(request, 'kubeNetworkPolicies/networkpolicy-details.html', context)

    except ApiException as e:
        if e.status == 404:
            return HttpResponse("NetworkPolicy not found", status=404)
        else:
            error_message = f"An error occurred: {e.reason or 'Unknown error'}"
            logger.error(f"API Exception in network_policy_details_page: {error_message}")
            return HttpResponse(error_message, status=e.status if e.status else 500)
    except Exception as e:
        error_message = f"Unexpected Error: {str(e)}"
        logger.error(f"Unexpected Exception in network_policy_details_page: {error_message}")
        return HttpResponse(error_message, status=500)


def network_policy_json_page(request, namespace, network_policy_name):
    """
    Displays the JSON representation of a specific NetworkPolicy.
    """
    cluster, error = get_cluster_client(request)
    if error:
        return HttpResponse(error, status=500)

    try:
        network_policy = cluster.networking_v1.read_namespaced_network_policy(network_policy_name, namespace)
        if not network_policy:
            return HttpResponse("NetworkPolicy not found", status=404)

        api_client = cluster.networking_v1.api_client
        serialized_network_policy = api_client.sanitize_for_serialization(network_policy)
        network_policy_json = json.dumps(serialized_network_policy, indent=4)

        context = {
            'network_policy_json': network_policy_json,
            'network_policy_name': network_policy_name,
            'namespace': namespace,
        }

        return render(request, 'kubeNetworkPolicies/networkpolicy-details-json.html', context)

    except ApiException as e:
        if e.status == 404:
            return HttpResponse("NetworkPolicy not found", status=404)
        else:
            error_message = f"An error occurred: {e.reason or 'Unknown error'}"
            logger.error(f"API Exception in network_policy_json_page: {error_message}")
            return HttpResponse(error_message, status=e.status if e.status else 500)
    except Exception as e:
        error_message = f"Unexpected Error: {str(e)}"
        logger.error(f"Unexpected Exception in network_policy_json_page: {error_message}")
        return HttpResponse(error_message, status=500)