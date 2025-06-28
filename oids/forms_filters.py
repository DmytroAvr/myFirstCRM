# C:\myFirstCRM\oids\forms_filters.py
from django import forms
from django.forms import inlineformset_factory, modelformset_factory, formset_factory
from .models import (OIDTypeChoices, OIDStatusChoices, SecLevelChoices, WorkRequestStatusChoices, WorkTypeChoices, 
    DocumentReviewResultChoices, AttestationRegistrationStatusChoices, PeminSubTypeChoices
)
from .models import (
    WorkRequest, WorkRequestItem, OID, Unit, Person, Trip, TripResultForUnit, Document, DocumentType,
    AttestationRegistration, AttestationResponse,  TechnicalTask
)


# форма для фільтрації
class OIDFilterForm(forms.Form):
    # Використовуємо ModelMultipleChoiceField для полів, пов'язаних з моделями
    unit = forms.ModelMultipleChoiceField(
        queryset=Unit.objects.all().order_by('code'),
        required=False,
        label="Військова частина",
        widget=forms.SelectMultiple(attrs={'class': 'tomselect-field', 'placeholder': 'Оберіть одну або декілька ВЧ...'})
    )
    city = forms.MultipleChoiceField(
        choices=[], # Заповнимо динамічно в __init__
        required=False,
        label="Місто",
        widget=forms.SelectMultiple(attrs={'class': 'tomselect-field', 'placeholder': 'Оберіть місто...'})
    )
    # Використовуємо MultipleChoiceField для полів з вибором (choices)
    oid_type = forms.MultipleChoiceField(
        choices=OIDTypeChoices.choices,
        required=False,
        label="Тип ОІД",
        widget=forms.SelectMultiple(attrs={'class': 'tomselect-field', 'placeholder': 'Оберіть тип...'})
    )
    pemin_sub_type = forms.MultipleChoiceField(
        choices=PeminSubTypeChoices.choices,
        required=False,
        label="Клас (ПЕМІН)",
        widget=forms.SelectMultiple(attrs={'class': 'tomselect-field', 'placeholder': 'Оберіть клас...'})
    )
    status = forms.MultipleChoiceField(
        choices=OIDStatusChoices.choices,
        required=False,
        label="Статус",
        widget=forms.SelectMultiple(attrs={'class': 'tomselect-field', 'placeholder': 'Оберіть статус...'})
    )
    sec_level = forms.MultipleChoiceField(
        choices=SecLevelChoices.choices,
        required=False,
        label="Гриф",
        widget=forms.SelectMultiple(attrs={'class': 'tomselect-field', 'placeholder': 'Оберіть гриф...'})
    )
    # Поле для повнотекстового пошуку
    search_query = forms.CharField(
        required=False,
        label="Пошук",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Пошук по шифру, назві, кімнаті...'})
    )
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Динамічно отримуємо список унікальних міст з моделі Unit
        # і встановлюємо його як вибір для поля 'city'
        cities = Unit.objects.exclude(city__isnull=True).exclude(city__exact='')\
                             .values_list('city', 'city').distinct().order_by('city')
        self.fields['city'].choices = cities

class TechnicalTaskFilterForm(forms.Form):
    unit = forms.ModelMultipleChoiceField( 
        queryset=Unit.objects.all().order_by('code'),
        required=False,
        label="Військові частини",
        widget=forms.SelectMultiple(attrs={'id': 'id_tt_filter_unit', 'class': ' tomselect-field'}) 
        # auto-submit-filter

    )
    oid = forms.ModelMultipleChoiceField(  
        queryset=OID.objects.none(),  
        required=False,
        label="ОІДи",
        widget=forms.SelectMultiple(attrs={'id': 'id_tt_filter_oid', 'class': ' tomselect-field'}) 
    )
    review_result = forms.ChoiceField(
        choices=[('', 'Всі статуси')] + DocumentReviewResultChoices.choices, # Додав порожній вибір на початок
        required=False, label="Статус ТЗ",
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    )
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Встановлюємо актуальний queryset для поля 'unit' при кожному створенні форми
        self.fields['unit'].queryset = Unit.objects.all().order_by('code')

