from django.contrib import admin
from django.urls import path
from kubeBoard.views import index_page

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', index_page, name='index_page'),
]
