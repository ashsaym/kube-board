from django.contrib import admin
from django.urls import path
from kubeBoard.views import index_page, select_kubeconfig
from kubePods.views import pod_details_page, pod_json_page, download_pod_json, all_pods_page
from kubeLogs.views import stream_pod_logs

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', index_page, name='index_page'),
    path('select-kubeconfig/', select_kubeconfig, name='select_kubeconfig'),
path('pods/', all_pods_page, name='all_pods_page'),
    path('pods/<str:namespace>/<str:pod_name>/', pod_details_page, name='pod_details_page'),
    path('pods/<str:namespace>/<str:pod_name>/json/', pod_json_page, name='pod_json_page'),
    path('pods/<str:namespace>/<str:pod_name>/download_json/', download_pod_json, name='download_pod_json'),

    path('pods/<str:namespace>/<str:pod_name>/stream-logs/<str:container_name>/', stream_pod_logs,
         name='stream_pod_logs'),
]
