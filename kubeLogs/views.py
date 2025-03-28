# appName/views.py

import json

from django.http import StreamingHttpResponse, HttpResponse
from kubernetes.client import ApiException

from appConfig.utils import get_cluster_client  # Import the helper function
from appConfig.settings import logger
def stream_pod_logs(request, namespace, pod_name, container_name):
    """
    Streams the logs of a specific pod's container in the selected Kubernetes cluster.

    Args:
        request (HttpRequest): The incoming HTTP request.
        namespace (str): The namespace of the pod.
        pod_name (str): The name of the pod.
        container_name (str): The name of the container within the pod.

    Returns:
        StreamingHttpResponse: A streaming HTTP response with log data.
        HttpResponse: An error response in case of failures.
    """
    # Retrieve the ClusterClient based on the user's selected kubeconfig
    cluster, error = get_cluster_client(request)
    if error:
        logger.error(f"Failed to get cluster client: {error}")
        return HttpResponse(error, status=500)

    try:
        # Initialize the log stream
        pod_logs = cluster.core_v1.read_namespaced_pod_log(
            name=pod_name,
            namespace=namespace,
            container=container_name,
            follow=True,
            tail_lines=100,  # Fetch the last 100 log lines initially
            _preload_content=False,
            pretty=True,
            async_req=False
        )

        def event_stream():
            try:
                for log_line in pod_logs:
                    if isinstance(log_line, bytes):
                        decoded_log = log_line.decode('utf-8').rstrip()
                    else:
                        decoded_log = str(log_line).rstrip()
                    yield f"data: {json.dumps({'log': decoded_log})}\n\n"
            except GeneratorExit:
                cluster.core_v1.api_client.close()  # Handle client disconnect
                logger.info(f"Log streaming for pod '{pod_name}' in namespace '{namespace}' has been terminated by the client.")
            except Exception as e:
                error_message = f"Error streaming logs: {str(e)}"
                logger.error(error_message)
                yield f"data: {json.dumps({'log': error_message})}\n\n"

        response = StreamingHttpResponse(event_stream(), content_type='text/event-stream')
        response['Cache-Control'] = 'no-cache'
        response['X-Accel-Buffering'] = 'no'
        return response

    except ApiException as e:
        error_message = f"API Error: {e.reason or 'An unknown API error occurred.'}"
        logger.error(f"API Exception in stream_pod_logs: {error_message}")
        return HttpResponse(error_message, status=e.status if e.status else 500)
    except Exception as e:
        error_message = f"Unexpected Error: {str(e)}"
        logger.error(f"Unexpected Exception in stream_pod_logs: {error_message}")
        return HttpResponse(error_message, status=500)