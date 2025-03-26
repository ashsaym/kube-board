from django.contrib import admin
from django.urls import path
from kubeBoard.views import index_page,all_pods_page,pod_details_page,pod_json_page,download_pod_json

urlpatterns = [
    path('admin/', admin.site.urls),
    path('',index_page, name='index_page'),
    path('all-pods/', all_pods_page, name='all_pods_page'),
    path('pods/<str:namespace>/<str:pod_name>/', pod_details_page, name='pod_details_page'),
    path('pods/<str:namespace>/<str:pod_name>/json/', pod_json_page, name='pod_details_json'),
    path('pods/<str:namespace>/<str:pod_name>/json/download/', download_pod_json, name='download_pod_json'),
]