class WorkRequestFilterForm(forms.Form):
    unit = forms.ModelMultipleChoiceField(
        queryset=Unit.objects.all().order_by('code'),
        required=False,
        label="Військова частина",
        widget=forms.SelectMultiple(attrs={'class': 'tomselect-field', 'placeholder': 'Оберіть ВЧ...'})
    )
    status = forms.MultipleChoiceField(
        choices=WorkRequestStatusChoices.choices,
        required=False,
        label="Статус заявки",
        widget=forms.SelectMultiple(attrs={'class': 'tomselect-field', 'placeholder': 'Оберіть статус...'})
    )
    date_from = forms.DateField(
        required=False,
        label="вх. дата заявки (з)",
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control', 'id':'id_start_date'})
    )
    date_to = forms.DateField(
        required=False,
        label="вх. дата заявки (по)",
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control', 'id':'id_end_date'})
    )
    search_query = forms.CharField(
        required=False,
        label="Пошук",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Пошук по номеру, ВЧ, ОІД...'})
    )

class WorkRequestItemProcessingFilterForm(forms.Form):
    prefix = 'wri'
    unit = forms.ModelMultipleChoiceField(  
        queryset=Unit.objects.all().order_by('code'),
        required=False,
        label="Військові частини",
        widget=forms.SelectMultiple(attrs={'id': 'id_wri_filter_unit', 'class': ' tomselect-field'})  
    )
    oid = forms.ModelMultipleChoiceField(   
        queryset=OID.objects.none(), # Залишаємо порожнім, JS заповнить
        required=False,
        label="ОІДи",
        widget=forms.SelectMultiple(attrs={'id': 'id_wri_filter_oid', 'class': ' tomselect-field'})  
    )
    status = forms.ChoiceField(
        choices=[('', 'Всі статуси')] + WorkRequestStatusChoices.choices, # Додав порожній вибір
        required=False, label="Статус ел. заявки",
        widget=forms.Select(attrs={'class': 'form-select form-select-sm  '})
    )
    trip_date_from = forms.DateField(
        label="Дата відрядження (з)",
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control form-control-sm '})
    )
    trip_date_to = forms.DateField(
        label="Дата відрядження (по)",
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control form-control-sm '})
    )
    deadline_from = forms.DateField(required=False, widget=forms.DateInput(attrs={'type':'date', 'class':'form-control form-control-sm '}), label="Дедлайн з" )
    deadline_to = forms.DateField(required=False, widget=forms.DateInput(attrs={'type':'date', 'class':'form-control form-control-sm '}), label="Дедлайн по")
    processed = forms.ChoiceField(
		choices=[('', 'Всі'), ('yes', 'Опрацьовано'), ('no', 'Не опрацьовано')],
		required=False,
		label="Стан факт. опрацювання",
		widget=forms.Select(attrs={'class': 'form-select form-select-sm '})
	)
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Встановлюємо актуальний queryset для поля 'unit'
        self.fields['unit'].queryset = Unit.objects.all().order_by('code')

class DocumentFilterForm(forms.Form):
    # Дозволяємо вибір кількох ВЧ
    unit = forms.ModelMultipleChoiceField(
        queryset=Unit.objects.all().order_by('code'),
        required=False,
        label="Військова частина",
        widget=forms.SelectMultiple(attrs={'class': 'tomselect-field', 'placeholder': 'Оберіть ВЧ...'})
    )
    # Дозволяємо вибір кількох типів документів
    document_type = forms.ModelMultipleChoiceField(
        queryset=DocumentType.objects.all().order_by('name'),
        required=False,
        label="Тип документа",
        widget=forms.SelectMultiple(attrs={'class': 'tomselect-field', 'placeholder': 'Оберіть тип...'})
    )
    # Дозволяємо вибір кількох авторів
    author = forms.ModelMultipleChoiceField(
        queryset=Person.objects.filter(is_active=True).order_by('full_name'),
        required=False,
        label="Автор/Виконавець",
        widget=forms.SelectMultiple(attrs={'class': 'tomselect-field', 'placeholder': 'Оберіть автора...'})
    )
    # Фільтри по датах
    date_from = forms.DateField(
        required=False,
        label="Дата опрацювання (з)",
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control', 'id':'id_start_date'})
    )
    date_to = forms.DateField(
        required=False,
        label="Дата опрацювання (по)",
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control', 'id':'id_end_date'})
    )
    # Поле для повнотекстового пошуку
    search_query = forms.CharField(
        required=False,
        label="Пошук",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Пошук по номеру, ОІД, примітках...'})
    )

