from django.core.exceptions import PermissionDenied

class LawyerRequiredMixin:
    def dispatch(self, request, *args, **kwargs):
        if not request.user.role == 'LAWYER':
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

class CanUploadDocumentMixin:
    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('main.can_upload_document'):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)