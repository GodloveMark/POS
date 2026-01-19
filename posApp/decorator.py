from django.http import HttpResponseForbidden

def cashier_only(view_func):
    def wrapper(request, *args, **kwargs):
        if request.user.role != 'cashier':
            return HttpResponseForbidden("Access denied.")
        return view_func(request, *args, **kwargs)
    return wrapper

def admin_or_manager_only(view_func):
    def wrapper(request, *args, **kwargs):
        if request.user.role not in ['admin', 'manager']:
            return HttpResponseForbidden("Not allowed.")
        return view_func(request, *args, **kwargs)
    return wrapper
