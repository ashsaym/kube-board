import json

from django.http import StreamingHttpResponse, HttpResponse
from kubernetes.client import ApiException

from appConfig.kubeconfig import v1


# Create your views here.
def stream_pod_logs(request, namespace, pod_name, container_name):
    try:
        pod_logs = v1.read_namespaced_pod_log(
            name=pod_name,
            namespace=namespace,
            container=container_name,
            follow=True,
            tail_lines=100,  # Fetch the last 100 log lines initially
            _preload_content=False
        )

        def event_stream():
            try:
                for log_line in pod_logs:
                    decoded_log = log_line.decode('utf-8').rstrip()
                    yield f"data: {json.dumps({'log': decoded_log})}\n\n"
            except GeneratorExit:
                v1.api_client.close()  # Handle client disconnect
            except Exception as e:
                yield f"data: {json.dumps({'log': f'Error streaming logs: {str(e)}'})}\n\n"

        response = StreamingHttpResponse(event_stream(), content_type='text/event-stream')
        response['Cache-Control'] = 'no-cache'
        response['X-Accel-Buffering'] = 'no'
        return response

    except ApiException as e:
        return HttpResponse(f"API Error: {e.reason}", status=e.status)
    except Exception as e:
        return HttpResponse(f"Unexpected Error: {str(e)}", status=500)