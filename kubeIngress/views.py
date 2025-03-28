import json
from datetime import datetime, timezone

from django.shortcuts import render
from kubernetes.client import ApiException

from appConfig.settings import logger
from appConfig.utils import get_cluster_client


def all_ingresses_page(request):
    """
    Renders a dedicated page displaying all Ingress resources in the selected Kubernetes cluster.
    """
    try:
        cluster, error = get_cluster_client(request)
        if error:
            return render(request, 'kubeIngress/all_ingresses.html', {'error': error})

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

        # Define dynamic kubectl commands
        kube_commands = {
            'cluster_info': 'kubectl cluster-info',
            'get_ingresses': 'kubectl get ingress --all-namespaces',
            'describe_ingress': 'kubectl describe ingress {name} -n {namespace}',
        }

        # Prepare context for the template
        context = {
            'ingresses_data_json': ingresses_data_json,
            'kube_commands': kube_commands,
        }

        return render(request, 'kubeIngress/all_ingresses.html', context)

    except ApiException as e:
        error_message = f"API Error: {e.reason or 'An unknown API error occurred.'}"
        logger.error(f"API Exception: {error_message}")
        return render(request, 'kubeIngress/all_ingresses.html', {'error': error_message})
    except Exception as e:
        error_message = f"Unexpected Error: {str(e)}"
        logger.error(f"Unexpected Exception: {error_message}")
        return render(request, 'kubeIngress/all_ingresses.html', {'error': error_message})


def ingress_detail(request, namespace, name):
    """
    Renders a detailed page for a specific Ingress resource.
    """
    try:
        cluster, error = get_cluster_client(request)
        if error:
            return render(request, 'kubeIngress/ingress_detail.html', {'error': error})

        # Retrieve the specific Ingress
        try:
            ingress = cluster.networking_v1.read_namespaced_ingress(name=name, namespace=namespace)
            logger.info(f"Retrieved ingress '{name}' in namespace '{namespace}'.")
        except ApiException as e:
            logger.error(f"Failed to retrieve ingress '{name}' in namespace '{namespace}': {e}")
            return render(request, 'kubeIngress/ingress_detail.html', {'error': f"Error fetching ingress: {e}"})
        # Prepare context for the template
        context = {
            'ingress': ingress,
            'kube_commands': {
                'describe_ingress': f"kubectl describe ingress {name} -n {namespace}",
                'delete_ingress': f"kubectl delete ingress {name} -n {namespace}",
            }
        }

        return render(request, 'kubeIngress/ingress_detail.html', context)

    except ApiException as e:
        error_message = f"API Error: {e.reason or 'An unknown API error occurred.'}"
        logger.error(f"API Exception: {error_message}")
        return render(request, 'kubeIngress/ingress_detail.html', {'error': error_message})
    except Exception as e:
        error_message = f"Unexpected Error: {str(e)}"
        logger.error(f"Unexpected Exception: {error_message}")
        return render(request, 'kubeIngress/ingress_detail.html', {'error': error_message})