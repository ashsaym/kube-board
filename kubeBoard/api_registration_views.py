from django.http import JsonResponse
from kubernetes.client import ApiException
from appConfig.utils import get_cluster_client, KubernetesResourceView

class APIServiceView(KubernetesResourceView):
    """Views for handling APIService operations"""

    @staticmethod
    def list_api_service(request):
        """Implements ApiregistrationV1Api.list_api_service"""
        try:
            cluster, error = get_cluster_client(request)
            if error:
                return JsonResponse({'error': error}, status=400)

            api_services = cluster.apiregistration_v1_api.list_api_service()
            return JsonResponse({
                'items': [svc.to_dict() for svc in api_services.items]
            })
        except ApiException as e:
            return APIServiceView.handle_api_error(e, 'list_api_service')
        except Exception as e:
            return APIServiceView.handle_general_error(e, 'list_api_service')

    @staticmethod
    def read_api_service(request, name):
        """Implements ApiregistrationV1Api.read_api_service"""
        try:
            cluster, error = get_cluster_client(request)
            if error:
                return JsonResponse({'error': error}, status=400)

            api_service = cluster.apiregistration_v1_api.read_api_service(name=name)
            return JsonResponse(api_service.to_dict())
        except ApiException as e:
            return APIServiceView.handle_api_error(e, 'read_api_service')
        except Exception as e:
            return APIServiceView.handle_general_error(e, 'read_api_service')

    @staticmethod
    def read_api_service_status(request, name):
        """Implements ApiregistrationV1Api.read_api_service_status"""
        try:
            cluster, error = get_cluster_client(request)
            if error:
                return JsonResponse({'error': error}, status=400)

            status = cluster.apiregistration_v1_api.read_api_service_status(name=name)
            return JsonResponse(status.to_dict())
        except ApiException as e:
            return APIServiceView.handle_api_error(e, 'read_api_service_status')
        except Exception as e:
            return APIServiceView.handle_general_error(e, 'read_api_service_status')