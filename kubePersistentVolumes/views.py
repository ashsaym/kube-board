import json
from datetime import datetime, timezone

from django.http import HttpResponse
from django.shortcuts import render
from kubernetes.client import ApiException

from appConfig.kubeconfig import list_persistent_volumes, list_persistent_volume_claims
from appConfig.settings import logger
from appConfig.utils import get_cluster_client


def all_persistent_volumes_page(request):
    """
    Displays all PersistentVolumes in the selected Kubernetes cluster.
    """
    cluster, error = get_cluster_client(request)
    if error:
        return HttpResponse(error, status=500)

    try:
        # Get all PersistentVolumes
        try:
            persistent_volumes = cluster.core_v1.list_persistent_volume()
        except ApiException as e:
            logger.error(f"Failed to retrieve PersistentVolumes: {e}")
            persistent_volumes = None

        # Process persistent_volumes to add age and other useful information
        processed_persistent_volumes = []
        if persistent_volumes and persistent_volumes.items:
            for pv in persistent_volumes.items:
                creation_time = pv.metadata.creation_timestamp
                if creation_time:
                    age_timedelta = datetime.now(timezone.utc) - creation_time
                    age_hours = age_timedelta.total_seconds() / 3600
                    age_str = f"{int(age_hours)}h" if age_hours < 24 else f"{int(age_hours / 24)}d"
                else:
                    age_str = "N/A"

                # Get capacity
                capacity = "N/A"
                if pv.spec.capacity and 'storage' in pv.spec.capacity:
                    capacity = pv.spec.capacity['storage']

                # Get access modes
                access_modes = pv.spec.access_modes or []
                access_modes_str = ", ".join(access_modes)

                # Get claim reference
                claim_ref = "N/A"
                if pv.spec.claim_ref:
                    claim_ref = f"{pv.spec.claim_ref.namespace}/{pv.spec.claim_ref.name}"

                processed_persistent_volumes.append({
                    'name': pv.metadata.name,
                    'status': pv.status.phase,
                    'capacity': capacity,
                    'access_modes': access_modes_str,
                    'reclaim_policy': pv.spec.persistent_volume_reclaim_policy,
                    'storage_class': pv.spec.storage_class_name or "N/A",
                    'claim': claim_ref,
                    'age': age_str,
                    'details_url': f"/persistentvolumes/{pv.metadata.name}/",
                })

        kubectl_command = {
            'get': "kubectl get pv",
            'yaml': "kubectl get pv -o yaml",
            'describe': "kubectl describe pv",
            'create': "kubectl create -f pv.yaml",
            'delete': "kubectl delete pv <pv-name>",
        }

        context = {
            'persistent_volumes': persistent_volumes.items if persistent_volumes else [],
            'processed_persistent_volumes': processed_persistent_volumes,
            'kubectl_command': kubectl_command,
        }

        return render(request, 'kubePersistentVolumes/all-persistentvolumes.html', context)

    except ApiException as e:
        error_message = f"API Error: {e.reason or 'An unknown API error occurred.'}"
        logger.error(f"API Exception in all_persistent_volumes_page: {error_message}")
        return HttpResponse(error_message, status=e.status if e.status else 500)
    except Exception as e:
        error_message = f"Unexpected Error: {str(e)}"
        logger.error(f"Unexpected Exception in all_persistent_volumes_page: {error_message}")
        return HttpResponse(error_message, status=500)


def persistent_volume_details_page(request, pv_name):
    """
    Displays detailed information about a specific PersistentVolume.
    """
    cluster, error = get_cluster_client(request)
    if error:
        return HttpResponse(error, status=500)

    try:
        pv = cluster.core_v1.read_persistent_volume(pv_name)
        if not pv:
            return HttpResponse("PersistentVolume not found", status=404)

        # Get PVCs that reference this PV
        pvcs = []
        if pv.spec.claim_ref:
            try:
                pvc = cluster.core_v1.read_namespaced_persistent_volume_claim(
                    name=pv.spec.claim_ref.name,
                    namespace=pv.spec.claim_ref.namespace
                )
                pvcs.append(pvc)
            except ApiException as e:
                logger.error(f"Failed to read PVC for PV '{pv_name}': {e}")

        # Get events related to this PV
        events = []
        try:
            event_list = cluster.core_v1.list_event_for_all_namespaces(
                field_selector=f"involvedObject.name={pv_name},involvedObject.kind=PersistentVolume"
            )
            events = event_list.items
        except ApiException as e:
            logger.error(f"Failed to list events for PV '{pv_name}': {e}")

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
                'command': f"kubectl get pv {pv_name}",
                'explanation': "Lists details about the specified PersistentVolume."
            },
            {
                'command': f"kubectl get pv {pv_name} -o yaml",
                'explanation': "Outputs the PersistentVolume's configuration in YAML format."
            },
            {
                'command': f"kubectl describe pv {pv_name}",
                'explanation': "Provides detailed information about the PersistentVolume."
            },
            {
                'command': f"kubectl delete pv {pv_name}",
                'explanation': "Deletes the specified PersistentVolume."
            },
        ]

        context = {
            'pv': pv,
            'pvcs': pvcs,
            'events': formatted_events,
            'pv_name': pv_name,
            'kubectl_commands': kubectl_commands,
        }

        return render(request, 'kubePersistentVolumes/persistentvolume-details.html', context)

    except ApiException as e:
        if e.status == 404:
            return HttpResponse("PersistentVolume not found", status=404)
        else:
            error_message = f"An error occurred: {e.reason or 'Unknown error'}"
            logger.error(f"API Exception in persistent_volume_details_page: {error_message}")
            return HttpResponse(error_message, status=e.status if e.status else 500)
    except Exception as e:
        error_message = f"Unexpected Error: {str(e)}"
        logger.error(f"Unexpected Exception in persistent_volume_details_page: {error_message}")
        return HttpResponse(error_message, status=500)


