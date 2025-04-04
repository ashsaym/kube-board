# appConfig/urls.py

from django.contrib import admin
from django.urls import path
from kubeBoard.views import index_page, select_kubeconfig
from kubeBoard.api_views import KubernetesApiView
from kubeIngress.views import ingress_detail, all_ingresses_page
from kubePods.views import pod_details_page, pod_json_page, download_pod_json, all_pods_page
from kubeLogs.views import stream_pod_logs
from kubeEvents.views import all_events_page, event_detail_page
from kubeConfigMaps.views import all_config_maps_page, config_map_details_page, config_map_json_page
from kubeSecrets.views import all_secrets_page, secret_details_page, secret_json_page
from kubeDeployments.views import all_deployments_page, deployment_details_page, deployment_json_page
from kubeDaemonSets.views import all_daemon_sets_page, daemon_set_details_page, daemon_set_json_page
from kubeStorageClasses.views import all_storage_classes_page, storage_class_details_page, storage_class_json_page
from kubeStatefulSets.views import all_statefulsets_page, statefulset_details_page, statefulset_json_page
from kubeJobs.views import all_jobs_page, job_details_page, job_json_page
from kubeCronJobs.views import all_cron_jobs_page, cron_job_details_page, cron_job_json_page
from kubeNetworkPolicies.views import all_network_policies_page, network_policy_details_page, network_policy_json_page
from kubePersistentVolumes.views import (
    all_persistent_volumes_page, persistent_volume_details_page, persistent_volume_json_page,
    all_persistent_volume_claims_page, persistent_volume_claim_details_page, persistent_volume_claim_json_page
)
from kubeNamespaces.views import all_namespaces_page, namespace_details_page, namespace_json_page
from kubeBoard.component_views import ComponentStatusView
from kubeBoard.custom_resource_views import CustomResourceView
from kubeBoard.api_registration_views import APIServiceView
from kubeBoard.certificate_views import CertificateSigningRequestView
from kubeBoard.auth_views import AuthenticationView
from kubeBoard.lease_views import LeaseView
from kubeBoard.admission_views import AdmissionRegistrationView
from kubeBoard.discovery_views import DiscoveryView

