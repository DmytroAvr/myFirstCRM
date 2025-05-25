# C:\myFirstCRM\oids\forms.py

# oids/forms.py
from django import forms
from .models import (
    WorkRequest, WorkRequestItem, OID, Unit, Person, Trip, Document, DocumentType,
    WorkRequestStatusChoices, WorkTypeChoices, OIDTypeChoices
)

# --- Форми для панелі керування ---

class WorkRequestForm(forms.ModelForm):
    # Поля, які будуть відображатися у формі
    # OIDs повинні бути MultiSelect, оскільки заявка може стосуватися кількох ОІД
    oids = forms.ModelMultipleChoiceField(
        queryset=OID.objects.all().order_by('cipher'),
        widget=forms.CheckboxSelectMultiple, # або forms.SelectMultiple
        label="Оберіть ОІД, які стосуються заявки",
        required=False # Якщо заявка може бути загальною без конкретних ОІД на початку
    )

    class Meta:
        model = WorkRequest
        fields = ['unit', 'incoming_number', 'incoming_date', 'oids', 'note']
        widgets = {
            'incoming_date': forms.DateInput(attrs={'type': 'date'}),
        }
        labels = {
            'unit': 'Військова частина',
            'incoming_number': 'Вхідний обліковий номер заявки',
            'incoming_date': 'Вхідна дата заявки',
            'note': 'Примітки',
        }

    # Логіка для створення WorkRequestItem після збереження WorkRequest
    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit:
            instance.save()
            # Створюємо WorkRequestItem для кожного обраного ОІД
            for oid in self.cleaned_data['oids']:
                WorkRequestItem.objects.create(
                    request=instance,
                    oid=oid,
                    work_type=WorkTypeChoices.ATTESTATION, # Або визначити через форму, який тип роботи
                    status=WorkRequestStatusChoices.PENDING
                )
        return instance

class TripForm(forms.ModelForm):
    # Тут можна додати фільтрацію для OID залежно від обраних Unit
    # Це вимагає JS на фронтенді, але для початку можна вивести всі
    oids = forms.ModelMultipleChoiceField(
        queryset=OID.objects.all().order_by('cipher'),
        widget=forms.CheckboxSelectMultiple,
        label="Оберіть ОІД, що будуть задіяні у відрядженні",
        required=False
    )
    units = forms.ModelMultipleChoiceField(
        queryset=Unit.objects.all().order_by('name'),
        widget=forms.CheckboxSelectMultiple,
        label="Військові частини призначення",
    )
    persons = forms.ModelMultipleChoiceField(
        queryset=Person.objects.filter(is_active=True).order_by('full_name'),
        widget=forms.CheckboxSelectMultiple,
        label="Особи у відрядженні",
    )
    work_requests = forms.ModelMultipleChoiceField(
        queryset=WorkRequest.objects.filter(status=WorkRequestStatusChoices.PENDING),
        widget=forms.CheckboxSelectMultiple,
        label="Пов'язані заявки (статус 'Очікує')",
        required=False
    )


    class Meta:
        model = Trip
        fields = ['start_date', 'end_date', 'units', 'oids', 'persons', 'work_requests', 'purpose']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }
        labels = {
            'start_date': 'Дата початку',
            'end_date': 'Дата завершення',
            'purpose': 'Мета відрядження',
        }

class DocumentForm(forms.ModelForm):
    # Додаємо поля, які допоможуть динамічно вибрати DocumentType
    # Це поле буде заповнюватися JavaScript'ом на фронтенді
    # або можна використовувати ModelChoiceField з queryset, який фільтрується
    # в залежності від обраних oid та work_type
    document_type_id = forms.ModelChoiceField(
        queryset=DocumentType.objects.all(),
        label="Тип документа",
        required=True,
        empty_label="Оберіть тип документа"
    )

    class Meta:
        model = Document
        fields = ['oid', 'work_request_item', 'document_type_id', 'document_number', 'process_date', 'work_date', 'author', 'note']
        widgets = {
            'process_date': forms.DateInput(attrs={'type': 'date'}),
            'work_date': forms.DateInput(attrs={'type': 'date'}),
        }
        labels = {
            'oid': 'Об’єкт інформаційної діяльності',
            'work_request_item': 'Елемент заявки (якщо документ за заявкою)',
            'document_number': 'Підготовлений № документа',
            'process_date': 'Дата опрацювання',
            'work_date': 'Дата проведення робіт',
            'author': 'Виконавець (ПІБ)',
            'note': 'Примітки',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Динамічно фільтруємо work_request_item залежно від oid
        if 'oid' in self.initial:
            oid_instance = self.initial['oid']
            self.fields['work_request_item'].queryset = WorkRequestItem.objects.filter(oid=oid_instance)
        elif self.instance.pk:
            self.fields['work_request_item'].queryset = WorkRequestItem.objects.filter(oid=self.instance.oid)
        else:
            self.fields['work_request_item'].queryset = WorkRequestItem.objects.none() # За замовчуванням пусто

        # Оптимізуємо вибір DocumentType
        # У реальному проекті тут потрібен JS, щоб фільтрувати типи документів
        # залежно від обраного OID (OIDType) та WorkType (з WorkRequestItem)
        # Наразі показуємо всі
        self.fields['document_type_id'].label_from_instance = lambda obj: f"{obj.name} ({obj.get_oid_type_display()}, {obj.get_work_type_display()})"

    def clean(self):
        cleaned_data = super().clean()
        document_type = cleaned_data.get('document_type_id')
        oid = cleaned_data.get('oid')

        if document_type and oid:
            # Тут можна додати перевірки, чи відповідає обраний DocumentType
            # типу ОІД та виду робіт (якщо потрібно).
            # Наприклад, якщо DocumentType.oid_type не 'Спільний', він має відповідати oid.oid_type
            if document_type.oid_type != 'Спільний' and document_type.oid_type != oid.oid_type:
                self.add_error('document_type_id', 'Обраний тип документа не відповідає типу ОІД.')
            
            # Якщо work_request_item обрано, можна додатково перевірити work_type
            work_request_item = cleaned_data.get('work_request_item')
            if work_request_item and document_type.work_type != 'Спільний' and document_type.work_type != work_request_item.work_type:
                self.add_error('document_type_id', 'Обраний тип документа не відповідає виду робіт в заявці.')
        return cleaned_data
    
    def save(self, commit=True):
        # Передаємо вибраний DocumentType до моделі Document
        self.instance.document_type = self.cleaned_data['document_type_id']
        return super().save(commit=commit)