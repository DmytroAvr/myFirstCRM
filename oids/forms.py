# C:\myFirstCRM\oids\forms.py

from django import forms
from django.forms import inlineformset_factory
from .models import (
    WorkRequest, WorkRequestItem, OID, Unit, Person, Trip, Document, DocumentType,
    WorkRequestStatusChoices, WorkTypeChoices, OIDTypeChoices, OIDStatusChoices, 
)
from django_tomselect.forms import TomSelectModelChoiceField, TomSelectConfig

# --- Форми для панелі керування ---

class WorkRequestForm(forms.ModelForm):
    unit = forms.ModelChoiceField(
        queryset=Unit.objects.all().order_by('code'),
        label="Військова частина",
        # Додаємо клас для ініціалізації TomSelect, якщо потрібно для цього поля
        widget=forms.Select(attrs={'class': 'form-select tomselect-main-unit'}) 
    )
    # Поля 'oids' та 'request_work_type' видалені звідси,
    # оскільки вони тепер будуть у формсеті WorkRequestItemForm

    class Meta:
        model = WorkRequest
        # 'oids' та 'request_work_type' видалені зі списку полів
        fields = ['unit', 'incoming_number', 'incoming_date', 'note'] 
        widgets = {
            'incoming_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'incoming_number': forms.TextInput(attrs={'class': 'form-control'}),
            'note': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }
        labels = {
            'unit': 'Військова частина',
            'incoming_number': 'Вхідний обліковий номер заявки',
            'incoming_date': 'Вхідна дата заявки',
            'note': 'Примітки до заявки (загальні)',
        }

    # Метод save() тепер не створює WorkRequestItem, це буде робити view через формсет
    # def save(self, commit=True):
    #     instance = super().save(commit=commit)
    #     # ... логіка створення WorkRequestItem видалена ...
    #     return instance

class WorkRequestItemForm(forms.ModelForm):
    oid = forms.ModelChoiceField(
        queryset=OID.objects.none(), # Початково порожній, заповнюється/фільтрується JS
        label="ОІД",
        widget=forms.Select(attrs={'class': 'form-select tomselect-oid-item'}), # Клас для TomSelect у формсеті
        required=True
    )
    work_type = forms.ChoiceField(
        choices=WorkTypeChoices.choices,
        label="Тип робіт для ОІД",
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=True
    )
    # Можна додати поле status, якщо його потрібно встановлювати вручну для кожного елемента
    # status = forms.ChoiceField(choices=WorkRequestStatusChoices.choices, ...)

    class Meta:
        model = WorkRequestItem
        fields = ['oid', 'work_type'] # Додайте 'status', якщо потрібно
        # widgets = {
        #     'oid': forms.Select(attrs={'class': 'form-select tomselect-oid-item'}),
        #     'work_type': forms.Select(attrs={'class': 'form-select'}),
        # }

    def __init__(self, *args, **kwargs):
        # Отримуємо екземпляр WorkRequest (батьківської заявки), якщо він є
        # Це може бути передано через form_kwargs у view при створенні формсету
        self.parent_instance_unit = kwargs.pop('parent_instance_unit', None)
        super().__init__(*args, **kwargs)

        if self.parent_instance_unit:
            self.fields['oid'].queryset = OID.objects.filter(unit=self.parent_instance_unit).order_by('cipher')
        else:
            # Якщо ВЧ ще не відома (наприклад, при першому завантаженні пустої форми),
            # queryset залишається порожнім. JS оновить опції.
            self.fields['oid'].queryset = OID.objects.none()


# Створюємо формсет для WorkRequestItem
# extra=1 означає, що за замовчуванням буде одна порожня форма для додавання
# can_delete=True додасть чекбокс для видалення існуючих елементів (при редагуванні)
WorkRequestItemFormSet = inlineformset_factory(
    WorkRequest,
    WorkRequestItem,
    form=WorkRequestItemForm,
    extra=1,
    can_delete=True,
    # min_num=1, # Якщо потрібно хоча б один елемент
    # validate_min=True,
    # fk_name=None # Django зазвичай сам знаходить ForeignKey
)