class TechnicalTaskFilterForm(forms.Form):
    unit = forms.ModelMultipleChoiceField(
        queryset=Unit.objects.all().order_by('code'),
        required=False,
        label="Військова частина",
        widget=forms.SelectMultiple(attrs={'class': 'tomselect-field', 'placeholder': 'Оберіть ВЧ...'})
    )
    oid = forms.ModelMultipleChoiceField(
        queryset=OID.objects.all().order_by('cipher'),
        required=False,
        label="ОІД",
        widget=forms.SelectMultiple(attrs={'class': 'tomselect-field', 'placeholder': 'Оберіть ОІД...'})
    )
    review_result = forms.MultipleChoiceField(
        choices=DocumentReviewResultChoices.choices,
        required=False,
        label="Результат розгляду",
        widget=forms.SelectMultiple(attrs={'class': 'tomselect-field', 'placeholder': 'Оберіть результат...'})
    )
    reviewed_by = forms.ModelMultipleChoiceField(
        queryset=Person.objects.filter(is_active=True).order_by('full_name'),
        required=False,
        label="Хто ознайомився",
        widget=forms.SelectMultiple(attrs={'class': 'tomselect-field', 'placeholder': 'Оберіть особу...'})
    )
    input_date_from = forms.DateField(
        label="Вхідна дата (з)", required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control', 'id':'id_start_date'})
    )
    input_date_to = forms.DateField(
        label="Вхідна дата (по)", required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control', 'id':'id_end_date'})
    )
    
    search_query = forms.CharField(
        required=False,
        label="Пошук",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Номер ТЗ, шифр/назва ОІД...'})
    )
    
class AttestationRegistrationFilterForm(forms.Form):
    units = forms.ModelMultipleChoiceField(
        queryset=Unit.objects.all().order_by('code'),
        required=False,
        label="Військова частина",
        widget=forms.SelectMultiple(attrs={'class': 'tomselect-field', 'placeholder': 'Оберіть ВЧ...'})
    )
    status = forms.MultipleChoiceField(
        choices=AttestationRegistrationStatusChoices.choices,
        required=False,
        label="Статус відправки",
        widget=forms.SelectMultiple(attrs={'class': 'tomselect-field', 'placeholder': 'Оберіть статус...'})
    )
    sent_by = forms.ModelMultipleChoiceField(
        queryset=Person.objects.filter(is_active=True).order_by('full_name'),
        required=False,
        label="Хто відправив",
        widget=forms.SelectMultiple(attrs={'class': 'tomselect-field', 'placeholder': 'Оберіть особу...'})
    )
    date_from = forms.DateField(
        required=False,
        label="Дата відправки (з)",
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    date_to = forms.DateField(
        required=False,
        label="Дата відправки (по)",
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    search_query = forms.CharField(
        required=False,
        label="Пошук",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Пошук по номеру листа...'})
    )
    
class AttestationResponseFilterForm(forms.Form):
    # Дозволяємо вибір кількох відправок
    attestation_registration_sent = forms.ModelMultipleChoiceField(
        queryset=AttestationRegistration.objects.all().order_by('-outgoing_letter_date'),
        required=False,
        label="Пов'язана відправка",
        widget=forms.SelectMultiple(attrs={'class': 'tomselect-field', 'placeholder': 'Оберіть відправку...'})
    )
    # Дозволяємо вибір кількох осіб, що отримали відповідь
    received_by = forms.ModelMultipleChoiceField(
        queryset=Person.objects.filter(is_active=True).order_by('full_name'),
        required=False,
        label="Хто отримав",
        widget=forms.SelectMultiple(attrs={'class': 'tomselect-field', 'placeholder': 'Оберіть особу...'})
    )
    # Фільтри по датах
    date_from = forms.DateField(
        required=False,
        label="Дата вх. листа (з)",
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    date_to = forms.DateField(
        required=False,
        label="Дата вх. листа (по)",
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    # Поле для повнотекстового пошуку
    search_query = forms.CharField(
        required=False,
        label="Пошук",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Пошук по номеру листа...'})
    )

class RegisteredActsFilterForm(forms.Form):
    unit = forms.ModelMultipleChoiceField(
        queryset=Unit.objects.all().order_by('code'),
        required=False,
        label="Військова частина",
        widget=forms.SelectMultiple(attrs={'id': 'id_filter_unit', 'class': 'tomselect-field'})
    )
    registration_date_from = forms.DateField(
        required=False, label="Дата реєстрації ДССЗЗІ (з)",
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    registration_date_to = forms.DateField(
        required=False, label="Дата реєстрації ДССЗЗІ (по)",
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    search_query = forms.CharField(
        required=False,
        label="Пошук",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Номер акту, ОІД, реєстр. номер...'})
    )
