from django import template

register = template.Library()

@register.filter
def get_user_store(user):
    """
    Return the first store linked to the user, or None.
    """
    storeuser = getattr(user, "storeuser_set", None)
    if storeuser:
        link = storeuser.first()
        if link and hasattr(link, "store"):
            return link.store
    return None
