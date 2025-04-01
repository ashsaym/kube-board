import json
from datetime import datetime, timezone

from django.http import HttpResponse
from django.shortcuts import render
from kubernetes.client import ApiException

from appConfig.kubeconfig import list_jobs, list_jobs_for_all_namespaces
from appConfig.settings import logger
from appConfig.utils import get_cluster_client


def all_jobs_page(request):
    """
    Displays all Jobs across all namespaces in the selected Kubernetes cluster.
    """
    cluster, error = get_cluster_client(request)
    if error:
        return HttpResponse(error, status=500)

    try:
        # Get all namespaces
        all_namespaces = cluster.core_v1.list_namespace().items

        # Get all Jobs across all namespaces
        try:
            jobs = cluster.batch_v1.list_job_for_all_namespaces()
        except ApiException as e:
            logger.error(f"Failed to retrieve Jobs: {e}")
            jobs = None

        # Process jobs to add age and other useful information
        processed_jobs = []
        if jobs and jobs.items:
            for job in jobs.items:
                creation_time = job.metadata.creation_timestamp
                if creation_time:
                    age_timedelta = datetime.now(timezone.utc) - creation_time
                    age_hours = age_timedelta.total_seconds() / 3600
                    age_str = f"{int(age_hours)}h" if age_hours < 24 else f"{int(age_hours / 24)}d"
                else:
                    age_str = "N/A"

                # Calculate completion status
                status = "Running"
                if job.status.succeeded:
                    status = "Completed"
                elif job.status.failed:
                    status = "Failed"

                # Calculate completions
                completions = job.spec.completions or 1
                succeeded = job.status.succeeded or 0
                completion_str = f"{succeeded}/{completions}"

                processed_jobs.append({
                    'name': job.metadata.name,
                    'namespace': job.metadata.namespace,
                    'status': status,
                    'completions': completion_str,
                    'age': age_str,
                    'details_url': f"/jobs/{job.metadata.namespace}/{job.metadata.name}/",
                })

        kubectl_command = {
            'get': "kubectl get jobs --all-namespaces",
            'yaml': "kubectl get jobs --all-namespaces -o yaml",
            'describe': "kubectl describe jobs --all-namespaces",
            'create': "kubectl create job <job-name> --image=<image-name>",
            'delete': "kubectl delete job <job-name> -n <namespace>",
        }

        context = {
            'namespaces': all_namespaces,
            'jobs': jobs.items if jobs else [],
            'processed_jobs': processed_jobs,
            'kubectl_command': kubectl_command,
        }

        return render(request, 'kubeJobs/all-jobs.html', context)

    except ApiException as e:
        error_message = f"API Error: {e.reason or 'An unknown API error occurred.'}"
        logger.error(f"API Exception in all_jobs_page: {error_message}")
        return HttpResponse(error_message, status=e.status if e.status else 500)
    except Exception as e:
        error_message = f"Unexpected Error: {str(e)}"
        logger.error(f"Unexpected Exception in all_jobs_page: {error_message}")
        return HttpResponse(error_message, status=500)


def job_details_page(request, namespace, job_name):
    """
    Displays detailed information about a specific Job.
    """
    cluster, error = get_cluster_client(request)
    if error:
        return HttpResponse(error, status=500)

    try:
        job = cluster.batch_v1.read_namespaced_job(job_name, namespace)
        if not job:
            return HttpResponse("Job not found", status=404)

        # Get pods managed by this job
        selector = ""
        if job.spec.selector and job.spec.selector.match_labels:
            selector_parts = []
            for key, value in job.spec.selector.match_labels.items():
                selector_parts.append(f"{key}={value}")
            selector = ",".join(selector_parts)

        pods = []
        if selector:
            try:
                pod_list = cluster.core_v1.list_namespaced_pod(
                    namespace=namespace,
                    label_selector=selector
                )
                pods = pod_list.items
            except ApiException as e:
                logger.error(f"Failed to list pods for job '{job_name}': {e}")

        # Get events related to this job
        events = []
        try:
            event_list = cluster.core_v1.list_namespaced_event(
                namespace=namespace,
                field_selector=f"involvedObject.name={job_name},involvedObject.kind=Job"
            )
            events = event_list.items
        except ApiException as e:
            logger.error(f"Failed to list events for job '{job_name}': {e}")

        # Format events
        formatted_events = []
        for event in events:
            first_seen = event.first_timestamp.replace(tzinfo=timezone.utc).astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S") if event.first_timestamp else ''
            last_seen = event.last_timestamp.replace(tzinfo=timezone.utc).astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S") if event.last_timestamp else ''
            formatted_events.append({
                'type': event.type,
                'reason': event.reason,
                'message': event.message,
                'first_seen': first_seen,
                'last_seen': last_seen,
            })

        kubectl_commands = [
            {
                'command': f"kubectl get job {job_name} -n {namespace}",
                'explanation': "Lists details about the specified Job."
            },
            {
                'command': f"kubectl get job {job_name} -n {namespace} -o yaml",
                'explanation': "Outputs the Job's configuration in YAML format."
            },
            {
                'command': f"kubectl describe job {job_name} -n {namespace}",
                'explanation': "Provides detailed information about the Job."
            },
            {
                'command': f"kubectl delete job {job_name} -n {namespace}",
                'explanation': "Deletes the specified Job."
            },
        ]

        context = {
            'job': job,
            'pods': pods,
            'events': formatted_events,
            'selected_namespace': namespace,
            'job_name': job_name,
            'kubectl_commands': kubectl_commands,
        }

        return render(request, 'kubeJobs/job-details.html', context)

    except ApiException as e:
        if e.status == 404:
            return HttpResponse("Job not found", status=404)
        else:
            error_message = f"An error occurred: {e.reason or 'Unknown error'}"
            logger.error(f"API Exception in job_details_page: {error_message}")
            return HttpResponse(error_message, status=e.status if e.status else 500)
    except Exception as e:
        error_message = f"Unexpected Error: {str(e)}"
        logger.error(f"Unexpected Exception in job_details_page: {error_message}")
        return HttpResponse(error_message, status=500)


def job_json_page(request, namespace, job_name):
    """
    Displays the JSON representation of a specific Job.
    """
    cluster, error = get_cluster_client(request)
    if error:
        return HttpResponse(error, status=500)

    try:
        job = cluster.batch_v1.read_namespaced_job(job_name, namespace)
        if not job:
            return HttpResponse("Job not found", status=404)

        api_client = cluster.batch_v1.api_client
        serialized_job = api_client.sanitize_for_serialization(job)
        job_json = json.dumps(serialized_job, indent=4)

        context = {
            'job_json': job_json,
            'job_name': job_name,
            'namespace': namespace,
        }

        return render(request, 'kubeJobs/job-details-json.html', context)

    except ApiException as e:
        if e.status == 404:
            return HttpResponse("Job not found", status=404)
        else:
            error_message = f"An error occurred: {e.reason or 'Unknown error'}"
            logger.error(f"API Exception in job_json_page: {error_message}")
            return HttpResponse(error_message, status=e.status if e.status else 500)
    except Exception as e:
        error_message = f"Unexpected Error: {str(e)}"
        logger.error(f"Unexpected Exception in job_json_page: {error_message}")
        return HttpResponse(error_message, status=500)