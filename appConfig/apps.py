# appConfig/apps.py

from django.apps import AppConfig
import atexit
from .kubeconfig import close_all_cluster_clients

class AppConfig(AppConfig):
    name = 'appConfig'

    def ready(self):
        # Register the shutdown handler
        atexit.register(close_all_cluster_clients)