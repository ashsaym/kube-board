import json
import base64

from django.http import HttpResponse
from django.shortcuts import render
from kubernetes.client import ApiException

from appConfig.kubeconfig import list_secrets, list_secrets_for_all_namespaces, read_namespaced_secret
from appConfig.settings import logger
from appConfig.utils import get_cluster_client


def all_secrets_page(request):
    """
    Displays all Secrets across all namespaces in the selected Kubernetes cluster.
    """
    cluster, error = get_cluster_client(request)
    if error:
        return HttpResponse(error, status=500)

    try:
        # Get all namespaces
        all_namespaces = cluster.core_v1.list_namespace().items

        # Get all Secrets across all namespaces
        secrets = list_secrets_for_all_namespaces(cluster)
        if not secrets:
            secrets = {"items": []}

        # Filter out service account tokens and other system secrets
        filtered_secrets = []
        for secret in secrets.items:
            # Skip service account tokens and other system secrets
            if secret.type not in ["kubernetes.io/service-account-token", "bootstrap.kubernetes.io/token"]:
                filtered_secrets.append(secret)

        kubectl_command = {
            'get': "kubectl get secrets --all-namespaces",
            'yaml': "kubectl get secrets --all-namespaces -o yaml",
            'describe': "kubectl describe secrets --all-namespaces",
            'create': "kubectl create secret generic <secret-name> --from-literal=key1=value1 --from-literal=key2=value2",
            'edit': "kubectl edit secret <secret-name> -n <namespace>",
            'delete': "kubectl delete secret <secret-name> -n <namespace>",
        }

        context = {
            'namespaces': all_namespaces,
            'secrets': filtered_secrets,
            'kubectl_command': kubectl_command,
        }

        return render(request, 'kubeSecrets/all-secrets.html', context)

    except ApiException as e:
        error_message = f"API Error: {e.reason or 'An unknown API error occurred.'}"
        logger.error(f"API Exception in all_secrets_page: {error_message}")
        return HttpResponse(error_message, status=e.status if e.status else 500)
    except Exception as e:
        error_message = f"Unexpected Error: {str(e)}"
        logger.error(f"Unexpected Exception in all_secrets_page: {error_message}")
        return HttpResponse(error_message, status=500)


def secret_details_page(request, namespace, secret_name):
    """
    Displays detailed information about a specific Secret.
    """
    cluster, error = get_cluster_client(request)
    if error:
        return HttpResponse(error, status=500)

    try:
        secret = read_namespaced_secret(cluster, secret_name, namespace)
        if not secret:
            return HttpResponse("Secret not found", status=404)

        # Decode secret data
        decoded_data = {}
        if secret.data:
            for key, value in secret.data.items():
                try:
                    decoded_value = base64.b64decode(value).decode('utf-8')
                    # Mask the value for security
                    masked_value = "●" * len(decoded_value)
                    decoded_data[key] = {
                        'value': masked_value,
                        'length': len(decoded_value)
                    }
                except Exception:
                    decoded_data[key] = {
                        'value': "Binary data (cannot display)",
                        'length': len(value)
                    }

        kubectl_commands = [
            {
                'command': f"kubectl get secret {secret_name} -n {namespace}",
                'explanation': "Lists details about the specified Secret."
            },
            {
                'command': f"kubectl get secret {secret_name} -n {namespace} -o yaml",
                'explanation': "Outputs the Secret's configuration in YAML format."
            },
            {
                'command': f"kubectl describe secret {secret_name} -n {namespace}",
                'explanation': "Provides detailed information about the Secret."
            },
            {
                'command': f"kubectl edit secret {secret_name} -n {namespace}",
                'explanation': "Edits the Secret's configuration."
            },
            {
                'command': f"kubectl delete secret {secret_name} -n {namespace}",
                'explanation': "Deletes the specified Secret."
            },
        ]

        context = {
            'secret': secret,
            'decoded_data': decoded_data,
            'selected_namespace': namespace,
            'secret_name': secret_name,
            'kubectl_commands': kubectl_commands,
        }

        return render(request, 'kubeSecrets/secret-details.html', context)

    except ApiException as e:
        if e.status == 404:
            return HttpResponse("Secret not found", status=404)
        else:
            error_message = f"An error occurred: {e.reason or 'Unknown error'}"
            logger.error(f"API Exception in secret_details_page: {error_message}")
            return HttpResponse(error_message, status=e.status if e.status else 500)
    except Exception as e:
        error_message = f"Unexpected Error: {str(e)}"
        logger.error(f"Unexpected Exception in secret_details_page: {error_message}")
        return HttpResponse(error_message, status=500)


def secret_json_page(request, namespace, secret_name):
    """
    Displays the JSON representation of a specific Secret.
    """
    cluster, error = get_cluster_client(request)
    if error:
        return HttpResponse(error, status=500)

    try:
        secret = read_namespaced_secret(cluster, secret_name, namespace)
        if not secret:
            return HttpResponse("Secret not found", status=404)

        # Mask the secret data for security
        if secret.data:
            masked_data = {}
            for key in secret.data.keys():
                masked_data[key] = "**REDACTED**"
            secret.data = masked_data

        api_client = cluster.core_v1.api_client
        serialized_secret = api_client.sanitize_for_serialization(secret)
        secret_json = json.dumps(serialized_secret, indent=4)

        context = {
            'secret_json': secret_json,
            'secret_name': secret_name,
            'namespace': namespace,
        }

        return render(request, 'kubeSecrets/secret-details-json.html', context)

    except ApiException as e:
        if e.status == 404:
            return HttpResponse("Secret not found", status=404)
        else:
            error_message = f"An error occurred: {e.reason or 'Unknown error'}"
            logger.error(f"API Exception in secret_json_page: {error_message}")
            return HttpResponse(error_message, status=e.status if e.status else 500)
    except Exception as e:
        error_message = f"Unexpected Error: {str(e)}"
        logger.error(f"Unexpected Exception in secret_json_page: {error_message}")
        return HttpResponse(error_message, status=500)