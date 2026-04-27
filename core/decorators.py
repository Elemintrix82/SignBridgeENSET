from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def admin_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('core:connexion')
        if not request.user.is_admin:
            messages.error(request, 'Accès refusé. Droits administrateur requis.')
            return redirect('core:interface')
        return view_func(request, *args, **kwargs)
    return wrapper
