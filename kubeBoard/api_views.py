import json
from django.http import HttpResponse, JsonResponse, FileResponse
from kubernetes.client import ApiException

from appConfig.utils import get_cluster_client, KubernetesResourceView
from kubeLogs.utils import LogHandler

class KubernetesApiView(KubernetesResourceView):
    """Views for handling Kubernetes API operations"""

    @staticmethod
    def get_api_versions(request):
        """Implements CoreApi.get_api_versions"""
        try:
            cluster, error = get_cluster_client(request)
            if error:
                return JsonResponse({'error': error}, status=400)

            api_versions = cluster.core_api.get_api_versions()
            return JsonResponse(api_versions.to_dict())
        except ApiException as e:
            return KubernetesApiView.handle_api_error(e, 'get_api_versions')
        except Exception as e:
            return KubernetesApiView.handle_general_error(e, 'get_api_versions')

    @staticmethod
    def get_api_group(request, group):
        """Gets API group information"""
        try:
            cluster, error = get_cluster_client(request)
            if error:
                return JsonResponse({'error': error}, status=400)

            # Map group names to API instances
            group_apis = {
                'admissionregistration': cluster.admissionregistration_api,
                'apiextensions': cluster.apiextensions_api,
                'apiregistration': cluster.apiregistration_api,
                'apps': cluster.apps_api,
                'authentication': cluster.authentication_api,
                'authorization': cluster.authorization_api,
                'autoscaling': cluster.autoscaling_api,
                'batch': cluster.batch_api,
                'certificates': cluster.certificates_api,
                'coordination': cluster.coordination_api,
                'core': cluster.core_api,
                'discovery': cluster.discovery_api,
                'events': cluster.events_api,
                'flowcontrol': cluster.flowcontrol_apiserver_api,
                'internal': cluster.internal_apiserver_api,
                'networking': cluster.networking_api,
                'node': cluster.node_api,
                'policy': cluster.policy_api,
                'rbac': cluster.rbac_authorization_api,
                'resource': cluster.resource_api,
                'storage': cluster.storage_api,
            }

            if group not in group_apis:
                return JsonResponse({'error': f'Invalid API group: {group}'}, status=400)

            api_group = group_apis[group].get_api_group()
            return JsonResponse(api_group.to_dict())
        except ApiException as e:
            return KubernetesApiView.handle_api_error(e, 'get_api_group')
        except Exception as e:
            return KubernetesApiView.handle_general_error(e, 'get_api_group')

    @staticmethod 
    def get_api_resources(request, group, version):
        """Gets API resources for a specific API group and version"""
        try:
            cluster, error = get_cluster_client(request)
            if error:
                return JsonResponse({'error': error}, status=400)

            # Map version strings to API instances
            version_apis = {
                'v1': cluster.core_v1_api,
                'admissionregistration/v1': cluster.admissionregistration_v1_api,
                'admissionregistration/v1beta1': cluster.admissionregistration_v1beta1_api,
                'apps/v1': cluster.apps_v1_api,
                'autoscaling/v1': cluster.autoscaling_v1_api,
                'autoscaling/v2': cluster.autoscaling_v2_api,
                'batch/v1': cluster.batch_v1_api,
                'certificates/v1': cluster.certificates_v1_api,
                'certificates/v1alpha1': cluster.certificates_v1alpha1_api,
                'coordination/v1': cluster.coordination_v1_api,
                'events/v1': cluster.events_v1_api,
                'networking/v1': cluster.networking_v1_api,
                'node/v1': cluster.node_v1_api,
                'policy/v1': cluster.policy_v1_api,
                'rbac/v1': cluster.rbac_authorization_v1_api,
                'storage/v1': cluster.storage_v1_api,
            }

            version_key = f"{group}/{version}" if group else version
            if version_key not in version_apis:
                return JsonResponse({'error': f'Invalid API version: {version_key}'}, status=400)

            resources = version_apis[version_key].get_api_resources()
            return JsonResponse(resources.to_dict())
        except ApiException as e:
            return KubernetesApiView.handle_api_error(e, 'get_api_resources')
        except Exception as e:
            return KubernetesApiView.handle_general_error(e, 'get_api_resources')

    @staticmethod
    def get_service_account_issuer_openid_configuration(request):
        """Implements WellKnownApi.get_service_account_issuer_open_id_configuration"""
        try:
            cluster, error = get_cluster_client(request)
            if error:
                return JsonResponse({'error': error}, status=400)

            config = cluster.wellknown_api.get_service_account_issuer_open_id_configuration()
            return JsonResponse(config.to_dict())
        except ApiException as e:
            return KubernetesApiView.handle_api_error(e, 'get_service_account_issuer_openid_configuration')
        except Exception as e:
            return KubernetesApiView.handle_general_error(e, 'get_service_account_issuer_openid_configuration')

    @staticmethod
    def get_service_account_issuer_openid_keyset(request):
        """Implements OpenidApi.get_service_account_issuer_open_id_keyset"""
        try:
            cluster, error = get_cluster_client(request)
            if error:
                return JsonResponse({'error': error}, status=400)

            keyset = cluster.openid_api.get_service_account_issuer_open_id_keyset()
            return JsonResponse(keyset)
        except ApiException as e:
            return KubernetesApiView.handle_api_error(e, 'get_service_account_issuer_openid_keyset')
        except Exception as e:
            return KubernetesApiView.handle_general_error(e, 'get_service_account_issuer_openid_keyset')

    @staticmethod
    def get_code(request):
        """Implements VersionApi.get_code"""
        try:
            cluster, error = get_cluster_client(request)
            if error:
                return JsonResponse({'error': error}, status=400)

            code_version = cluster.version_api.get_code()
            return JsonResponse(code_version.to_dict())
        except ApiException as e:
            return KubernetesApiView.handle_api_error(e, 'get_code')
        except Exception as e:
            return KubernetesApiView.handle_general_error(e, 'get_code')

    @staticmethod
    def log_file_handler(request):
        """Implements LogsApi.log_file_handler"""
        try:
            cluster, error = get_cluster_client(request)
            if error:
                return JsonResponse({'error': error}, status=400)

            # Get log file path from query params
            log_path = request.GET.get('logpath')
            if not log_path:
                return JsonResponse({'error': 'Log path is required'}, status=400)

            # Read and return log file
            try:
                with open(log_path, 'r') as f:
                    return FileResponse(f)
            except FileNotFoundError:
                return JsonResponse({'error': f'Log file not found: {log_path}'}, status=404)
            except Exception as e:
                return JsonResponse({'error': f'Error reading log file: {str(e)}'}, status=500)

        except Exception as e:
            return KubernetesApiView.handle_general_error(e, 'log_file_handler')

    @staticmethod
    def log_file_list_handler(request):
        """Implements LogsApi.log_file_list_handler"""
        try:
            cluster, error = get_cluster_client(request)
            if error:
                return JsonResponse({'error': error}, status=400)

            # List available log files
            try:
                import glob
                import os
                
                # Get log directory from query params or use default
                log_dir = request.GET.get('logdir', '/var/log/containers/')
                
                # List all .log files
                log_files = []
                for f in glob.glob(os.path.join(log_dir, '*.log')):
                    log_files.append({
                        'path': f,
                        'size': os.path.getsize(f),
                        'modified': os.path.getmtime(f)
                    })
                
                return JsonResponse({'log_files': log_files})
            except Exception as e:
                return JsonResponse({'error': f'Error listing log files: {str(e)}'}, status=500)

        except Exception as e:
            return KubernetesApiView.handle_general_error(e, 'log_file_list_handler')

    @staticmethod
    def list_storage_version_migration(request):
        """Implements InternalApiserverV1alpha1Api.list_storage_version_migration"""
        try:
            cluster, error = get_cluster_client(request)
            if error:
                return JsonResponse({'error': error}, status=400)

            migrations = cluster.internal_apiserver_v1alpha1_api.list_storage_version_migration()
            return JsonResponse({
                'items': [migration.to_dict() for migration in migrations.items]
            })
        except ApiException as e:
            return KubernetesApiView.handle_api_error(e, 'list_storage_version_migration')
        except Exception as e:
            return KubernetesApiView.handle_general_error(e, 'list_storage_version_migration')

    @staticmethod
    def read_storage_version_migration(request, name):
        """Implements InternalApiserverV1alpha1Api.read_storage_version_migration"""
        try:
            cluster, error = get_cluster_client(request)
            if error:
                return JsonResponse({'error': error}, status=400)

            migration = cluster.internal_apiserver_v1alpha1_api.read_storage_version_migration(name=name)
            return JsonResponse(migration.to_dict())
        except ApiException as e:
            return KubernetesApiView.handle_api_error(e, 'read_storage_version_migration')
        except Exception as e:
            return KubernetesApiView.handle_general_error(e, 'read_storage_version_migration')

    @staticmethod
    def read_storage_version_migration_status(request, name):
        """Implements InternalApiserverV1alpha1Api.read_storage_version_migration_status"""
        try:
            cluster, error = get_cluster_client(request)
            if error:
                return JsonResponse({'error': error}, status=400)

            status = cluster.internal_apiserver_v1alpha1_api.read_storage_version_migration_status(name=name)
            return JsonResponse(status.to_dict())
        except ApiException as e:
            return KubernetesApiView.handle_api_error(e, 'read_storage_version_migration_status')
        except Exception as e:
            return KubernetesApiView.handle_general_error(e, 'read_storage_version_migration_status')

    @staticmethod
    def list_flow_schema(request):
        """Implements FlowcontrolApiserverV1Api.list_flow_schema"""
        try:
            cluster, error = get_cluster_client(request)
            if error:
                return JsonResponse({'error': error}, status=400)

            schemas = cluster.flowcontrol_apiserver_v1_api.list_flow_schema()
            return JsonResponse({
                'items': [schema.to_dict() for schema in schemas.items]
            })
        except ApiException as e:
            return KubernetesApiView.handle_api_error(e, 'list_flow_schema')
        except Exception as e:
            return KubernetesApiView.handle_general_error(e, 'list_flow_schema')

    @staticmethod
    def list_priority_level_configuration(request):
        """Implements FlowcontrolApiserverV1Api.list_priority_level_configuration"""
        try:
            cluster, error = get_cluster_client(request)
            if error:
                return JsonResponse({'error': error}, status=400)

            configs = cluster.flowcontrol_apiserver_v1_api.list_priority_level_configuration()
            return JsonResponse({
                'items': [config.to_dict() for config in configs.items]
            })
        except ApiException as e:
            return KubernetesApiView.handle_api_error(e, 'list_priority_level_configuration')
        except Exception as e:
            return KubernetesApiView.handle_general_error(e, 'list_priority_level_configuration')

    @staticmethod
    def read_flow_schema(request, name):
        """Implements FlowcontrolApiserverV1Api.read_flow_schema"""
        try:
            cluster, error = get_cluster_client(request)
            if error:
                return JsonResponse({'error': error}, status=400)

            schema = cluster.flowcontrol_apiserver_v1_api.read_flow_schema(name=name)
            return JsonResponse(schema.to_dict())
        except ApiException as e:
            return KubernetesApiView.handle_api_error(e, 'read_flow_schema')
        except Exception as e:
            return KubernetesApiView.handle_general_error(e, 'read_flow_schema')

    @staticmethod
    def read_flow_schema_status(request, name):
        """Implements FlowcontrolApiserverV1Api.read_flow_schema_status"""
        try:
            cluster, error = get_cluster_client(request)
            if error:
                return JsonResponse({'error': error}, status=400)

            status = cluster.flowcontrol_apiserver_v1_api.read_flow_schema_status(name=name)
            return JsonResponse(status.to_dict())
        except ApiException as e:
            return KubernetesApiView.handle_api_error(e, 'read_flow_schema_status')
        except Exception as e:
            return KubernetesApiView.handle_general_error(e, 'read_flow_schema_status')

    @staticmethod
    def read_priority_level_configuration(request, name):
        """Implements FlowcontrolApiserverV1Api.read_priority_level_configuration"""
        try:
            cluster, error = get_cluster_client(request)
            if error:
                return JsonResponse({'error': error}, status=400)

            config = cluster.flowcontrol_apiserver_v1_api.read_priority_level_configuration(name=name)
            return JsonResponse(config.to_dict())
        except ApiException as e:
            return KubernetesApiView.handle_api_error(e, 'read_priority_level_configuration')
        except Exception as e:
            return KubernetesApiView.handle_general_error(e, 'read_priority_level_configuration')

    @staticmethod
    def read_priority_level_configuration_status(request, name):
        """Implements FlowcontrolApiserverV1Api.read_priority_level_configuration_status"""
        try:
            cluster, error = get_cluster_client(request)
            if error:
                return JsonResponse({'error': error}, status=400)

            status = cluster.flowcontrol_apiserver_v1_api.read_priority_level_configuration_status(name=name)
            return JsonResponse(status.to_dict())
        except ApiException as e:
            return KubernetesApiView.handle_api_error(e, 'read_priority_level_configuration_status')
        except Exception as e:
            return KubernetesApiView.handle_general_error(e, 'read_priority_level_configuration_status')

    @staticmethod
    def get_api_resources_node(request):
        """Implements NodeV1Api.get_api_resources"""
        try:
            cluster, error = get_cluster_client(request)
            if error:
                return JsonResponse({'error': error}, status=400)

            resources = cluster.node_v1_api.get_api_resources()
            return JsonResponse(resources.to_dict())
        except ApiException as e:
            return KubernetesApiView.handle_api_error(e, 'get_api_resources_node')
        except Exception as e:
            return KubernetesApiView.handle_general_error(e, 'get_api_resources_node')

    @staticmethod
    def list_runtime_class(request):
        """Implements NodeV1Api.list_runtime_class"""
        try:
            cluster, error = get_cluster_client(request)
            if error:
                return JsonResponse({'error': error}, status=400)

            classes = cluster.node_v1_api.list_runtime_class()
            return JsonResponse({
                'items': [cls.to_dict() for cls in classes.items]
            })
        except ApiException as e:
            return KubernetesApiView.handle_api_error(e, 'list_runtime_class')
        except Exception as e:
            return KubernetesApiView.handle_general_error(e, 'list_runtime_class')

    @staticmethod
    def read_runtime_class(request, name):
        """Implements NodeV1Api.read_runtime_class"""
        try:
            cluster, error = get_cluster_client(request)
            if error:
                return JsonResponse({'error': error}, status=400)

            runtime_class = cluster.node_v1_api.read_runtime_class(name=name)
            return JsonResponse(runtime_class.to_dict())
        except ApiException as e:
            return KubernetesApiView.handle_api_error(e, 'read_runtime_class')
        except Exception as e:
            return KubernetesApiView.handle_general_error(e, 'read_runtime_class')