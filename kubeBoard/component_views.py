from django.http import JsonResponse
from kubernetes.client import ApiException

from appConfig.utils import get_cluster_client, KubernetesResourceView

class ComponentStatusView(KubernetesResourceView):
    """Views for handling Kubernetes Component Status operations"""

    @staticmethod
    def list_component_status(request):
        """Implements CoreV1Api.list_component_status"""
        try:
            cluster, error = get_cluster_client(request)
            if error:
                return JsonResponse({'error': error}, status=400)

            components = cluster.core_v1_api.list_component_status()
            return JsonResponse({
                'items': [comp.to_dict() for comp in components.items]
            })
        except ApiException as e:
            return ComponentStatusView.handle_api_error(e, 'list_component_status')
        except Exception as e:
            return ComponentStatusView.handle_general_error(e, 'list_component_status')

    @staticmethod
    def read_component_status(request, name):
        """Implements CoreV1Api.read_component_status"""
        try:
            cluster, error = get_cluster_client(request)
            if error:
                return JsonResponse({'error': error}, status=400)

            component = cluster.core_v1_api.read_component_status(name=name)
            return JsonResponse(component.to_dict())
        except ApiException as e:
            return ComponentStatusView.handle_api_error(e, 'read_component_status')
        except Exception as e:
            return ComponentStatusView.handle_general_error(e, 'read_component_status')