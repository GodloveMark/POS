from .models import Store, StoreSettings

def store_settings_context(request):
    if not request.user.is_authenticated:
        return {}

    store = Store.objects.filter(owner=request.user).first()

    if not store:
        return {}

    settings, _ = StoreSettings.objects.get_or_create(store=store)

    return {
        "store_settings": settings,
        "current_store": store,
    }
