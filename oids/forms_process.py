from django import forms
from .models import (OIDTypeChoices, OIDStatusChoices, SecLevelChoices, WorkRequestStatusChoices, WorkTypeChoices, 
    DocumentReviewResultChoices, AttestationRegistrationStatusChoices, PeminSubTypeChoices
)
from .models import (
    WorkRequest, WorkRequestItem, OID, Unit, Person, Trip, TripResultForUnit, Document, DocumentType,
    AttestationRegistration, AttestationResponse,  TechnicalTask
)

class DeclarationProcessStartForm(forms.Form):
    """Форма для ініціації процесу 'ДСК-Декларація'."""
    unit = forms.ModelChoiceField(
        queryset=Unit.objects.all().order_by('code'),
        label="Військова частина",
        widget=forms.Select(attrs={'class': 'form-select'}) # Можна додати TomSelect
    )
    cipher = forms.CharField(
        label="Шифр ОІД",
        help_text="Наприклад: ДСКДекларація АС1/2/3",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    full_name = forms.CharField(label="Повна назва ОІД", required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    pemin_sub_type = forms.ChoiceField(
        label="Тип ЕОТ",
        choices=[(PeminSubTypeChoices.AS1_4_DSK, PeminSubTypeChoices.AS1_4_DSK.label), (PeminSubTypeChoices.AS23_4_DSK, PeminSubTypeChoices.AS23_4_DSK.label)],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    serial_number = forms.CharField(label="Серійний номер", required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    inventory_number = forms.CharField(label="Інвентарний номер", required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    note = forms.CharField(label="Примітка", required=False, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}))
    
    # Поля, які заповнюються автоматично, але можуть бути потрібні для логіки
    oid_type = forms.CharField(initial=OIDTypeChoices.PEMIN, widget=forms.HiddenInput())
    sec_level = forms.CharField(initial=SecLevelChoices.DSK, widget=forms.HiddenInput())
    initial_oid_status = forms.CharField(initial=OIDStatusChoices.RECEIVED_DECLARATION, widget=forms.HiddenInput()) # Новий статус
    room = forms.CharField(initial='ДСК', widget=forms.HiddenInput())

class SendForRegistrationForm(forms.Form):
    """
    Форма-підтвердження для відправки документа на реєстрацію.
    """
    confirmation = forms.BooleanField(
        required=True,
        label="Я підтверджую відправку цього документа на реєстрацію.",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
