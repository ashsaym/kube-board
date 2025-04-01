from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/(?P<resource_type>\w+)/$', consumers.KubernetesResourceConsumer.as_asgi()),
]