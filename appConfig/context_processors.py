# appConfig/context_processors.py

from .kubeconfig import list_kubeconfigs

def kubeconfig_context(request):
    """
    Adds kubeconfig files and the selected kubeconfig to the template context.
    """
    kubeconfig_files = [kubeconfig_file.name for kubeconfig_file in list_kubeconfigs()]
    selected_kubeconfig = request.session.get('selected_kubeconfig')

    if selected_kubeconfig not in kubeconfig_files:
        # Default to the first kubeconfig file if available
        selected_kubeconfig = kubeconfig_files[0] if kubeconfig_files else None
        request.session['selected_kubeconfig'] = selected_kubeconfig

    return {
        'kubeconfig_files': kubeconfig_files,
        'selected_kubeconfig': selected_kubeconfig,
    }