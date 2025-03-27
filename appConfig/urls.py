from django.contrib import admin
from django.urls import path
from kubeBoard.views import index_page, select_kubeconfig

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', index_page, name='index_page'),
    path('select-kubeconfig/', select_kubeconfig, name='select_kubeconfig'),
]