def persistent_volume_json_page(request, pv_name):
    """
    Displays the JSON representation of a specific PersistentVolume.
    """
    cluster, error = get_cluster_client(request)
    if error:
        return HttpResponse(error, status=500)

    try:
        pv = cluster.core_v1.read_persistent_volume(pv_name)
        if not pv:
            return HttpResponse("PersistentVolume not found", status=404)

        api_client = cluster.core_v1.api_client
        serialized_pv = api_client.sanitize_for_serialization(pv)
        pv_json = json.dumps(serialized_pv, indent=4)

        context = {
            'pv_json': pv_json,
            'pv_name': pv_name,
        }

        return render(request, 'kubePersistentVolumes/persistentvolume-details-json.html', context)

    except ApiException as e:
        if e.status == 404:
            return HttpResponse("PersistentVolume not found", status=404)
        else:
            error_message = f"An error occurred: {e.reason or 'Unknown error'}"
            logger.error(f"API Exception in persistent_volume_json_page: {error_message}")
            return HttpResponse(error_message, status=e.status if e.status else 500)
    except Exception as e:
        error_message = f"Unexpected Error: {str(e)}"
        logger.error(f"Unexpected Exception in persistent_volume_json_page: {error_message}")
        return HttpResponse(error_message, status=500)


def all_persistent_volume_claims_page(request):
    """
    Displays all PersistentVolumeClaims across all namespaces in the selected Kubernetes cluster.
    """
    cluster, error = get_cluster_client(request)
    if error:
        return HttpResponse(error, status=500)

    try:
        # Get all namespaces
        all_namespaces = cluster.core_v1.list_namespace().items

        # Get all PersistentVolumeClaims across all namespaces
        try:
            pvcs = cluster.core_v1.list_persistent_volume_claim_for_all_namespaces()
        except ApiException as e:
            logger.error(f"Failed to retrieve PersistentVolumeClaims: {e}")
            pvcs = None

        # Process pvcs to add age and other useful information
        processed_pvcs = []
        if pvcs and pvcs.items:
            for pvc in pvcs.items:
                creation_time = pvc.metadata.creation_timestamp
                if creation_time:
                    age_timedelta = datetime.now(timezone.utc) - creation_time
                    age_hours = age_timedelta.total_seconds() / 3600
                    age_str = f"{int(age_hours)}h" if age_hours < 24 else f"{int(age_hours / 24)}d"
                else:
                    age_str = "N/A"

                # Get capacity
                capacity = "N/A"
                if pvc.status and pvc.status.capacity and 'storage' in pvc.status.capacity:
                    capacity = pvc.status.capacity['storage']

                # Get access modes
                access_modes = pvc.spec.access_modes or []
                access_modes_str = ", ".join(access_modes)

                # Get volume name
                volume_name = pvc.spec.volume_name or "N/A"

                processed_pvcs.append({
                    'name': pvc.metadata.name,
                    'namespace': pvc.metadata.namespace,
                    'status': pvc.status.phase,
                    'volume': volume_name,
                    'capacity': capacity,
                    'access_modes': access_modes_str,
                    'storage_class': pvc.spec.storage_class_name or "N/A",
                    'age': age_str,
                    'details_url': f"/persistentvolumeclaims/{pvc.metadata.namespace}/{pvc.metadata.name}/",
                })

        kubectl_command = {
            'get': "kubectl get pvc --all-namespaces",
            'yaml': "kubectl get pvc --all-namespaces -o yaml",
            'describe': "kubectl describe pvc --all-namespaces",
            'create': "kubectl create -f pvc.yaml",
            'delete': "kubectl delete pvc <pvc-name> -n <namespace>",
        }

        context = {
            'namespaces': all_namespaces,
            'pvcs': pvcs.items if pvcs else [],
            'processed_pvcs': processed_pvcs,
            'kubectl_command': kubectl_command,
        }

        return render(request, 'kubePersistentVolumes/all-persistentvolumeclaims.html', context)

    except ApiException as e:
        error_message = f"API Error: {e.reason or 'An unknown API error occurred.'}"
        logger.error(f"API Exception in all_persistent_volume_claims_page: {error_message}")
        return HttpResponse(error_message, status=e.status if e.status else 500)
    except Exception as e:
        error_message = f"Unexpected Error: {str(e)}"
        logger.error(f"Unexpected Exception in all_persistent_volume_claims_page: {error_message}")
        return HttpResponse(error_message, status=500)


