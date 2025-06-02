from .models import OIDTypeChoices, OIDStatusChoices, SecLevelChoices # Або де визначені ваші Choices

def global_choices(request):
    # Припустимо, для нового ОІД доступні не всі статуси
    # Наприклад, тільки "створюється"
    filtered_oid_status_choices = [
        (OIDStatusChoices.NEW.value, OIDStatusChoices.NEW.label),
        (OIDStatusChoices.RECEIVED_REQUEST.value, OIDStatusChoices.RECEIVED_REQUEST.label),
        (OIDStatusChoices.ACTIVE.value, OIDStatusChoices.ACTIVE.label),
        # Додайте інші статуси, якщо потрібно для початкового створення
    ]
    
    # OIDTypeChoices та SecLevelChoices можуть залишатися повними
    # або також фільтруватися за вашою логікою

    return {
        'oid_type_choices_global': OIDTypeChoices.choices,
        'oid_status_choices_global_for_new': filtered_oid_status_choices, 
        'oid_status_choices_global_all': OIDStatusChoices.choices, 
        'sec_level_choices_global': SecLevelChoices.choices,
    }