urlpatterns = [
    # API endpoints
    path('api/versions/', KubernetesApiView.get_api_versions, name='api_versions'),
    path('api/groups/<str:group>/', KubernetesApiView.get_api_group, name='api_group'),
    path('api/resources/<str:group>/<str:version>/', KubernetesApiView.get_api_resources, name='api_resources'),
    path('api/openid/configuration/', KubernetesApiView.get_service_account_issuer_openid_configuration, name='openid_configuration'),
    path('api/openid/keyset/', KubernetesApiView.get_service_account_issuer_openid_keyset, name='openid_keyset'),
    path('api/version/', KubernetesApiView.get_code, name='version_code'),
    path('api/logs/', KubernetesApiView.log_file_handler, name='log_file'),
    path('api/logs/list/', KubernetesApiView.log_file_list_handler, name='log_file_list'),

    # Authentication and Authorization endpoints
    path('api/authentication/resources/', AuthenticationView.get_api_resources_authentication, name='api_resources_authentication'),
    path('api/authorization/resources/', AuthenticationView.get_api_resources_authorization, name='api_resources_authorization'),
    path('api/authorization/v1beta1/resources/', AuthenticationView.get_api_resources_authorization_v1beta1, name='api_resources_authorization_v1beta1'),

    # Lease endpoints
    path('api/coordination/resources/', LeaseView.get_api_resources_coordination, name='api_resources_coordination'),
    path('api/leases/', LeaseView.list_lease_for_all_namespaces, name='list_lease_all'),
    path('api/leases/<str:namespace>/', LeaseView.list_namespaced_lease, name='list_namespaced_lease'),
    path('api/leases/<str:namespace>/<str:name>/', LeaseView.read_namespaced_lease, name='read_namespaced_lease'),

    # Component Status endpoints
    path('api/components/', ComponentStatusView.list_component_status, name='list_component_status'),
    path('api/components/<str:name>/', ComponentStatusView.read_component_status, name='read_component_status'),

    # Custom Resource Definition endpoints
    path('api/crds/', CustomResourceView.list_custom_resource_definition, name='list_custom_resource_definition'),
    path('api/crds/<str:name>/', CustomResourceView.read_custom_resource_definition, name='read_custom_resource_definition'),
    path('api/crds/<str:name>/status/', CustomResourceView.read_custom_resource_definition_status, name='read_custom_resource_definition_status'),

    # Custom Resource endpoints
    path('api/custom/<str:group>/<str:version>/<str:plural>/', CustomResourceView.list_cluster_custom_object, name='list_cluster_custom_object'),
    path('api/custom/<str:group>/<str:version>/<str:plural>/all/', CustomResourceView.list_custom_object_for_all_namespaces, name='list_custom_object_for_all_namespaces'),
    path('api/custom/<str:group>/<str:version>/<str:plural>/<str:name>/', CustomResourceView.get_cluster_custom_object, name='get_cluster_custom_object'),
    path('api/custom/<str:group>/<str:version>/<str:plural>/<str:name>/scale/', CustomResourceView.get_cluster_custom_object_scale, name='get_cluster_custom_object_scale'),
    path('api/custom/<str:group>/<str:version>/<str:plural>/<str:name>/status/', CustomResourceView.get_cluster_custom_object_status, name='get_cluster_custom_object_status'),

    # Storage Version Migration endpoints
    path('api/storage-migrations/', KubernetesApiView.list_storage_version_migration, name='list_storage_version_migration'),
    path('api/storage-migrations/<str:name>/', KubernetesApiView.read_storage_version_migration, name='read_storage_version_migration'),
    path('api/storage-migrations/<str:name>/status/', KubernetesApiView.read_storage_version_migration_status, name='read_storage_version_migration_status'),

    # APIService endpoints
    path('api/services/', APIServiceView.list_api_service, name='list_api_service'),
    path('api/services/<str:name>/', APIServiceView.read_api_service, name='read_api_service'),
    path('api/services/<str:name>/status/', APIServiceView.read_api_service_status, name='read_api_service_status'),

    # Certificate Signing Request endpoints
    path('api/csrs/', CertificateSigningRequestView.list_certificate_signing_request, name='list_certificate_signing_request'),
    path('api/csrs/<str:name>/', CertificateSigningRequestView.read_certificate_signing_request, name='read_certificate_signing_request'),
    path('api/csrs/<str:name>/status/', CertificateSigningRequestView.read_certificate_signing_request_status, name='read_certificate_signing_request_status'),

    # Admission Registration endpoints
    path('api/admission-registration/resources/', AdmissionRegistrationView.get_api_resources_admissionregistration_v1, name='api_resources_admission_registration'),
    path('api/mutating-webhooks/', AdmissionRegistrationView.list_mutating_webhook_configuration, name='list_mutating_webhooks'),
    path('api/mutating-webhooks/<str:name>/', AdmissionRegistrationView.read_mutating_webhook_configuration, name='read_mutating_webhook'),
    path('api/validating-webhooks/', AdmissionRegistrationView.list_validating_webhook_configuration, name='list_validating_webhooks'),
    path('api/validating-webhooks/<str:name>/', AdmissionRegistrationView.read_validating_webhook_configuration, name='read_validating_webhook'),

    # Admission Policy endpoints
    path('api/validating-policies/', AdmissionRegistrationView.list_validating_admission_policy, name='list_validating_policies'),
    path('api/validating-policies/<str:name>/', AdmissionRegistrationView.read_validating_admission_policy, name='read_validating_policy'),
    path('api/validating-policies/<str:name>/status/', AdmissionRegistrationView.read_validating_admission_policy_status, name='read_validating_policy_status'),
    path('api/validating-policy-bindings/', AdmissionRegistrationView.list_validating_admission_policy_binding, name='list_validating_policy_bindings'),
    path('api/validating-policy-bindings/<str:name>/', AdmissionRegistrationView.read_validating_admission_policy_binding, name='read_validating_policy_binding'),

    # Flow Control endpoints
    path('api/flow-schemas/', KubernetesApiView.list_flow_schema, name='list_flow_schema'),
    path('api/flow-schemas/<str:name>/', KubernetesApiView.read_flow_schema, name='read_flow_schema'),
    path('api/flow-schemas/<str:name>/status/', KubernetesApiView.read_flow_schema_status, name='read_flow_schema_status'),
    path('api/priority-levels/', KubernetesApiView.list_priority_level_configuration, name='list_priority_level_configuration'),
    path('api/priority-levels/<str:name>/', KubernetesApiView.read_priority_level_configuration, name='read_priority_level_configuration'),
    path('api/priority-levels/<str:name>/status/', KubernetesApiView.read_priority_level_configuration_status, name='read_priority_level_configuration_status'),

    # RBAC endpoints
    path('api/rbac/resources/', AuthenticationView.get_api_resources_rbac, name='api_resources_rbac'),
    path('api/rbac/cluster-roles/', AuthenticationView.list_cluster_role, name='list_cluster_role'),
    path('api/rbac/cluster-roles/<str:name>/', AuthenticationView.read_cluster_role, name='read_cluster_role'),
    path('api/rbac/cluster-role-bindings/', AuthenticationView.list_cluster_role_binding, name='list_cluster_role_binding'),
    path('api/rbac/cluster-role-bindings/<str:name>/', AuthenticationView.read_cluster_role_binding, name='read_cluster_role_binding'),

    # Discovery endpoints
    path('api/discovery/resources/', DiscoveryView.get_api_resources_discovery, name='api_resources_discovery'),
    path('api/endpoint-slices/', DiscoveryView.list_endpoint_slice_for_all_namespaces, name='list_endpoint_slice_all'),
    path('api/endpoint-slices/<str:namespace>/', DiscoveryView.list_namespaced_endpoint_slice, name='list_namespaced_endpoint_slice'),
    path('api/endpoint-slices/<str:namespace>/<str:name>/', DiscoveryView.read_namespaced_endpoint_slice, name='read_namespaced_endpoint_slice'),

    # Node API endpoints
    path('api/node/resources/', KubernetesApiView.get_api_resources_node, name='api_resources_node'),
    path('api/runtime-classes/', KubernetesApiView.list_runtime_class, name='list_runtime_class'),
    path('api/runtime-classes/<str:name>/', KubernetesApiView.read_runtime_class, name='read_runtime_class'),

    # Existing endpoints
    path('admin/', admin.site.urls),
    path('', index_page, name='index_page'),
    path('select-kubeconfig/', select_kubeconfig, name='select_kubeconfig'),

    # Pods
    path('pods/', all_pods_page, name='all_pods_page'),
    path('pods/<str:namespace>/<str:pod_name>/', pod_details_page, name='pod_details_page'),
    path('pods/<str:namespace>/<str:pod_name>/json/', pod_json_page, name='pod_json_page'),
    path('pods/<str:namespace>/<str:pod_name>/download_json/', download_pod_json, name='download_pod_json'),
    path('pods/<str:namespace>/<str:pod_name>/stream-logs/<str:container_name>/', stream_pod_logs,
         name='stream_pod_logs'),

    # Events
    path('events/', all_events_page, name='all_events_page'),
    path('events/<str:namespace>/<str:event_name>/', event_detail_page, name='event_detail_page'),

    # Ingresses
    path('ingresses/<str:namespace>/<str:name>/', ingress_detail, name='ingress_detail'),
    path('ingresses/', all_ingresses_page, name='all_ingresses_page'),

    # ConfigMaps
    path('configmaps/', all_config_maps_page, name='all_config_maps_page'),
    path('configmaps/<str:namespace>/<str:config_map_name>/', config_map_details_page, name='config_map_details_page'),
    path('configmaps/<str:namespace>/<str:config_map_name>/json/', config_map_json_page, name='config_map_json_page'),

    # Secrets
    path('secrets/', all_secrets_page, name='all_secrets_page'),
    path('secrets/<str:namespace>/<str:secret_name>/', secret_details_page, name='secret_details_page'),
    path('secrets/<str:namespace>/<str:secret_name>/json/', secret_json_page, name='secret_json_page'),

    # Deployments
    path('deployments/', all_deployments_page, name='all_deployments_page'),
    path('deployments/<str:namespace>/<str:deployment_name>/', deployment_details_page, name='deployment_details_page'),
    path('deployments/<str:namespace>/<str:deployment_name>/json/', deployment_json_page, name='deployment_json_page'),

    # DaemonSets
    path('daemonsets/', all_daemon_sets_page, name='all_daemon_sets_page'),
    path('daemonsets/<str:namespace>/<str:daemon_set_name>/', daemon_set_details_page, name='daemon_set_details_page'),
    path('daemonsets/<str:namespace>/<str:daemon_set_name>/json/', daemon_set_json_page, name='daemon_set_json_page'),

    # StorageClasses
    path('storageclasses/', all_storage_classes_page, name='all_storage_classes_page'),
    path('storageclasses/<str:storage_class_name>/', storage_class_details_page, name='storage_class_details_page'),
    path('storageclasses/<str:storage_class_name>/json/', storage_class_json_page, name='storage_class_json_page'),
    
    # StatefulSets
    path('statefulsets/', all_statefulsets_page, name='all_statefulsets_page'),
    path('statefulsets/<str:namespace>/<str:statefulset_name>/', statefulset_details_page, name='statefulset_details_page'),
    path('statefulsets/<str:namespace>/<str:statefulset_name>/json/', statefulset_json_page, name='statefulset_json_page'),
    
    # Jobs
    path('jobs/', all_jobs_page, name='all_jobs_page'),
    path('jobs/<str:namespace>/<str:job_name>/', job_details_page, name='job_details_page'),
    path('jobs/<str:namespace>/<str:job_name>/json/', job_json_page, name='job_json_page'),
    
    # CronJobs
    path('cronjobs/', all_cron_jobs_page, name='all_cron_jobs_page'),
    path('cronjobs/<str:namespace>/<str:cron_job_name>/', cron_job_details_page, name='cron_job_details_page'),
    path('cronjobs/<str:namespace>/<str:cron_job_name>/json/', cron_job_json_page, name='cron_job_json_page'),
    
    # NetworkPolicies
    path('networkpolicies/', all_network_policies_page, name='all_network_policies_page'),
    path('networkpolicies/<str:namespace>/<str:network_policy_name>/', network_policy_details_page, name='network_policy_details_page'),
    path('networkpolicies/<str:namespace>/<str:network_policy_name>/json/', network_policy_json_page, name='network_policy_json_page'),
    
    # PersistentVolumes
    path('persistentvolumes/', all_persistent_volumes_page, name='all_persistent_volumes_page'),
    path('persistentvolumes/<str:pv_name>/', persistent_volume_details_page, name='persistent_volume_details_page'),
    path('persistentvolumes/<str:pv_name>/json/', persistent_volume_json_page, name='persistent_volume_json_page'),
    
    # PersistentVolumeClaims
    path('persistentvolumeclaims/', all_persistent_volume_claims_page, name='all_persistent_volume_claims_page'),
    path('persistentvolumeclaims/<str:namespace>/<str:pvc_name>/', persistent_volume_claim_details_page, name='persistent_volume_claim_details_page'),
    path('persistentvolumeclaims/<str:namespace>/<str:pvc_name>/json/', persistent_volume_claim_json_page, name='persistent_volume_claim_json_page'),
    
    # Namespaces
    path('namespaces/', all_namespaces_page, name='all_namespaces_page'),
    path('namespaces/<str:namespace_name>/', namespace_details_page, name='namespace_details_page'),
    path('namespaces/<str:namespace_name>/json/', namespace_json_page, name='namespace_json_page'),
]