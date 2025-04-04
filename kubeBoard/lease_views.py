from django.http import JsonResponse
from kubernetes.client import ApiException
from appConfig.utils import get_cluster_client, KubernetesResourceView

class LeaseView(KubernetesResourceView):
    """Views for handling Lease operations"""

    @staticmethod
    def get_api_resources_coordination(request):
        """Implements CoordinationV1Api.get_api_resources"""
        try:
            cluster, error = get_cluster_client(request)
            if error:
                return JsonResponse({'error': error}, status=400)

            resources = cluster.coordination_v1_api.get_api_resources()
            return JsonResponse(resources.to_dict())
        except ApiException as e:
            return LeaseView.handle_api_error(e, 'get_api_resources_coordination')
        except Exception as e:
            return LeaseView.handle_general_error(e, 'get_api_resources_coordination')

    @staticmethod
    def list_lease_for_all_namespaces(request):
        """Implements CoordinationV1Api.list_lease_for_all_namespaces"""
        try:
            cluster, error = get_cluster_client(request)
            if error:
                return JsonResponse({'error': error}, status=400)

            leases = cluster.coordination_v1_api.list_lease_for_all_namespaces()
            return JsonResponse({
                'items': [lease.to_dict() for lease in leases.items]
            })
        except ApiException as e:
            return LeaseView.handle_api_error(e, 'list_lease_for_all_namespaces')
        except Exception as e:
            return LeaseView.handle_general_error(e, 'list_lease_for_all_namespaces')

    @staticmethod
    def list_namespaced_lease(request, namespace):
        """Implements CoordinationV1Api.list_namespaced_lease"""
        try:
            cluster, error = get_cluster_client(request)
            if error:
                return JsonResponse({'error': error}, status=400)

            leases = cluster.coordination_v1_api.list_namespaced_lease(namespace=namespace)
            return JsonResponse({
                'items': [lease.to_dict() for lease in leases.items]
            })
        except ApiException as e:
            return LeaseView.handle_api_error(e, 'list_namespaced_lease')
        except Exception as e:
            return LeaseView.handle_general_error(e, 'list_namespaced_lease')

    @staticmethod
    def read_namespaced_lease(request, namespace, name):
        """Implements CoordinationV1Api.read_namespaced_lease"""
        try:
            cluster, error = get_cluster_client(request)
            if error:
                return JsonResponse({'error': error}, status=400)

            lease = cluster.coordination_v1_api.read_namespaced_lease(
                name=name, 
                namespace=namespace
            )
            return JsonResponse(lease.to_dict())
        except ApiException as e:
            return LeaseView.handle_api_error(e, 'read_namespaced_lease')
        except Exception as e:
            return LeaseView.handle_general_error(e, 'read_namespaced_lease')