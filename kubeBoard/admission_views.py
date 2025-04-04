from django.http import JsonResponse
from kubernetes.client import ApiException
from appConfig.utils import get_cluster_client, KubernetesResourceView

class AdmissionRegistrationView(KubernetesResourceView):
    """Views for handling Admission Registration operations"""

    @staticmethod
    def get_api_resources_admissionregistration_v1(request):
        """Implements AdmissionregistrationV1Api.get_api_resources"""
        try:
            cluster, error = get_cluster_client(request)
            if error:
                return JsonResponse({'error': error}, status=400)

            resources = cluster.admissionregistration_v1_api.get_api_resources()
            return JsonResponse(resources.to_dict())
        except ApiException as e:
            return AdmissionRegistrationView.handle_api_error(e, 'get_api_resources_admissionregistration_v1')
        except Exception as e:
            return AdmissionRegistrationView.handle_general_error(e, 'get_api_resources_admissionregistration_v1')

    @staticmethod
    def list_mutating_webhook_configuration(request):
        """Implements AdmissionregistrationV1Api.list_mutating_webhook_configuration"""
        try:
            cluster, error = get_cluster_client(request)
            if error:
                return JsonResponse({'error': error}, status=400)

            webhooks = cluster.admissionregistration_v1_api.list_mutating_webhook_configuration()
            return JsonResponse({
                'items': [webhook.to_dict() for webhook in webhooks.items]
            })
        except ApiException as e:
            return AdmissionRegistrationView.handle_api_error(e, 'list_mutating_webhook_configuration')
        except Exception as e:
            return AdmissionRegistrationView.handle_general_error(e, 'list_mutating_webhook_configuration')

    @staticmethod
    def list_validating_webhook_configuration(request):
        """Implements AdmissionregistrationV1Api.list_validating_webhook_configuration"""
        try:
            cluster, error = get_cluster_client(request)
            if error:
                return JsonResponse({'error': error}, status=400)

            webhooks = cluster.admissionregistration_v1_api.list_validating_webhook_configuration()
            return JsonResponse({
                'items': [webhook.to_dict() for webhook in webhooks.items]
            })
        except ApiException as e:
            return AdmissionRegistrationView.handle_api_error(e, 'list_validating_webhook_configuration')
        except Exception as e:
            return AdmissionRegistrationView.handle_general_error(e, 'list_validating_webhook_configuration')

    @staticmethod
    def read_mutating_webhook_configuration(request, name):
        """Implements AdmissionregistrationV1Api.read_mutating_webhook_configuration"""
        try:
            cluster, error = get_cluster_client(request)
            if error:
                return JsonResponse({'error': error}, status=400)

            webhook = cluster.admissionregistration_v1_api.read_mutating_webhook_configuration(name=name)
            return JsonResponse(webhook.to_dict())
        except ApiException as e:
            return AdmissionRegistrationView.handle_api_error(e, 'read_mutating_webhook_configuration')
        except Exception as e:
            return AdmissionRegistrationView.handle_general_error(e, 'read_mutating_webhook_configuration')

    @staticmethod
    def read_validating_webhook_configuration(request, name):
        """Implements AdmissionregistrationV1Api.read_validating_webhook_configuration"""
        try:
            cluster, error = get_cluster_client(request)
            if error:
                return JsonResponse({'error': error}, status=400)

            webhook = cluster.admissionregistration_v1_api.read_validating_webhook_configuration(name=name)
            return JsonResponse(webhook.to_dict())
        except ApiException as e:
            return AdmissionRegistrationView.handle_api_error(e, 'read_validating_webhook_configuration')
        except Exception as e:
            return AdmissionRegistrationView.handle_general_error(e, 'read_validating_webhook_configuration')

    @staticmethod
    def list_validating_admission_policy(request):
        """Implements AdmissionregistrationV1Api.list_validating_admission_policy"""
        try:
            cluster, error = get_cluster_client(request)
            if error:
                return JsonResponse({'error': error}, status=400)

            policies = cluster.admissionregistration_v1_api.list_validating_admission_policy()
            return JsonResponse({
                'items': [policy.to_dict() for policy in policies.items]
            })
        except ApiException as e:
            return AdmissionRegistrationView.handle_api_error(e, 'list_validating_admission_policy')
        except Exception as e:
            return AdmissionRegistrationView.handle_general_error(e, 'list_validating_admission_policy')

    @staticmethod
    def list_validating_admission_policy_binding(request):
        """Implements AdmissionregistrationV1Api.list_validating_admission_policy_binding"""
        try:
            cluster, error = get_cluster_client(request)
            if error:
                return JsonResponse({'error': error}, status=400)

            bindings = cluster.admissionregistration_v1_api.list_validating_admission_policy_binding()
            return JsonResponse({
                'items': [binding.to_dict() for binding in bindings.items]
            })
        except ApiException as e:
            return AdmissionRegistrationView.handle_api_error(e, 'list_validating_admission_policy_binding')
        except Exception as e:
            return AdmissionRegistrationView.handle_general_error(e, 'list_validating_admission_policy_binding')

    @staticmethod
    def read_validating_admission_policy(request, name):
        """Implements AdmissionregistrationV1Api.read_validating_admission_policy"""
        try:
            cluster, error = get_cluster_client(request)
            if error:
                return JsonResponse({'error': error}, status=400)

            policy = cluster.admissionregistration_v1_api.read_validating_admission_policy(name=name)
            return JsonResponse(policy.to_dict())
        except ApiException as e:
            return AdmissionRegistrationView.handle_api_error(e, 'read_validating_admission_policy')
        except Exception as e:
            return AdmissionRegistrationView.handle_general_error(e, 'read_validating_admission_policy')

    @staticmethod
    def read_validating_admission_policy_binding(request, name):
        """Implements AdmissionregistrationV1Api.read_validating_admission_policy_binding"""
        try:
            cluster, error = get_cluster_client(request)
            if error:
                return JsonResponse({'error': error}, status=400)

            binding = cluster.admissionregistration_v1_api.read_validating_admission_policy_binding(name=name)
            return JsonResponse(binding.to_dict())
        except ApiException as e:
            return AdmissionRegistrationView.handle_api_error(e, 'read_validating_admission_policy_binding')
        except Exception as e:
            return AdmissionRegistrationView.handle_general_error(e, 'read_validating_admission_policy_binding')

    @staticmethod
    def read_validating_admission_policy_status(request, name):
        """Implements AdmissionregistrationV1Api.read_validating_admission_policy_status"""
        try:
            cluster, error = get_cluster_client(request)
            if error:
                return JsonResponse({'error': error}, status=400)

            status = cluster.admissionregistration_v1_api.read_validating_admission_policy_status(name=name)
            return JsonResponse(status.to_dict())
        except ApiException as e:
            return AdmissionRegistrationView.handle_api_error(e, 'read_validating_admission_policy_status')
        except Exception as e:
            return AdmissionRegistrationView.handle_general_error(e, 'read_validating_admission_policy_status')