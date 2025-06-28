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

@register.filter(name='status_to_bootstrap_class')
def status_to_bootstrap_class(status):
    """
    Перетворює статус заявки на відповідний CSS-клас Bootstrap.
    """
    mapping = {
        'PENDING': 'bg-secondary',
        'очікує': 'bg-secondary',

        'IN_PROGRESS': 'bg-primary',
        'в роботі': 'bg-primary',
        
        'COMPLETED': 'bg-success',
        'виконано': 'bg-success',
        
        'CANCELED': 'bg-danger',
        'скасовано': 'bg-danger',

        # Додамо статуси для OID, якщо вони використовуються
        'new': 'bg-info',
        'in_progress': 'bg-primary',
        'done': 'bg-success',
        'cancelled': 'bg-danger',
        'problem': 'bg-warning',
    }
    return mapping.get(status, 'bg-dark') # Повертаємо 'bg-dark' для невідомих статусів




@register.filter
def div(value, arg):
    try:
        return int(value) // int(arg)
    except (ValueError, ZeroDivisionError):
        return ''

@register.filter
def mul(value, arg):
    try:
        return int(value) * int(arg)
    except ValueError:
        return ''

@register.filter
def sub(value, arg):
    try:
        return int(value) - int(arg)
    except ValueError:
        return ''

@register.filter
def mod(value, arg):
    try:
        return int(value) % int(arg)
    except (ValueError, ZeroDivisionError):
        return ''