from typing import Optional, Dict, Any
from kubernetes.client import ApiException
from appConfig.settings import logger
from appConfig.utils import KubernetesResourceView

class LogHandler(KubernetesResourceView):
    """Utility class for handling Kubernetes log operations"""

    @staticmethod
    def get_log_options(params: Dict[str, Any]) -> Dict[str, Any]:
        """Creates log options from request parameters"""
        return {
            'container': params.get('container'),
            'follow': params.get('follow', False),
            'tail_lines': params.get('tail_lines'),
            'previous': params.get('previous', False),
            'since_seconds': params.get('since_seconds'),
            'timestamps': params.get('timestamps', False),
            'limit_bytes': params.get('limit_bytes'),
        }

    @staticmethod
    def read_namespaced_pod_log(cluster, namespace: str, pod_name: str, **kwargs) -> Optional[str]:
        """
        Reads logs from a specific pod in a namespace.
        Returns None if there's an error.
        """
        try:
            return cluster.core_v1_api.read_namespaced_pod_log(
                name=pod_name,
                namespace=namespace,
                **kwargs
            )
        except ApiException as e:
            logger.error(f"Failed to read pod logs for {pod_name} in {namespace}: {e}")
            return None

    @staticmethod
    def read_namespaced_pod_log_stream(cluster, namespace: str, pod_name: str, **kwargs):
        """Returns a stream for reading pod logs"""
        try:
            return cluster.core_v1_api.read_namespaced_pod_log(
                name=pod_name,
                namespace=namespace,
                _preload_content=False,
                **kwargs
            )
        except ApiException as e:
            logger.error(f"Failed to stream pod logs for {pod_name} in {namespace}: {e}")
            return None