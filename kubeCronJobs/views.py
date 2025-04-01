import json
from datetime import datetime, timezone

from django.http import HttpResponse
from django.shortcuts import render
from kubernetes.client import ApiException

from appConfig.kubeconfig import list_cron_jobs, list_cron_jobs_for_all_namespaces
from appConfig.settings import logger
from appConfig.utils import get_cluster_client


def all_cron_jobs_page(request):
    """
    Displays all CronJobs across all namespaces in the selected Kubernetes cluster.
    """
    cluster, error = get_cluster_client(request)
    if error:
        return HttpResponse(error, status=500)

    try:
        # Get all namespaces
        all_namespaces = cluster.core_v1.list_namespace().items

        # Get all CronJobs across all namespaces
        try:
            cron_jobs = cluster.batch_v1.list_cron_job_for_all_namespaces()
        except ApiException as e:
            logger.error(f"Failed to retrieve CronJobs: {e}")
            cron_jobs = None

        # Process cron_jobs to add age and other useful information
        processed_cron_jobs = []
        if cron_jobs and cron_jobs.items:
            for cron_job in cron_jobs.items:
                creation_time = cron_job.metadata.creation_timestamp
                if creation_time:
                    age_timedelta = datetime.now(timezone.utc) - creation_time
                    age_hours = age_timedelta.total_seconds() / 3600
                    age_str = f"{int(age_hours)}h" if age_hours < 24 else f"{int(age_hours / 24)}d"
                else:
                    age_str = "N/A"

                # Get schedule and status
                schedule = cron_job.spec.schedule or "N/A"
                suspend = cron_job.spec.suspend or False
                status = "Suspended" if suspend else "Active"
                
                # Get last schedule time
                last_schedule = "Never"
                if cron_job.status and cron_job.status.last_schedule_time:
                    last_schedule_time = cron_job.status.last_schedule_time
                    last_schedule = last_schedule_time.strftime("%Y-%m-%d %H:%M:%S")

                processed_cron_jobs.append({
                    'name': cron_job.metadata.name,
                    'namespace': cron_job.metadata.namespace,
                    'schedule': schedule,
                    'status': status,
                    'last_schedule': last_schedule,
                    'age': age_str,
                    'details_url': f"/cronjobs/{cron_job.metadata.namespace}/{cron_job.metadata.name}/",
                })

        kubectl_command = {
            'get': "kubectl get cronjobs --all-namespaces",
            'yaml': "kubectl get cronjobs --all-namespaces -o yaml",
            'describe': "kubectl describe cronjobs --all-namespaces",
            'create': "kubectl create cronjob <cronjob-name> --image=<image-name> --schedule='*/1 * * * *'",
            'suspend': "kubectl patch cronjob <cronjob-name> -p '{\"spec\":{\"suspend\":true}}' -n <namespace>",
            'resume': "kubectl patch cronjob <cronjob-name> -p '{\"spec\":{\"suspend\":false}}' -n <namespace>",
            'delete': "kubectl delete cronjob <cronjob-name> -n <namespace>",
        }

        context = {
            'namespaces': all_namespaces,
            'cron_jobs': cron_jobs.items if cron_jobs else [],
            'processed_cron_jobs': processed_cron_jobs,
            'kubectl_command': kubectl_command,
        }

        return render(request, 'kubeCronJobs/all-cronjobs.html', context)

    except ApiException as e:
        error_message = f"API Error: {e.reason or 'An unknown API error occurred.'}"
        logger.error(f"API Exception in all_cron_jobs_page: {error_message}")
        return HttpResponse(error_message, status=e.status if e.status else 500)
    except Exception as e:
        error_message = f"Unexpected Error: {str(e)}"
        logger.error(f"Unexpected Exception in all_cron_jobs_page: {error_message}")
        return HttpResponse(error_message, status=500)


