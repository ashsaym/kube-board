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
]
