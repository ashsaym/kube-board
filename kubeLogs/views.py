# kubeLogs/views.py

import json
from django.http import StreamingHttpResponse, HttpResponse
from kubernetes.client import ApiException
from appConfig.settings import logger
from appConfig.utils import get_cluster_client, acquire_stream_semaphore, release_stream_semaphore

def stream_pod_logs(request, namespace, pod_name, container_name):
    """
    Streams the logs of a specific pod's container in the selected Kubernetes cluster.
    """
    # Retrieve the ClusterClient based on the user's selected kubeconfig
    cluster, error = get_cluster_client(request)
    if error:
        logger.error(f"Failed to get cluster client: {error}")
        return HttpResponse(error, status=500)

    # Acquire semaphore before starting the log stream
    if not acquire_stream_semaphore():
        error_message = "Maximum number of concurrent log streams reached. Please try again later."
        logger.warning(error_message)
        return HttpResponse(error_message, status=429)  # 429 Too Many Requests

    # Get tail_lines from query parameters with default value
    try:
        tail_lines = int(request.GET.get('tail_lines', 100))
        if tail_lines < 1:
            raise ValueError("tail_lines must be a positive integer.")
    except ValueError as ve:
        # Release semaphore and return error response
        release_stream_semaphore()
        error_message = f"Invalid tail_lines parameter: {str(ve)}"
        logger.error(error_message)
        return HttpResponse(error_message, status=400)  # 400 Bad Request

    try:
        # Initialize the log stream
        pod_logs = cluster.core_v1.read_namespaced_pod_log(
            name=pod_name,
            namespace=namespace,
            container=container_name,
            follow=True,
            tail_lines=tail_lines,
            _preload_content=False,
            pretty=True,
            async_req=False
        )

        def event_stream():
            try:
                for log_line in pod_logs.stream():
                    if isinstance(log_line, bytes):
                        decoded_log = log_line.decode('utf-8').rstrip()
                    elif isinstance(log_line, str):
                        decoded_log = log_line.rstrip()
                    elif isinstance(log_line, dict):
                        # Assuming log_line is a JSON object
                        decoded_log = json.dumps(log_line).rstrip()
                    elif isinstance(log_line, list):
                        # Assuming log_line is a list of JSON objects
                        decoded_log = json.dumps(log_line).rstrip()
                    else:
                        decoded_log = str(log_line).rstrip()
                    yield f"data: {json.dumps({'log': decoded_log})}\n\n\n\n"
            except GeneratorExit:
                logger.info(f"Client disconnected from log streaming for pod '{pod_name}' in namespace '{namespace}'.")
            except Exception as e:
                error_message = f"Error streaming logs: {str(e)}"
                logger.error(error_message)
                yield f"data: {json.dumps({'log': error_message})}\n\n"
            finally:
                # Ensure the semaphore is released when streaming ends
                release_stream_semaphore()
                # Close the pod_logs stream to free resources
                pod_logs.close()

        # Create a StreamingHttpResponse using the generator
        response = StreamingHttpResponse(event_stream(), content_type='text/event-stream')
        response['Cache-Control'] = 'no-cache'
        response['X-Accel-Buffering'] = 'no'

        return response

    except ApiException as e:
        # Release semaphore in case of an exception
        release_stream_semaphore()
        error_message = f"API Error: {e.reason or 'An unknown API error occurred.'}"
        logger.error(f"API Exception in stream_pod_logs: {error_message}")
        return HttpResponse(error_message, status=e.status if e.status else 500)
    except Exception as e:
        # Release semaphore in case of an exception
        release_stream_semaphore()
        error_message = f"Unexpected Error: {str(e)}"
        logger.error(f"Unexpected Exception in stream_pod_logs: {error_message}")
        return HttpResponse(error_message, status=500)