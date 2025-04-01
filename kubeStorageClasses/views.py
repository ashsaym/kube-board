# kubeStorageClasses/views.py

import json
from django.shortcuts import render
from django.http import JsonResponse
from kubernetes.client.exceptions import ApiException

from appConfig.settings import logger
from appConfig.utils import get_cluster_client


def all_storage_classes_page(request):
    """
    Renders the page displaying all storage classes.
    """
    try:
        cluster, error = get_cluster_client(request)
        if error:
            return render(request, 'kubeStorageClasses/all_storage_classes.html', {'error': error})

        # Retrieve storage classes
        try:
            storage_classes = cluster.storage_v1.list_storage_class()
            logger.info(f"Retrieved {len(storage_classes.items)} storage classes")
        except ApiException as e:
            logger.error(f"Failed to retrieve storage classes: {e}")
            return render(request, 'kubeStorageClasses/all_storage_classes.html', 
                          {'error': f"Failed to retrieve storage classes: {e}"})

        # Process storage classes
        all_storage_classes_data = []
        for sc in storage_classes.items:
            name = sc.metadata.name
            provisioner = sc.provisioner
            reclaim_policy = sc.reclaim_policy or "Delete"
            volume_binding_mode = sc.volume_binding_mode or "Immediate"
            is_default = sc.metadata.annotations.get('storageclass.kubernetes.io/is-default-class') == 'true' if sc.metadata.annotations else False
            
            all_storage_classes_data.append({
                'name': name,
                'provisioner': provisioner,
                'reclaim_policy': reclaim_policy,
                'volume_binding_mode': volume_binding_mode,
                'is_default': is_default,
                'details_url': f"/storageclasses/{name}/",
            })

        # Convert to JSON for JavaScript
        storage_classes_data_json = json.dumps(all_storage_classes_data)

        # Kubectl commands
        kubectl_commands = {
            'get_storage_classes': 'kubectl get storageclasses',
            'describe_storage_class': 'kubectl describe storageclass <storage-class-name>',
            'create_storage_class': 'kubectl apply -f storage-class.yaml',
            'delete_storage_class': 'kubectl delete storageclass <storage-class-name>',
        }

        return render(request, 'kubeStorageClasses/all_storage_classes.html', {
            'storage_classes_data': all_storage_classes_data,
            'storage_classes_data_json': storage_classes_data_json,
            'kubectl_commands': kubectl_commands,
        })

    except Exception as e:
        logger.error(f"Error in all_storage_classes_page: {e}")
        return render(request, 'kubeStorageClasses/all_storage_classes.html', 
                      {'error': f"An error occurred: {e}"})


def storage_class_details_page(request, storage_class_name):
    """
    Renders the details page for a specific storage class.
    """
    try:
        cluster, error = get_cluster_client(request)
        if error:
            return render(request, 'kubeStorageClasses/storage_class_details.html', {'error': error})

        # Retrieve storage class
        try:
            storage_class = cluster.storage_v1.read_storage_class(name=storage_class_name)
            logger.info(f"Retrieved storage class '{storage_class_name}'")
        except ApiException as e:
            logger.error(f"Failed to retrieve storage class '{storage_class_name}': {e}")
            return render(request, 'kubeStorageClasses/storage_class_details.html', 
                          {'error': f"Failed to retrieve storage class: {e}"})

        # Process storage class details
        sc_details = {
            'name': storage_class.metadata.name,
            'provisioner': storage_class.provisioner,
            'reclaim_policy': storage_class.reclaim_policy or "Delete",
            'volume_binding_mode': storage_class.volume_binding_mode or "Immediate",
            'is_default': storage_class.metadata.annotations.get('storageclass.kubernetes.io/is-default-class') == 'true' if storage_class.metadata.annotations else False,
            'allow_volume_expansion': storage_class.allow_volume_expansion or False,
            'mount_options': storage_class.mount_options or [],
            'parameters': storage_class.parameters or {},
            'creation_timestamp': storage_class.metadata.creation_timestamp,
            'labels': storage_class.metadata.labels or {},
            'annotations': storage_class.metadata.annotations or {},
        }

        # Kubectl commands
        kubectl_commands = {
            'get_storage_class': f'kubectl get storageclass {storage_class_name} -o yaml',
            'describe_storage_class': f'kubectl describe storageclass {storage_class_name}',
            'delete_storage_class': f'kubectl delete storageclass {storage_class_name}',
            'set_default': f'kubectl patch storageclass {storage_class_name} -p \'{"metadata":{"annotations":{"storageclass.kubernetes.io/is-default-class":"true"}}}\'',
        }

        # Convert to JSON for JavaScript
        sc_details_json = json.dumps(sc_details, default=str)

        return render(request, 'kubeStorageClasses/storage_class_details.html', {
            'storage_class': sc_details,
            'storage_class_json': sc_details_json,
            'kubectl_commands': kubectl_commands,
        })

    except Exception as e:
        logger.error(f"Error in storage_class_details_page: {e}")
        return render(request, 'kubeStorageClasses/storage_class_details.html', 
                      {'error': f"An error occurred: {e}"})


def storage_class_json_page(request, storage_class_name):
    """
    Returns the JSON representation of a storage class.
    """
    try:
        cluster, error = get_cluster_client(request)
        if error:
            return JsonResponse({'error': error}, status=400)

        # Retrieve storage class
        try:
            storage_class = cluster.storage_v1.read_storage_class(name=storage_class_name)
            logger.info(f"Retrieved storage class '{storage_class_name}' for JSON view")
        except ApiException as e:
            logger.error(f"Failed to retrieve storage class '{storage_class_name}' for JSON view: {e}")
            return JsonResponse({'error': f"Failed to retrieve storage class: {e}"}, status=404)

        # Convert to dict for JSON response
        sc_dict = storage_class.to_dict()
        
        return JsonResponse(sc_dict)

    except Exception as e:
        logger.error(f"Error in storage_class_json_page: {e}")
        return JsonResponse({'error': f"An error occurred: {e}"}, status=500)