def persistent_volume_claim_details_page(request, namespace, pvc_name):
    """
    Displays detailed information about a specific PersistentVolumeClaim.
    """
    cluster, error = get_cluster_client(request)
    if error:
        return HttpResponse(error, status=500)

    try:
        pvc = cluster.core_v1.read_namespaced_persistent_volume_claim(pvc_name, namespace)
        if not pvc:
            return HttpResponse("PersistentVolumeClaim not found", status=404)

        # Get PV that this PVC references
        pv = None
        if pvc.spec.volume_name:
            try:
                pv = cluster.core_v1.read_persistent_volume(pvc.spec.volume_name)
            except ApiException as e:
                logger.error(f"Failed to read PV for PVC '{pvc_name}': {e}")

        # Get pods that use this PVC
        pods = []
        try:
            pod_list = cluster.core_v1.list_namespaced_pod(namespace=namespace)
            for pod in pod_list.items:
                for volume in pod.spec.volumes or []:
                    if volume.persistent_volume_claim and volume.persistent_volume_claim.claim_name == pvc_name:
                        pods.append(pod)
                        break
        except ApiException as e:
            logger.error(f"Failed to list pods for PVC '{pvc_name}': {e}")

        # Get events related to this PVC
        events = []
        try:
            event_list = cluster.core_v1.list_namespaced_event(
                namespace=namespace,
                field_selector=f"involvedObject.name={pvc_name},involvedObject.kind=PersistentVolumeClaim"
            )
            events = event_list.items
        except ApiException as e:
            logger.error(f"Failed to list events for PVC '{pvc_name}': {e}")

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
                'command': f"kubectl get pvc {pvc_name} -n {namespace}",
                'explanation': "Lists details about the specified PersistentVolumeClaim."
            },
            {
                'command': f"kubectl get pvc {pvc_name} -n {namespace} -o yaml",
                'explanation': "Outputs the PersistentVolumeClaim's configuration in YAML format."
            },
            {
                'command': f"kubectl describe pvc {pvc_name} -n {namespace}",
                'explanation': "Provides detailed information about the PersistentVolumeClaim."
            },
            {
                'command': f"kubectl delete pvc {pvc_name} -n {namespace}",
                'explanation': "Deletes the specified PersistentVolumeClaim."
            },
        ]

        context = {
            'pvc': pvc,
            'pv': pv,
            'pods': pods,
            'events': formatted_events,
            'selected_namespace': namespace,
            'pvc_name': pvc_name,
            'kubectl_commands': kubectl_commands,
        }

        return render(request, 'kubePersistentVolumes/persistentvolumeclaim-details.html', context)

    except ApiException as e:
        if e.status == 404:
            return HttpResponse("PersistentVolumeClaim not found", status=404)
        else:
            error_message = f"An error occurred: {e.reason or 'Unknown error'}"
            logger.error(f"API Exception in persistent_volume_claim_details_page: {error_message}")
            return HttpResponse(error_message, status=e.status if e.status else 500)
    except Exception as e:
        error_message = f"Unexpected Error: {str(e)}"
        logger.error(f"Unexpected Exception in persistent_volume_claim_details_page: {error_message}")
        return HttpResponse(error_message, status=500)


def persistent_volume_claim_json_page(request, namespace, pvc_name):
    """
    Displays the JSON representation of a specific PersistentVolumeClaim.
    """
    cluster, error = get_cluster_client(request)
    if error:
        return HttpResponse(error, status=500)

    try:
        pvc = cluster.core_v1.read_namespaced_persistent_volume_claim(pvc_name, namespace)
        if not pvc:
            return HttpResponse("PersistentVolumeClaim not found", status=404)

        api_client = cluster.core_v1.api_client
        serialized_pvc = api_client.sanitize_for_serialization(pvc)
        pvc_json = json.dumps(serialized_pvc, indent=4)

        context = {
            'pvc_json': pvc_json,
            'pvc_name': pvc_name,
            'namespace': namespace,
        }

        return render(request, 'kubePersistentVolumes/persistentvolumeclaim-details-json.html', context)

    except ApiException as e:
        if e.status == 404:
            return HttpResponse("PersistentVolumeClaim not found", status=404)
        else:
            error_message = f"An error occurred: {e.reason or 'Unknown error'}"
            logger.error(f"API Exception in persistent_volume_claim_json_page: {error_message}")
            return HttpResponse(error_message, status=e.status if e.status else 500)
    except Exception as e:
        error_message = f"Unexpected Error: {str(e)}"
        logger.error(f"Unexpected Exception in persistent_volume_claim_json_page: {error_message}")
        return HttpResponse(error_message, status=500)