class TripForm(forms.ModelForm):
    units = forms.ModelMultipleChoiceField(
        queryset=Unit.objects.all().order_by('code'),
        label="Військові частини призначення",
        widget=forms.SelectMultiple(attrs={'class': 'form-select tomselect-field', 'id': 'id_trip_form_units'}), # Додав ID
        required=True
    )
    # Поле oids буде заповнюватися динамічно на основі обраних units
    oids = forms.ModelMultipleChoiceField(
        queryset=OID.objects.none(), # Початково порожній
        label="ОІДи, що задіяні у відрядженні (відфільтруються після вибору ВЧ)",
        widget=forms.SelectMultiple(attrs={'class': 'form-select tomselect-field', 'id': 'id_trip_form_oids'}), # Додав ID
        required=False # Може бути False, якщо ОІДи не завжди відомі одразу
    )
    persons = forms.ModelMultipleChoiceField(
        queryset=Person.objects.filter(is_active=True).order_by('full_name'),
        label="Особи у відрядженні",
        widget=forms.SelectMultiple(attrs={'class': 'form-select tomselect-field'}),
        required=True
    )
    work_requests = forms.ModelMultipleChoiceField(
        queryset=WorkRequest.objects.filter(
            status__in=[WorkRequestStatusChoices.PENDING, WorkRequestStatusChoices.IN_PROGRESS]
        ).order_by('-incoming_date'),
        label="Пов'язані заявки (статус 'Очікує' або 'В роботі')",
        widget=forms.SelectMultiple(attrs={'class': 'form-select tomselect-field'}),
        required=False
    )

    class Meta:
        model = Trip
        fields = ['start_date', 'end_date', 'units', 'oids', 'persons', 'work_requests', 'purpose']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'purpose': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }
        labels = {
            'start_date': "Дата початку відрядження",
            'end_date': "Дата завершення відрядження",
            'purpose': "Мета та примітки до відрядження",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        selected_unit_ids = []

        # Якщо форма зв'язана з даними (POST)
        if self.is_bound and 'units' in self.data:
            try:
                # self.data.getlist('units') поверне список рядкових ID
                selected_unit_ids = [int(uid) for uid in self.data.getlist('units') if uid.isdigit()]
            except (ValueError, TypeError):
                selected_unit_ids = []
        # Якщо форма не зв'язана, але є initial дані (наприклад, при редагуванні або GET з параметрами)
        elif 'units' in self.initial:
            initial_units = self.initial.get('units') # Може бути queryset або список ID
            if hasattr(initial_units, 'values_list'): # Якщо це queryset
                selected_unit_ids = list(initial_units.values_list('id', flat=True))
            elif isinstance(initial_units, list):
                selected_unit_ids = [int(uid) for uid in initial_units if str(uid).isdigit()]
        # Якщо форма для існуючого екземпляра (редагування)
        elif self.instance and self.instance.pk:
            selected_unit_ids = list(self.instance.units.all().values_list('id', flat=True))
            # Попередньо заповнюємо поле oids, якщо units вже є
            if selected_unit_ids:
                self.fields['oids'].queryset = OID.objects.filter(
                    unit__id__in=selected_unit_ids,
                    # Можна додати фільтр по статусу ОІД, наприклад, тільки активні:
                    # status__in=[OIDStatusChoices.ACTIVE, OIDStatusChoices.NEW] 
                ).distinct().order_by('unit__code', 'cipher')


        # Встановлюємо queryset для поля oids на основі обраних ВЧ (для валідації POST)
        if selected_unit_ids:
            self.fields['oids'].queryset = OID.objects.filter(
                unit__id__in=selected_unit_ids
            ).distinct().order_by('unit__code', 'cipher')
        else:
            self.fields['oids'].queryset = OID.objects.none()
            
class DocumentForm(forms.ModelForm): 
    # Поле для вибору типу документа. Фільтрація на основі OID.oid_type та work_type
    # буде реалізована через JavaScript або при ініціалізації форми у view.
    document_type = forms.ModelChoiceField(
        queryset=DocumentType.objects.all().order_by('name'),
        label="Тип документа",
        widget=forms.Select(attrs={'class': 'select2-basic'}), # Можна select2-basic для простого Select2
        empty_label="Спочатку оберіть ОІД та вид робіт"
    )
    
    # work_request_item може бути необов'язковим, якщо документ не пов'язаний з конкретним елементом заявки
    work_request_item = forms.ModelChoiceField(
        queryset=WorkRequestItem.objects.none(), # Початково порожній, заповнюється динамічно
        required=False,
        label="Елемент заявки (якщо застосовно)",
        widget=forms.Select(attrs={'class': 'select2-basic'})
    )

    class Meta:
        model = Document
        fields = [
            'oid', 'work_request_item', 'document_type', 'document_number', 
            'process_date', 'work_date', 'author', 'note', 'attachment' # Додав attachment
        ]
        widgets = {
            'oid': forms.Select(attrs={'class': 'select2-basic', 'id': 'id_document_oid'}), # ID для JS
            'process_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'work_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'author': forms.Select(attrs={'class': 'select2-basic'}),
            'note': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'document_number': forms.TextInput(attrs={'class': 'form-control'}),
            'attachment': forms.FileInput(attrs={'class': 'form-control-file'}) # Для завантаження файлу
        }
        labels = {
            'oid': "Об'єкт інформаційної діяльності",
            'document_number': "Підготовлений № документа (наприклад, 27/14-XXXX)",
            'process_date': "Дата опрацювання документа (створення)",
            'work_date': "Дата фактичного проведення робіт на ОІД",
            'author': "Автор/Виконавець документа",
            'note': "Примітки до документа",
            'attachment': "Прикріплений файл (скан-копія)"
        }

    def __init__(self, *args, **kwargs):
        # Можна передати початковий oid_id з view, щоб відфільтрувати work_request_item
        initial_oid = kwargs.pop('initial_oid', None) 
        super().__init__(*args, **kwargs)

        self.fields['author'].queryset = Person.objects.filter(is_active=True).order_by('full_name')
        
        if initial_oid:
            self.fields['oid'].initial = initial_oid
            self.fields['work_request_item'].queryset = WorkRequestItem.objects.filter(oid=initial_oid).select_related('request')
        elif self.instance and self.instance.pk and self.instance.oid:
             self.fields['work_request_item'].queryset = WorkRequestItem.objects.filter(oid=self.instance.oid).select_related('request')
        
        # Динамічне завантаження/фільтрація document_type краще реалізувати через JS,
        # що реагує на зміну OID (для отримання oid.oid_type) та WorkRequestItem (для work_type).
        # Поки що залишаємо всі типи документів.
        # Або можна фільтрувати тут, якщо work_type відомий заздалегідь.
        # Наприклад, якщо форма викликається для конкретного типу робіт
        # initial_work_type = kwargs.pop('initial_work_type', None)
        # if initial_oid and initial_work_type:
        #     self.fields['document_type'].queryset = DocumentType.objects.filter(
        #         Q(oid_type=initial_oid.oid_type) | Q(oid_type='Спільний'),
        #         Q(work_type=initial_work_type) | Q(work_type='Спільний')
        #     ).order_by('name')

    def clean_document_number(self):
        # Приклад валідації: переконатися, що номер починається з "27/14-"
        number = self.cleaned_data.get('document_number')
        if number and not number.startswith('27/14-'):
            # Можна просто додати префікс, якщо його немає
            # return f"27/14-{number}" 
            raise forms.ValidationError("Номер документа має починатися з префіксу '27/14-'.")
        return number

    def save(self, commit=True):
        instance = super().save(commit=False)
        # Автоматичне обчислення expiration_date вже є в моделі Document
        if commit:
            instance.save()
            self.save_m2m() # Якщо є ManyToMany поля
        return instance
    
class OIDForm(forms.ModelForm):
    class Meta:
        model = OID
        fields = ['unit', 'oid_type', 'cipher', 'full_name', 'room', 'status', 'sec_level', 'note']
        widgets = {
            'unit': forms.Select(attrs={'class': 'select2-basic-modal'}), # Окремий клас для Select2 в модальному вікні
            'oid_type': forms.Select(attrs={'class': 'form-control'}),
            'cipher': forms.TextInput(attrs={'class': 'form-control'}),
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'room': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'sec_level': forms.Select(attrs={'class': 'form-control'}),
            'note': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }
        labels = {
            'unit': 'Військова частина',
            'oid_type': 'Тип ОІД',
            'cipher': 'Шифр ОІД',
            'full_name': 'Повна назва ОІД',
            'room': 'Приміщення №',
            'status': 'Поточний стан ОІД',
            'sec_level': 'Гриф ОІД',
            'note': 'Примітка',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Можна відфільтрувати queryset для unit, якщо потрібно
        self.fields['unit'].queryset = Unit.objects.all().order_by('code')
        # Якщо форма відкривається з контексту заявки, де вже обрана ВЧ,
        # можна передати initial_unit_id і встановити його
        initial_unit_id = kwargs.pop('initial_unit_id', None)
        if initial_unit_id:
            self.fields['unit'].initial = initial_unit_id
