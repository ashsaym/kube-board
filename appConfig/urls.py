from django.contrib import admin
from django.urls import path
from kubeBoard.views import index_page, all_pods_page, pod_details_page, pod_json_page, download_pod_json, \
    all_events_page, event_detail_page, stream_pod_logs

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', index_page, name='index_page'),
    path('all-pods/', all_pods_page, name='all_pods_page'),
    path('pods/<str:namespace>/<str:pod_name>/', pod_details_page, name='pod_details_page'),
    path('pods/<str:namespace>/<str:pod_name>/json/', pod_json_page, name='pod_details_json'),
    path('pods/<str:namespace>/<str:pod_name>/json/download/', download_pod_json, name='download_pod_json'),
    path('pods/<str:namespace>/<str:pod_name>/stream-logs/<str:container_name>/', stream_pod_logs,
         name='stream_pod_logs'),
    # SSE Endpoint
    path('events/', all_events_page, name='all_events_page'),
    path('events/<str:namespace>/<str:event_name>/', event_detail_page, name='event_detail_page'),  # Updated pattern
]
