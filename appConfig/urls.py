from django.contrib import admin
from django.urls import path
from kubeBoard.views import index_page
from kubePods import views as pod_views
from kubeEvents import views as event_views
from kubeLogs import views as log_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', index_page, name='index_page'),

    # Pods-related URLs
    path('all-pods/', pod_views.all_pods_page, name='all_pods_page'),
    path('pods/<str:namespace>/<str:pod_name>/', pod_views.pod_details_page, name='pod_details_page'),
    path('pods/<str:namespace>/<str:pod_name>/json/', pod_views.pod_json_page, name='pod_details_json'),
    path('pods/<str:namespace>/<str:pod_name>/json/download/', pod_views.download_pod_json, name='download_pod_json'),
    path('pods/<str:namespace>/<str:pod_name>/stream-logs/<str:container_name>/', log_views.stream_pod_logs,
         name='stream_pod_logs'),

    # Events-related URLs
    path('events/', event_views.all_events_page, name='all_events_page'),
    path('events/<str:namespace>/<str:event_name>/', event_views.event_detail_page, name='event_detail_page'),
]
