from django.http import JsonResponse
from kubernetes.client import ApiException
from appConfig.utils import get_cluster_client, KubernetesResourceView

class CertificateSigningRequestView(KubernetesResourceView):
    """Views for handling Certificate Signing Request operations"""

    @staticmethod
    def list_certificate_signing_request(request):
        """Implements CertificatesV1Api.list_certificate_signing_request"""
        try:
            cluster, error = get_cluster_client(request)
            if error:
                return JsonResponse({'error': error}, status=400)

            csrs = cluster.certificates_v1_api.list_certificate_signing_request()
            return JsonResponse({
                'items': [csr.to_dict() for csr in csrs.items]
            })
        except ApiException as e:
            return CertificateSigningRequestView.handle_api_error(e, 'list_certificate_signing_request')
        except Exception as e:
            return CertificateSigningRequestView.handle_general_error(e, 'list_certificate_signing_request')

    @staticmethod
    def read_certificate_signing_request(request, name):
        """Implements CertificatesV1Api.read_certificate_signing_request"""
        try:
            cluster, error = get_cluster_client(request)
            if error:
                return JsonResponse({'error': error}, status=400)

            csr = cluster.certificates_v1_api.read_certificate_signing_request(name=name)
            return JsonResponse(csr.to_dict())
        except ApiException as e:
            return CertificateSigningRequestView.handle_api_error(e, 'read_certificate_signing_request')
        except Exception as e:
            return CertificateSigningRequestView.handle_general_error(e, 'read_certificate_signing_request')

    @staticmethod
    def read_certificate_signing_request_status(request, name):
        """Implements CertificatesV1Api.read_certificate_signing_request_status"""
        try:
            cluster, error = get_cluster_client(request)
            if error:
                return JsonResponse({'error': error}, status=400)

            status = cluster.certificates_v1_api.read_certificate_signing_request_status(name=name)
            return JsonResponse(status.to_dict())
        except ApiException as e:
            return CertificateSigningRequestView.handle_api_error(e, 'read_certificate_signing_request_status')
        except Exception as e:
            return CertificateSigningRequestView.handle_general_error(e, 'read_certificate_signing_request_status')