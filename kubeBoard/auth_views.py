from django.http import JsonResponse
from kubernetes.client import ApiException
from appConfig.utils import get_cluster_client, KubernetesResourceView

class AuthenticationView(KubernetesResourceView):
    """Views for handling Authentication, Authorization, and RBAC operations"""

    @staticmethod
    def get_api_resources_authentication(request):
        """Implements AuthenticationV1Api.get_api_resources"""
        try:
            cluster, error = get_cluster_client(request)
            if error:
                return JsonResponse({'error': error}, status=400)

            resources = cluster.authentication_v1_api.get_api_resources()
            return JsonResponse(resources.to_dict())
        except ApiException as e:
            return AuthenticationView.handle_api_error(e, 'get_api_resources_authentication')
        except Exception as e:
            return AuthenticationView.handle_general_error(e, 'get_api_resources_authentication')

    @staticmethod
    def get_api_resources_authorization(request):
        """Implements AuthorizationV1Api.get_api_resources"""
        try:
            cluster, error = get_cluster_client(request)
            if error:
                return JsonResponse({'error': error}, status=400)

            resources = cluster.authorization_v1_api.get_api_resources()
            return JsonResponse(resources.to_dict())
        except ApiException as e:
            return AuthenticationView.handle_api_error(e, 'get_api_resources_authorization')
        except Exception as e:
            return AuthenticationView.handle_general_error(e, 'get_api_resources_authorization')

    @staticmethod
    def get_api_resources_authorization_v1beta1(request):
        """Implements AuthorizationV1beta1Api.get_api_resources"""
        try:
            cluster, error = get_cluster_client(request)
            if error:
                return JsonResponse({'error': error}, status=400)

            resources = cluster.authorization_v1beta1_api.get_api_resources()
            return JsonResponse(resources.to_dict())
        except ApiException as e:
            return AuthenticationView.handle_api_error(e, 'get_api_resources_authorization_v1beta1')
        except Exception as e:
            return AuthenticationView.handle_general_error(e, 'get_api_resources_authorization_v1beta1')

    @staticmethod
    def get_api_resources_rbac(request):
        """Implements RbacAuthorizationV1Api.get_api_resources"""
        try:
            cluster, error = get_cluster_client(request)
            if error:
                return JsonResponse({'error': error}, status=400)

            resources = cluster.rbac_authorization_v1_api.get_api_resources()
            return JsonResponse(resources.to_dict())
        except ApiException as e:
            return AuthenticationView.handle_api_error(e, 'get_api_resources_rbac')
        except Exception as e:
            return AuthenticationView.handle_general_error(e, 'get_api_resources_rbac')

    @staticmethod
    def list_cluster_role(request):
        """Implements RbacAuthorizationV1Api.list_cluster_role"""
        try:
            cluster, error = get_cluster_client(request)
            if error:
                return JsonResponse({'error': error}, status=400)

            roles = cluster.rbac_authorization_v1_api.list_cluster_role()
            return JsonResponse({
                'items': [role.to_dict() for role in roles.items]
            })
        except ApiException as e:
            return AuthenticationView.handle_api_error(e, 'list_cluster_role')
        except Exception as e:
            return AuthenticationView.handle_general_error(e, 'list_cluster_role')

    @staticmethod
    def list_cluster_role_binding(request):
        """Implements RbacAuthorizationV1Api.list_cluster_role_binding"""
        try:
            cluster, error = get_cluster_client(request)
            if error:
                return JsonResponse({'error': error}, status=400)

            bindings = cluster.rbac_authorization_v1_api.list_cluster_role_binding()
            return JsonResponse({
                'items': [binding.to_dict() for binding in bindings.items]
            })
        except ApiException as e:
            return AuthenticationView.handle_api_error(e, 'list_cluster_role_binding')
        except Exception as e:
            return AuthenticationView.handle_general_error(e, 'list_cluster_role_binding')

    @staticmethod
    def read_cluster_role(request, name):
        """Implements RbacAuthorizationV1Api.read_cluster_role"""
        try:
            cluster, error = get_cluster_client(request)
            if error:
                return JsonResponse({'error': error}, status=400)

            role = cluster.rbac_authorization_v1_api.read_cluster_role(name=name)
            return JsonResponse(role.to_dict())
        except ApiException as e:
            return AuthenticationView.handle_api_error(e, 'read_cluster_role')
        except Exception as e:
            return AuthenticationView.handle_general_error(e, 'read_cluster_role')

    @staticmethod
    def read_cluster_role_binding(request, name):
        """Implements RbacAuthorizationV1Api.read_cluster_role_binding"""
        try:
            cluster, error = get_cluster_client(request)
            if error:
                return JsonResponse({'error': error}, status=400)

            binding = cluster.rbac_authorization_v1_api.read_cluster_role_binding(name=name)
            return JsonResponse(binding.to_dict())
        except ApiException as e:
            return AuthenticationView.handle_api_error(e, 'read_cluster_role_binding')
        except Exception as e:
            return AuthenticationView.handle_general_error(e, 'read_cluster_role_binding')