def cron_job_details_page(request, namespace, cron_job_name):
    """
    Displays detailed information about a specific CronJob.
    """
    cluster, error = get_cluster_client(request)
    if error:
        return HttpResponse(error, status=500)

    try:
        cron_job = cluster.batch_v1.read_namespaced_cron_job(cron_job_name, namespace)
        if not cron_job:
            return HttpResponse("CronJob not found", status=404)

        # Get jobs created by this cronjob
        jobs = []
        try:
            job_list = cluster.batch_v1.list_namespaced_job(namespace=namespace)
            for job in job_list.items:
                # Check if job is owned by this cronjob
                for owner_ref in job.metadata.owner_references or []:
                    if owner_ref.kind == "CronJob" and owner_ref.name == cron_job_name:
                        jobs.append(job)
                        break
        except ApiException as e:
            logger.error(f"Failed to list jobs for cronjob '{cron_job_name}': {e}")

        # Get events related to this cronjob
        events = []
        try:
            event_list = cluster.core_v1.list_namespaced_event(
                namespace=namespace,
                field_selector=f"involvedObject.name={cron_job_name},involvedObject.kind=CronJob"
            )
            events = event_list.items
        except ApiException as e:
            logger.error(f"Failed to list events for cronjob '{cron_job_name}': {e}")

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

        # Format jobs
        formatted_jobs = []
        for job in jobs:
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

            formatted_jobs.append({
                'name': job.metadata.name,
                'status': status,
                'age': age_str,
                'details_url': f"/jobs/{job.metadata.namespace}/{job.metadata.name}/",
            })

        kubectl_commands = [
            {
                'command': f"kubectl get cronjob {cron_job_name} -n {namespace}",
                'explanation': "Lists details about the specified CronJob."
            },
            {
                'command': f"kubectl get cronjob {cron_job_name} -n {namespace} -o yaml",
                'explanation': "Outputs the CronJob's configuration in YAML format."
            },
            {
                'command': f"kubectl describe cronjob {cron_job_name} -n {namespace}",
                'explanation': "Provides detailed information about the CronJob."
            },
            {
                'command': f"kubectl patch cronjob {cron_job_name} -p '{{\"spec\":{{\"suspend\":true}}}}' -n {namespace}",
                'explanation': "Suspends the CronJob."
            },
            {
                'command': f"kubectl patch cronjob {cron_job_name} -p '{{\"spec\":{{\"suspend\":false}}}}' -n {namespace}",
                'explanation': "Resumes the CronJob."
            },
            {
                'command': f"kubectl create job manual-{cron_job_name} --from=cronjob/{cron_job_name} -n {namespace}",
                'explanation': "Creates a Job manually from the CronJob."
            },
            {
                'command': f"kubectl delete cronjob {cron_job_name} -n {namespace}",
                'explanation': "Deletes the specified CronJob."
            },
        ]

        context = {
            'cron_job': cron_job,
            'jobs': formatted_jobs,
            'events': formatted_events,
            'selected_namespace': namespace,
            'cron_job_name': cron_job_name,
            'kubectl_commands': kubectl_commands,
        }

        return render(request, 'kubeCronJobs/cronjob-details.html', context)

    except ApiException as e:
        if e.status == 404:
            return HttpResponse("CronJob not found", status=404)
        else:
            error_message = f"An error occurred: {e.reason or 'Unknown error'}"
            logger.error(f"API Exception in cron_job_details_page: {error_message}")
            return HttpResponse(error_message, status=e.status if e.status else 500)
    except Exception as e:
        error_message = f"Unexpected Error: {str(e)}"
        logger.error(f"Unexpected Exception in cron_job_details_page: {error_message}")
        return HttpResponse(error_message, status=500)


def cron_job_json_page(request, namespace, cron_job_name):
    """
    Displays the JSON representation of a specific CronJob.
    """
    cluster, error = get_cluster_client(request)
    if error:
        return HttpResponse(error, status=500)

    try:
        cron_job = cluster.batch_v1.read_namespaced_cron_job(cron_job_name, namespace)
        if not cron_job:
            return HttpResponse("CronJob not found", status=404)

        api_client = cluster.batch_v1.api_client
        serialized_cron_job = api_client.sanitize_for_serialization(cron_job)
        cron_job_json = json.dumps(serialized_cron_job, indent=4)

        context = {
            'cron_job_json': cron_job_json,
            'cron_job_name': cron_job_name,
            'namespace': namespace,
        }

        return render(request, 'kubeCronJobs/cronjob-details-json.html', context)

    except ApiException as e:
        if e.status == 404:
            return HttpResponse("CronJob not found", status=404)
        else:
            error_message = f"An error occurred: {e.reason or 'Unknown error'}"
            logger.error(f"API Exception in cron_job_json_page: {error_message}")
            return HttpResponse(error_message, status=e.status if e.status else 500)
    except Exception as e:
        error_message = f"Unexpected Error: {str(e)}"
        logger.error(f"Unexpected Exception in cron_job_json_page: {error_message}")
        return HttpResponse(error_message, status=500)