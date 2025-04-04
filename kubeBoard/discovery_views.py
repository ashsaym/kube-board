from django.http import JsonResponse
from kubernetes.client import ApiException
from appConfig.utils import get_cluster_client, KubernetesResourceView

class DiscoveryView(KubernetesResourceView):
    """Views for handling Discovery and Metrics operations"""

    @staticmethod
    def get_api_resources_discovery(request):
        """Implements DiscoveryV1Api.get_api_resources"""
        try:
            cluster, error = get_cluster_client(request)
            if error:
                return JsonResponse({'error': error}, status=400)

            resources = cluster.discovery_v1_api.get_api_resources()
            return JsonResponse(resources.to_dict())
        except ApiException as e:
            return DiscoveryView.handle_api_error(e, 'get_api_resources_discovery')
        except Exception as e:
            return DiscoveryView.handle_general_error(e, 'get_api_resources_discovery')

    @staticmethod
    def list_namespaced_endpoint_slice(request, namespace):
        """Implements DiscoveryV1Api.list_namespaced_endpoint_slice"""
        try:
            cluster, error = get_cluster_client(request)
            if error:
                return JsonResponse({'error': error}, status=400)

            slices = cluster.discovery_v1_api.list_namespaced_endpoint_slice(namespace=namespace)
            return JsonResponse({
                'items': [slice.to_dict() for slice in slices.items]
            })
        except ApiException as e:
            return DiscoveryView.handle_api_error(e, 'list_namespaced_endpoint_slice')
        except Exception as e:
            return DiscoveryView.handle_general_error(e, 'list_namespaced_endpoint_slice')

    @staticmethod
    def list_endpoint_slice_for_all_namespaces(request):
        """Implements DiscoveryV1Api.list_endpoint_slice_for_all_namespaces"""
        try:
            cluster, error = get_cluster_client(request)
            if error:
                return JsonResponse({'error': error}, status=400)

            slices = cluster.discovery_v1_api.list_endpoint_slice_for_all_namespaces()
            return JsonResponse({
                'items': [slice.to_dict() for slice in slices.items]
            })
        except ApiException as e:
            return DiscoveryView.handle_api_error(e, 'list_endpoint_slice_for_all_namespaces')
        except Exception as e:
            return DiscoveryView.handle_general_error(e, 'list_endpoint_slice_for_all_namespaces')

    @staticmethod
    def read_namespaced_endpoint_slice(request, name, namespace):
        """Implements DiscoveryV1Api.read_namespaced_endpoint_slice"""
        try:
            cluster, error = get_cluster_client(request)
            if error:
                return JsonResponse({'error': error}, status=400)

            slice = cluster.discovery_v1_api.read_namespaced_endpoint_slice(
                name=name,
                namespace=namespace
            )
            return JsonResponse(slice.to_dict())
        except ApiException as e:
            return DiscoveryView.handle_api_error(e, 'read_namespaced_endpoint_slice')
        except Exception as e:
            return DiscoveryView.handle_general_error(e, 'read_namespaced_endpoint_slice')