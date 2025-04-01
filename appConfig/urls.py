# appConfig/urls.py

from django.contrib import admin
from django.urls import path
from kubeBoard.views import index_page, select_kubeconfig
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

urlpatterns = [
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