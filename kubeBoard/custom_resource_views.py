from django.http import JsonResponse
from kubernetes.client import ApiException

from appConfig.utils import get_cluster_client, KubernetesResourceView

class CustomResourceView(KubernetesResourceView):
    """Views for handling Custom Resources and Storage operations"""

    @staticmethod
    def get_cluster_custom_object(request, group, version, plural, name):
        """Implements CustomObjectsApi.get_cluster_custom_object"""
        try:
            cluster, error = get_cluster_client(request)
            if error:
                return JsonResponse({'error': error}, status=400)

            custom_object = cluster.custom_objects_api.get_cluster_custom_object(
                group=group,
                version=version,
                plural=plural,
                name=name
            )
            return JsonResponse(custom_object)
        except ApiException as e:
            return CustomResourceView.handle_api_error(e, 'get_cluster_custom_object')
        except Exception as e:
            return CustomResourceView.handle_general_error(e, 'get_cluster_custom_object')

    @staticmethod
    def get_cluster_custom_object_scale(request, group, version, plural, name):
        """Implements CustomObjectsApi.get_cluster_custom_object_scale"""
        try:
            cluster, error = get_cluster_client(request)
            if error:
                return JsonResponse({'error': error}, status=400)

            scale = cluster.custom_objects_api.get_cluster_custom_object_scale(
                group=group,
                version=version,
                plural=plural,
                name=name
            )
            return JsonResponse(scale)
        except ApiException as e:
            return CustomResourceView.handle_api_error(e, 'get_cluster_custom_object_scale')
        except Exception as e:
            return CustomResourceView.handle_general_error(e, 'get_cluster_custom_object_scale')

    @staticmethod
    def get_cluster_custom_object_status(request, group, version, plural, name):
        """Implements CustomObjectsApi.get_cluster_custom_object_status"""
        try:
            cluster, error = get_cluster_client(request)
            if error:
                return JsonResponse({'error': error}, status=400)

            status = cluster.custom_objects_api.get_cluster_custom_object_status(
                group=group,
                version=version,
                plural=plural,
                name=name
            )
            return JsonResponse(status)
        except ApiException as e:
            return CustomResourceView.handle_api_error(e, 'get_cluster_custom_object_status')
        except Exception as e:
            return CustomResourceView.handle_general_error(e, 'get_cluster_custom_object_status')

    @staticmethod
    def list_cluster_custom_object(request, group, version, plural):
        """Implements CustomObjectsApi.list_cluster_custom_object"""
        try:
            cluster, error = get_cluster_client(request)
            if error:
                return JsonResponse({'error': error}, status=400)

            custom_objects = cluster.custom_objects_api.list_cluster_custom_object(
                group=group,
                version=version,
                plural=plural
            )
            return JsonResponse(custom_objects)
        except ApiException as e:
            return CustomResourceView.handle_api_error(e, 'list_cluster_custom_object')
        except Exception as e:
            return CustomResourceView.handle_general_error(e, 'list_cluster_custom_object')

    @staticmethod
    def list_custom_object_for_all_namespaces(request, group, version, plural):
        """Implements CustomObjectsApi.list_custom_object_for_all_namespaces"""
        try:
            cluster, error = get_cluster_client(request)
            if error:
                return JsonResponse({'error': error}, status=400)

            custom_objects = cluster.custom_objects_api.list_custom_object_for_all_namespaces(
                group=group,
                version=version,
                plural=plural
            )
            return JsonResponse(custom_objects)
        except ApiException as e:
            return CustomResourceView.handle_api_error(e, 'list_custom_object_for_all_namespaces')
        except Exception as e:
            return CustomResourceView.handle_general_error(e, 'list_custom_object_for_all_namespaces')

    @staticmethod
    def list_custom_resource_definition(request):
        """Implements ApiextensionsV1Api.list_custom_resource_definition"""
        try:
            cluster, error = get_cluster_client(request)
            if error:
                return JsonResponse({'error': error}, status=400)

            crds = cluster.apiextensions_v1_api.list_custom_resource_definition()
            return JsonResponse({
                'items': [crd.to_dict() for crd in crds.items]
            })
        except ApiException as e:
            return CustomResourceView.handle_api_error(e, 'list_custom_resource_definition')
        except Exception as e:
            return CustomResourceView.handle_general_error(e, 'list_custom_resource_definition')

    @staticmethod
    def read_custom_resource_definition(request, name):
        """Implements ApiextensionsV1Api.read_custom_resource_definition"""
        try:
            cluster, error = get_cluster_client(request)
            if error:
                return JsonResponse({'error': error}, status=400)

            crd = cluster.apiextensions_v1_api.read_custom_resource_definition(name=name)
            return JsonResponse(crd.to_dict())
        except ApiException as e:
            return CustomResourceView.handle_api_error(e, 'read_custom_resource_definition')
        except Exception as e:
            return CustomResourceView.handle_general_error(e, 'read_custom_resource_definition')

    @staticmethod
    def read_custom_resource_definition_status(request, name):
        """Implements ApiextensionsV1Api.read_custom_resource_definition_status"""
        try:
            cluster, error = get_cluster_client(request)
            if error:
                return JsonResponse({'error': error}, status=400)

            status = cluster.apiextensions_v1_api.read_custom_resource_definition_status(name=name)
            return JsonResponse(status.to_dict())
        except ApiException as e:
            return CustomResourceView.handle_api_error(e, 'read_custom_resource_definition_status')
        except Exception as e:
            return CustomResourceView.handle_general_error(e, 'read_custom_resource_definition_status')