from django.core.exceptions import PermissionDenied


def admin_required(view_func):
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated or not (
            request.user.is_admin or request.user.is_superuser
        ):
            raise PermissionDenied
        return view_func(request, *args, **kwargs)

    return _wrapped_view


def profesor_required(view_func):
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role != "profesor":
            raise PermissionDenied
        return view_func(request, *args, **kwargs)

    return _wrapped_view
