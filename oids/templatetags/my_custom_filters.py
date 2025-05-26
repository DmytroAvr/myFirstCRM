# oids/templatetags/my_custom_filters.py
from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Повертає елемент словника або кверісету за ключем/ID.
    Приклад використання: {{ my_queryset|get_item:my_id }}
    """
    if hasattr(dictionary, 'get'):
        return dictionary.get(key)
    elif hasattr(dictionary, 'filter'):
        return dictionary.filter(pk=key).first()
    return None

