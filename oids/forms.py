# C:\myFirstCRM\oids\forms.py
from django import forms

from django.forms import inlineformset_factory, modelformset_factory, formset_factory
from .models import (OIDTypeChoices, OIDStatusChoices, SecLevelChoices, WorkRequestStatusChoices, WorkTypeChoices, 
    DocumentReviewResultChoices, AttestationRegistrationStatusChoices, PeminSubTypeChoices
)
from .models import (
    WorkRequest, WorkRequestItem, OID, DskEot , Unit, Person, Trip, TripResultForUnit, Document, DocumentType,
    AttestationRegistration, AttestationResponse, WorkCompletionRegistration, WorkCompletionResponse, 
    Declaration, DeclarationRegistration, TechnicalTask, 
)
from django_tomselect.forms import TomSelectModelChoiceField, TomSelectConfig
from django.utils import timezone
import datetime


def get_last_week_date():
    """Повертає дату 'сьогодні мінус 7 днів'."""
    todayDate = datetime.date.today() - datetime.timedelta(weeks=1)
    return todayDate.strftime("%Y-%m-%d")

# initial=datetime.date.today
# ставить дату СЬОГОДНІ

# initial=get_last_week_date
# дата СЬОГОДНІ - 1 тиждень

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
            status__in=[WorkRequestStatusChoices.PENDING]
        ).order_by('-incoming_date'),
        label="Відрядження на заявки: (статус 'Очікує')",
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
                    status__in=[
                        OIDStatusChoices.NEW,
                        OIDStatusChoices.RECEIVED_REQUEST,
                        OIDStatusChoices.RECEIVED_REQUEST_IK,
                        OIDStatusChoices.RECEIVED_REQUEST_ATTESTATION,
                        OIDStatusChoices.RECEIVED_REQUEST_PLAND_ATTESTATION,
                        OIDStatusChoices.RECEIVED_TZ,
                        OIDStatusChoices.ACTIVE,
                        OIDStatusChoices.TERMINATED,
                        OIDStatusChoices.INACTIVE    
                        ] 
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
        widget=forms.Select(attrs={'class': 'form-select tomselect-field'}), 
        empty_label="Спочатку оберіть ОІД та вид робіт"
    )
    
    # work_request_item може бути необов'язковим, якщо документ не пов'язаний з конкретним елементом заявки
    work_request_item = forms.ModelChoiceField(
        queryset=WorkRequestItem.objects.none(), # Початково порожній, заповнюється динамічно
        required=False,
        label="Елемент заявки (якщо застосовно)",
        widget=forms.Select(attrs={'class': 'form-select tomselect-field'})
    )

    class Meta:
        model = Document
        fields = [
            'oid', 'work_request_item', 'document_type', 'document_number', 
            'doc_process_date', 'work_date', 'author', 'note', 'attachment' # Додав attachment
        ]
        widgets = {
            'oid': forms.Select(attrs={'class': 'form-select tomselect-field', 'id': 'id_document_oid'}), # ID для JS
            'doc_process_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'work_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'author': forms.Select(attrs={'class': 'form-select tomselect-field'}),
            'note': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'document_number': forms.TextInput(attrs={'class': 'form-control'}),
            'attachment': forms.FileInput(attrs={'class': 'form-control-file'}) # Для завантаження файлу
        }
        labels = {
            'oid': "Об'єкт інформаційної діяльності",
            'document_number': "Підг. № документа (наприклад, 27/14-XXXX)",
            'doc_process_date': "Дата створення документа (від)",
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
    
# Форма для одного документа (буде використовуватися у формсеті)
class DocumentItemForm(forms.ModelForm):
    document_type = forms.ModelChoiceField(
        # queryset=DocumentType.objects.all().order_by('name'), # Поки що всі, потім буде фільтрація
        queryset=DocumentType.objects.all().extra(
            select={'oid_type_order': "CASE oid_type WHEN 'СПІЛЬНИЙ' THEN 1 WHEN 'ПЕМІН' THEN 2 WHEN 'МОВНА' THEN 3 ELSE 4 END"}
        ).order_by('oid_type_order', 'name'),
		label="Тип документа",
        widget=forms.Select(attrs={'class': 'form-select tomselect-doc-type'}), # Клас для JS
        required=True
    )
    document_number = forms.CharField(
        label="Підг. №",
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        initial='27/14-', # Можна встановити тут, або динамічно в JS
        required=True
    )
    note = forms.CharField(
        label="Примітки до документа",
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        required=False
    )
    

    class Meta:
        model = Document
        fields = ['document_type', 'document_number', 'note']
        # Поля oid, work_request_item, doc_process_date, work_date, author будуть з головної форми

# Головна форма для сторінки "Опрацювання документів"
class DocumentProcessingMainForm(forms.Form):
    unit = forms.ModelChoiceField(
        queryset=Unit.objects.all().order_by('code'),
        label="Військова частина",
        widget=forms.Select(attrs={'class': 'form-select tomselect-field', 'id': 'id_proc_form_unit'})
    )
    oid = forms.ModelChoiceField(
        queryset=OID.objects.none(), # Початково порожній
        label="Об'єкт інформаційної діяльності (ОІД)",
        widget=forms.Select(attrs={'class': 'form-select tomselect-field', 'id': 'id_proc_form_oid'}),
        required=True
    )
    work_request_item = forms.ModelChoiceField(
        queryset=WorkRequestItem.objects.none(), # Початково порожній
        label="Елемент заявки (якщо застосовно)",
        widget=forms.Select(attrs={'class': 'form-select tomselect-field', 'id': 'id_proc_form_work_request_item'}),
        required=False 
    )
    doc_process_date = forms.DateField(
        label="Дата опрацювання документів (підг. від)",
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        # initial=datetime.date.today,
        initial=datetime.date.today().strftime("%Y-%m-%d"),
        required=True
    )
    work_date = forms.DateField(
        label="Дата виконання робіт на ОІД (для відстежування терміну дії)",
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        initial=get_last_week_date,
        required=True
    )
    author = forms.ModelChoiceField(
        queryset=Person.objects.filter(is_active=True).order_by('full_name'),
        label="Автор/Виконавець (загальний для пакету)",
        widget=forms.Select(attrs={'class': 'form-select tomselect-field', 'id': 'id_proc_form_author'}),
        required=False
    )

    def __init__(self, *args, **kwargs):
        # Видаляємо кастомні kwargs перед викликом super().__init__
        initial_oid_instance_from_view = kwargs.pop('initial_oid', None)
        initial_wri_instance_from_view = kwargs.pop('initial_work_request_item', None) # Не використовується напряму тут
        
        super().__init__(*args, **kwargs)
        print(f"DEBUG DocumentProcessingMainForm __init__ called. Args: {args}, Kwargs: {kwargs}")
        print(f"DEBUG Form is_bound: {self.is_bound}")
        if self.is_bound:
            print(f"DEBUG Form data: {self.data}")
        
        # self.add_prefix(field_name) використовується для отримання правильного імені поля з POST, якщо форма має префікс
        # У вашому view: main_form = DocumentProcessingMainForm(request.POST, prefix='main')
        # Тому поля будуть 'main-unit', 'main-oid' і т.д.

        selected_unit_id = None
        if self.is_bound: # Обробка POST або GET з даними форми
            unit_id_from_data = self.data.get(self.add_prefix('unit'))
            print(f"DEBUG Unit ID from self.data['{self.add_prefix('unit')}']: {unit_id_from_data}")
            if unit_id_from_data and unit_id_from_data.isdigit():
                selected_unit_id = int(unit_id_from_data)
        elif initial_oid_instance_from_view: # Для GET-запиту з початковими даними з view
            if initial_oid_instance_from_view.unit:
                selected_unit_id = initial_oid_instance_from_view.unit.id
                self.fields['unit'].initial = initial_oid_instance_from_view.unit # Встановлюємо initial для поля unit
            print(f"DEBUG Unit ID from initial_oid_instance_from_view: {selected_unit_id}")
        
        # Оновлення queryset для поля ОІД
        if selected_unit_id:
            print(f"DEBUG Setting OID queryset for unit_id: {selected_unit_id}")
            self.fields['oid'].queryset = OID.objects.filter(unit_id=selected_unit_id).order_by('cipher')
        else:
            print("DEBUG No unit selected, OID queryset remains .none()")
            self.fields['oid'].queryset = OID.objects.none()

        # Встановлення initial для ОІД, якщо він був переданий з view (для GET)
        if not self.is_bound and initial_oid_instance_from_view:
             self.fields['oid'].initial = initial_oid_instance_from_view
             print(f"DEBUG Set initial OID: {initial_oid_instance_from_view.id if initial_oid_instance_from_view else 'None'}")


        # Оновлення queryset для поля Елемент Заявки (work_request_item)
        selected_oid_id_for_wri = None
        if self.is_bound:
            oid_id_from_data_for_wri = self.data.get(self.add_prefix('oid'))
            print(f"DEBUG OID ID for WRI from self.data['{self.add_prefix('oid')}']: {oid_id_from_data_for_wri}")
            if oid_id_from_data_for_wri and oid_id_from_data_for_wri.isdigit():
                selected_oid_id_for_wri = int(oid_id_from_data_for_wri)
        elif initial_oid_instance_from_view: # Для GET
            selected_oid_id_for_wri = initial_oid_instance_from_view.id
            print(f"DEBUG OID ID for WRI from initial_oid_instance_from_view: {selected_oid_id_for_wri}")

        if selected_oid_id_for_wri:
            print(f"DEBUG Setting WRI queryset for oid_id: {selected_oid_id_for_wri}")
            self.fields['work_request_item'].queryset = WorkRequestItem.objects.filter(
                oid_id=selected_oid_id_for_wri
            ).select_related('request').order_by('-request__incoming_date')
        else:
            print("DEBUG No OID selected for WRI, WRI queryset remains .none()")
            self.fields['work_request_item'].queryset = WorkRequestItem.objects.none()
        
        # Встановлення initial для WorkRequestItem, якщо він був переданий з view (для GET)
        # і належить до initial_oid_instance_from_view
        if not self.is_bound and initial_wri_instance_from_view:
            if initial_oid_instance_from_view and initial_wri_instance_from_view.oid == initial_oid_instance_from_view:
                self.fields['work_request_item'].initial = initial_wri_instance_from_view
                print(f"DEBUG Set initial WRI: {initial_wri_instance_from_view.id if initial_wri_instance_from_view else 'None'}")
            else:
                print("DEBUG Initial WRI not set because its OID doesn't match initial_oid_instance_from_view.")
                
# Створюємо формсет для DocumentItemForm
# extra=1 - одна порожня форма за замовчуванням
DocumentItemFormSet = formset_factory(DocumentItemForm, extra=1, can_delete=True)

# end end new form for documents

# --- Форма для створення "Відправки на реєстрацію" ---
class AttestationRegistrationSendForm(forms.ModelForm):
    # 1. Поле для вибору ВІЙСЬКОВИХ ЧАСТИН (множинний вибір)
    selected_units = forms.ModelMultipleChoiceField(
        queryset=Unit.objects.all().order_by('code'),
        label="1. Оберіть Військові Частини",
        widget=forms.SelectMultiple(attrs={'class': 'form-select tomselect-field', 'id': 'id_att_reg_send_units_selector'}),
        required=True,
        help_text="Оберіть одну або декілька ВЧ, ОІДи яких потрібно обробити."
    )
    
    # 2. Поле для вибору ОІДІВ (множинний вибір, залежить від selected_units)
    selected_oids = forms.ModelMultipleChoiceField(
        queryset=OID.objects.none(), # Заповнюється динамічно JS
        label="2. Оберіть ОІДи",
        widget=forms.SelectMultiple(attrs={'class': 'form-select tomselect-field', 'id': 'id_att_reg_send_oids_selector'}),
        required=True,
        help_text="Оберіть ОІДи з попередньо обраних ВЧ."
    )

    # 3. Поле для вибору АКТІВ АТЕСТАЦІЇ (множинний вибір, залежить від selected_oids)
    attestation_acts_to_send = forms.ModelMultipleChoiceField(
        queryset=Document.objects.none(), # Заповнюється динамічно JS
        label="3. Оберіть Акти Атестації для відправки",
        widget=forms.SelectMultiple(attrs={'class': 'form-select tomselect-field', 'id': 'id_att_reg_send_acts_selector', 'size': '10'}),
        required=True,
        help_text="Оберіть акти, які ще не були відправлені."
    )

    class Meta:
        model = AttestationRegistration
        fields = [
            'outgoing_letter_number', 
            'outgoing_letter_date', 
            'sent_by', 
            # Поля 'selected_units' та 'selected_oids' є допоміжними для фільтрації,
            # вони не є полями моделі AttestationRegistration.
            # Поле 'units' (ManyToMany з моделі) буде заповнене у save()
            'note', 
            # 'attachment' видалено з моделі
        ]
        widgets = {
            'outgoing_letter_number': forms.TextInput(attrs={'class': 'form-control'}),
            'outgoing_letter_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'sent_by': forms.Select(attrs={'class': 'form-select tomselect-field'}),
            'note': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }
        labels = {
            'outgoing_letter_number': "Вихідний номер супровідного листа",
            'outgoing_letter_date': "Дата вихідного супровідного листа",
            'sent_by': "Хто відправив (підготував лист)",
            'note': "Примітки до відправки",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        print(f"DEBUG AttestationRegSendForm __init__. is_bound: {self.is_bound}")
        if self.is_bound:
            print(f"DEBUG AttestationRegSendForm DATA: {self.data}")
            
            # Встановлюємо queryset для selected_oids на основі POST-даних selected_units
            unit_ids_from_data = self.data.getlist(self.add_prefix('selected_units'))
            if unit_ids_from_data:
                valid_unit_ids = [int(uid) for uid in unit_ids_from_data if uid.isdigit()]
                if valid_unit_ids:
                    self.fields['selected_oids'].queryset = OID.objects.filter(unit_id__in=valid_unit_ids).order_by('unit__code', 'cipher')
                    print(f"DEBUG AttestationRegSendForm (POST): OID queryset set for unit_ids: {valid_unit_ids}")

            # Встановлюємо queryset для attestation_acts_to_send на основі POST-даних selected_oids
            oid_ids_from_data = self.data.getlist(self.add_prefix('selected_oids'))
            if oid_ids_from_data:
                valid_oid_ids = [int(oid_id) for oid_id in oid_ids_from_data if oid_id.isdigit()]
                if valid_oid_ids:
                    document_type_act_att = DocumentType.objects.filter(name__icontains="Акт атестації").first() # Ваш спосіб ідентифікації "Акту атестації"
                    # document_type_act_att = DocumentType.objects.filter(duration_months=60).first() # Ваш спосіб ідентифікації "Акту атестації"
                    # attestation_act_type = DocumentType.objects.get(name__icontains="Акт атестації")
                    if document_type_act_att:
                        self.fields['attestation_acts_to_send'].queryset = Document.objects.filter(
                            oid_id__in=valid_oid_ids,
                            document_type=document_type_act_att,
                            attestation_registration_sent__isnull=True
                        ).order_by('oid__cipher', '-work_date')
                        print(f"DEBUG AttestationRegSendForm (POST): Acts queryset set for oid_ids: {valid_oid_ids}")
        # Для GET запитів querysets для selected_oids та attestation_acts_to_send залишаються .none(),
        # оскільки вони заповнюються JavaScript.

    def save(self, commit=True):
        # Спершу зберігаємо сам об'єкт AttestationRegistration з основними даними
        registration_instance = super().save(commit=False) 
        
        if commit:
            registration_instance.save() # Зберігаємо, щоб отримати ID

            selected_acts = self.cleaned_data.get('attestation_acts_to_send', [])
            units_involved = set()
            
            for act_document in selected_acts:
                act_document.attestation_registration_sent = registration_instance
                # Можливо, тут потрібно оновити статус самого документа (наприклад, "відправлено на реєстрацію")
                # act_document.some_status_field = 'sent_for_registration' 
                act_document.save(update_fields=['attestation_registration_sent', 'updated_at']) # Додайте 'some_status_field', якщо є
                
                if act_document.oid and act_document.oid.unit:
                    units_involved.add(act_document.oid.unit)
            
            if units_involved:
                registration_instance.units.set(list(units_involved))
            else:
                registration_instance.units.clear()
            
            # self.save_m2m() тут не потрібен, оскільки 'units' обробляється вручну,
            # а 'attestation_acts_to_send' - це не поле моделі, а допоміжне поле форми.
        
        return registration_instance
# --- Форма для внесення даних з "Відповіді ДССЗЗІ" ---


# Це буде головна форма
class AttestationResponseMainForm(forms.ModelForm):
    # Поле для вибору існуючої Відправки, на яку прийшла відповідь
    attestation_registration_sent = forms.ModelChoiceField(
        queryset=AttestationRegistration.objects.filter(
            status=AttestationRegistrationStatusChoices.SENT # Тільки ті, що очікують відповіді
        ).order_by('-outgoing_letter_date'),
        label="Вихідний лист (відправка), на який отримано відповідь",
        widget=forms.Select(attrs={'class': 'form-select tomselect-field', 'id': 'id_response_for_registration_sent'})
    )

    class Meta:
        model = AttestationResponse
        fields = [
            'attestation_registration_sent', 
            'response_letter_number', 
            'response_letter_date', 
            'received_by',
            'note', 
            
        ]
        widgets = {
            'response_letter_number': forms.TextInput(attrs={'class': 'form-control'}),
            'response_letter_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'received_by': forms.Select(attrs={'class': 'form-select tomselect-field'}),
            'note': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }

# Форма для ОНОВЛЕННЯ окремого Акту Атестації (буде використовуватися у формсеті)
# Ми не створюємо новий Document, а оновлюємо існуючий
class AttestationActUpdateForm(forms.ModelForm):
    # Поля, які користувач буде заповнювати для кожного акту з відповіді ДССЗЗІ
    dsszzi_registered_number = forms.CharField(
        label="Присвоєний № реєстрації ДССЗЗІ", 
        required=False, # Може бути не для всіх актів
        widget=forms.TextInput(attrs={'class': 'form-control form-control-sm'})
    )
    dsszzi_registered_date = forms.DateField(
        label="Дата реєстрації ДССЗЗІ", 
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control form-control-sm'}),
        initial=get_last_week_date
    )
    # Можна додати поле для коментаря/статусу саме цього акту з відповіді, якщо потрібно

    class Meta:
        model = Document # Ми оновлюємо існуючі документи
        fields = ['dsszzi_registered_number', 'dsszzi_registered_date']
        # Ми не хочемо, щоб користувач міг змінювати сам документ тут, тільки його реєстраційні дані.
        # Тому інші поля Document не включаємо.

# Формсет для оновлення Актів Атестації
# Ми будемо використовувати modelformset_factory, оскільки ми працюємо з існуючими об'єктами Document
AttestationActUpdateFormSet = modelformset_factory(
    Document,                                     # Модель
    form=AttestationActUpdateForm,                # Форма для кожного елемента
    extra=0,                                      # Не додавати порожніх форм за замовчуванням
    can_delete=False,                             # Не дозволяти видаляти документи з цієї форми
    edit_only=True                                # Тільки редагування, не створення нових
)


# ========================================================
# 
# AZR AZR AZR  відповідь
# 
# ========================================================

class WorkCompletionSendForm(forms.ModelForm):
    """
    Основна форма для сторінки "Відправка АЗР на реєстрацію".
    Збирає дані про супровідний лист та обирає ОІДи.
    """
    # Поле для вибору кількох військових частин, щоб відфільтрувати ОІДи
    units = forms.ModelMultipleChoiceField(
        queryset=Unit.objects.all().order_by('code'),
        label="1. Оберіть військові частини",
        widget=forms.SelectMultiple(attrs={'class': 'tomselect-field'}),
        required=True
    )
    
    # Поле для вибору ОІДів, queryset якого буде оновлюватися через AJAX
    oids = forms.ModelMultipleChoiceField(
        queryset=OID.objects.none(), # Починаємо з порожнього
        label="2. Оберіть ОІДи для створення АЗР",
        widget=forms.SelectMultiple(attrs={'class': 'tomselect-field'}),
        required=True
    )

    class Meta:
        model = WorkCompletionRegistration
        # Поля з моделі "конверта"
        fields = ['outgoing_letter_number', 'outgoing_letter_date', 'note']
        labels = {
            'outgoing_letter_number': "3. Вихідний номер супровідного листа",
            'outgoing_letter_date': "4. Дата вихідного листа",
            'note': "5. Примітки до відправки"
        }
        widgets = {        
			'outgoing_letter_number': forms.TextInput(attrs={'class': 'form-control'}),
			'outgoing_letter_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
			'note': forms.Textarea(attrs={'rows': 1, 'class': 'form-control'}),

        }



class WorkCompletionResponseForm(forms.ModelForm):
    """
    Основна форма для сторінки "Внесення відповіді по АЗР".
    Збирає дані про лист-відповідь.
    """
    class Meta:
        model = WorkCompletionResponse
        fields = ['response_letter_number', 'response_letter_date', 'note']
        labels = {
            'response_letter_number': "Номер листа-відповіді від ДССЗЗІ",
            'response_letter_date': "Дата листа-відповіді",
            'note': "Примітки до відповіді"
        }

        widgets = {
            'response_letter_number': forms.DateInput(attrs={'class': 'form-control'}),
            'response_letter_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'note': forms.Textarea(attrs={'rows': 1, 'class': 'form-control'})
        }



# ========================================================
# 
# AZR AZR AZR 
# 
# ========================================================

# Форма для "шапки" сторінки - дані супровідного листа
class AzrSubmissionForm(forms.Form):
    outgoing_letter_number = forms.CharField(label="Вихідний номер супровідного листа", widget=forms.DateInput(attrs={'class': 'form-control'}), max_length=50, required=True)
    outgoing_letter_date = forms.DateField(label="Дата вихідного листа", widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}), required=True, initial=get_last_week_date)
    note = forms.CharField(label="Примітки до відправки", widget=forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'твій текст', 'rows': 2}), required=False)

# Форма для одного рядка в нашому динамічному списку.
# Вона не прив'язана до моделі, бо ми створюємо об'єкти вручну.
class AzrItemForm(forms.Form):
    oid = forms.IntegerField(widget=forms.HiddenInput()) # Приховане поле для ID ОІДа
    prepared_number = forms.CharField(label="Підготовлений № АЗР", widget=forms.DateInput(attrs={'class': 'form-control'}), max_length=50, required=True)
    prepared_date = forms.DateField(label="Дата опрацювання АЗР", widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}), required=True, initial=get_last_week_date)

# Створюємо FormSet на основі нашої форми для одного рядка
AzrItemFormSet = forms.formset_factory(AzrItemForm, extra=0)


# ========================================================
# 
# AZR AZR AZR 
# 
# ========================================================


class AzrUpdateForm(forms.ModelForm):
    """
    Форма для ОДНОГО рядка в таблиці на сторінці відповіді.
    Дозволяє внести реєстраційні дані для конкретного АЗР.
    """
    class Meta:
        model = Document
        # Поля, які користувач може редагувати
        fields = ['dsszzi_registered_number', 'dsszzi_registered_date']
        labels = {
            'dsszzi_registered_number': "Зареєстрований №",
            'dsszzi_registered_date': "Дата реєстрації"
        }
        widgets = {
            'dsszzi_registered_number': forms.DateInput(attrs={'class': 'form-control'}),
            'dsszzi_registered_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
        }

# Створюємо формсет на основі нашої форми для одного рядка
AzrUpdateFormSet = forms.modelformset_factory(
    Document,
    form=AzrUpdateForm,
    extra=0 # Не показувати порожніх форм для додавання
)

# --- ФОРМИ ДЛЯ ПРОЦЕСУ РЕЄСТРАЦІЇ ДЕКЛАРАЦІЙ ---


class DeclarationSubmissionForm(forms.ModelForm):
    """
    Форма для даних супровідного листа ("шапки" сторінки відправки).
    Працює з об'єднаною моделлю DeclarationRegistration.
    """
    class Meta:
        model = DeclarationRegistration
        # Вказуємо тільки ті поля, що стосуються ВІДПРАВКИ
        fields = ['outgoing_letter_number', 'outgoing_letter_date', 'note']
        labels = {
            'outgoing_letter_number': "Вихідний номер супровідного листа",
            'outgoing_letter_date': "Дата вихідного листа",
            'note': "Примітки до відправки"
        }
        widgets = {
            'outgoing_letter_number': forms.TextInput(attrs={'class': 'form-control'}),
            'outgoing_letter_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'note': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
        }


class DskEotItemForm(forms.ModelForm):
    """
    Форма для створення ОДНОГО об'єкта ДСК ЕОТ.
    Використовується як шаблон у нашому динамічному формсеті.
    """
    # Додаємо поля для створення пов'язаної Декларації
    prepared_number = forms.CharField(label="Підготовлений № Декларації",widget=forms.DateInput(attrs={'class': 'form-control'}), required=True)
    prepared_date = forms.DateField(label="Дата опрацювання", widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}), required=True, initial=get_last_week_date)
    
    class Meta:
        model = DskEot
        # Поля, які користувач заповнює для кожного ЕОТ
        fields = ['unit', 'cipher', 'serial_number', 'inventory_number', 'room']
        # Поле 'unit' буде прихованим, оскільки воно визначається блоком, в якому знаходиться форма
        widgets = {
            'unit': forms.HiddenInput(),
            
			'cipher': forms.TextInput(attrs={'class': 'form-control'}),
			'serial_number': forms.TextInput(attrs={'class': 'form-control'}),
			'inventory_number': forms.TextInput(attrs={'class': 'form-control'}),
			'room': forms.TextInput(attrs={'class': 'form-control'}),

        }

# Створюємо FormSet на основі нашої форми. `formset_factory` краще підходить,
# оскільки ми створюємо об'єкти двох різних моделей (DskEot та Declaration).
DeclarationItemFormSet = forms.formset_factory(DskEotItemForm, extra=0)


class DeclarationResponseForm(forms.ModelForm):
    """
    Форма для внесення даних про лист-відповідь.
    Працює з тими ж полями моделі DeclarationRegistration, що стосуються відповіді.
    """
    class Meta:
        model = DeclarationRegistration
        # Вказуємо тільки ті поля, що стосуються ВІДПОВІДІ
        fields = ['response_letter_number', 'response_letter_date', 'response_note']
        labels = {
            'response_letter_number': "Номер листа-відповіді від ДССЗЗІ",
            'response_letter_date': "Дата листа-відповіді",
            'response_note': "Примітки до відповіді"
        }
        widgets = {
             'response_letter_number': forms.TextInput(attrs={'class': 'form-control'}),
             'response_letter_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
             'response_note': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
        }


class DeclarationUpdateForm(forms.ModelForm):
    """
    Форма для ОДНОГО рядка в таблиці на сторінці відповіді.
    Дозволяє внести реєстраційні дані для конкретної Декларації.
    """
    class Meta:
        model = Declaration
        fields = ['registered_number', 'registered_date']
        labels = {
            'registered_number': "Зареєстрований №",
            'registered_date': "Дата реєстрації"
        }
        widgets = {
                
			'registered_number': forms.TextInput(attrs={'class': 'form-control'}),
			'registered_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),

        }

# Створюємо modelformset, який буде працювати з моделлю Declaration
DeclarationUpdateFormSet = forms.modelformset_factory(
    Declaration,
    form=DeclarationUpdateForm,
    extra=0 # Не показувати порожніх форм
)

# --- КІНЕЦЬ ФОРМИ ДЛЯ ПРОЦЕСУ РЕЄСТРАЦІЇ ДЕКЛАРАЦІЙ ---


ALLOWED_STATUS_CHOICES = [
    # було 
    # (OIDStatusChoices.CANCELED, OIDStatusChoices.CANCELED.label),
    # (OIDStatusChoices.TERMINATED, OIDStatusChoices.TERMINATED.label),
    # (OIDStatusChoices.ACTIVE, OIDStatusChoices.ACTIVE.label),
    (OIDStatusChoices.NEW, OIDStatusChoices.NEW.label),
    (OIDStatusChoices.RECEIVED_TZ, OIDStatusChoices.RECEIVED_TZ.label),
    (OIDStatusChoices.RECEIVED_TZ_REPEAT, OIDStatusChoices.RECEIVED_TZ_REPEAT.label),
    (OIDStatusChoices.RECEIVED_TZ_APPROVE, OIDStatusChoices.RECEIVED_TZ_APPROVE.label),
    (OIDStatusChoices.RECEIVED_REQUEST_ATTESTATION, OIDStatusChoices.RECEIVED_REQUEST_ATTESTATION.label),
    (OIDStatusChoices.RECEIVED_REQUEST_IK, OIDStatusChoices.RECEIVED_REQUEST_IK.label),
    (OIDStatusChoices.RECEIVED_REQUEST_PLAND_ATTESTATION, OIDStatusChoices.RECEIVED_REQUEST_PLAND_ATTESTATION.label),
    (OIDStatusChoices.ATTESTED, OIDStatusChoices.ATTESTED.label),
    (OIDStatusChoices.AZR_SEND, OIDStatusChoices.AZR_SEND.label),
    (OIDStatusChoices.RECEIVED_DECLARATION, OIDStatusChoices.RECEIVED_DECLARATION.label),
    (OIDStatusChoices.ACTIVE, OIDStatusChoices.ACTIVE.label),
    (OIDStatusChoices.TERMINATED, OIDStatusChoices.TERMINATED.label),
    (OIDStatusChoices.CANCELED, OIDStatusChoices.CANCELED.label),
]

class OIDStatusUpdateForm(forms.Form):
    unit = forms.ModelChoiceField(
        queryset=Unit.objects.all().order_by('code'),
        label="Військова частина",
        widget=forms.Select(attrs={'class': 'form-select tomselect-field', 'id': 'id_status_update_unit'}),
        empty_label="Оберіть ВЧ..."
    )
    oid = forms.ModelChoiceField(
        queryset=OID.objects.none(), # Заповнюється динамічно
        label="Об'єкт інформаційної діяльності (ОІД)",
        widget=forms.Select(attrs={'class': 'form-select tomselect-field', 'id': 'id_status_update_oid'}),
        empty_label="Спочатку оберіть ВЧ..."
    )
    # Поточний статус буде відображатися окремо, не як поле форми для зміни
    new_status = forms.ChoiceField(
        choices=ALLOWED_STATUS_CHOICES,
        label="Новий статус ОІД",
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=True
    )
    reason = forms.CharField(
        label="Причина зміни статусу (Обов'язково)",
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        required=True
    )
    
    # Поля для документа, що ініціює зміну (якщо є)
    # Ці поля не будуть напряму створювати об'єкт Document, 
    # а будуть використані для заповнення полів в OIDStatusChange або для пошуку існуючого документа.
    # Для простоти, поки що це будуть текстові поля. Потім можна розширити до вибору документа.
    initiating_document_number = forms.CharField(
        label="Вх. номер документа-ініціатора",
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        required=False
    )
    initiating_document_date = forms.DateField(
        label="Дата вх. документа-ініціатора",
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        required=False
    )

    changed_by = forms.ModelChoiceField(
        queryset=Person.objects.filter(is_active=True).order_by('full_name'),
        label="Хто змінив статус (виконавець)",
        widget=forms.Select(attrs={'class': 'form-select tomselect-field', 'id': 'id_status_update_changed_by'}),
        required=False # Буде заповнюватися автоматично в майбутньому
    )

    def __init__(self, *args, **kwargs):
        # Можливість передати початкові unit_id або oid_id з view
        initial_unit_id = kwargs.pop('initial_unit_id', None)
        initial_oid_id = kwargs.pop('initial_oid_id', None)
        
        super().__init__(*args, **kwargs)

        if initial_unit_id:
            self.fields['unit'].initial = initial_unit_id
            self.fields['oid'].queryset = OID.objects.filter(unit_id=initial_unit_id).order_by('cipher')
            if initial_oid_id:
                self.fields['oid'].initial = initial_oid_id
        
        # Якщо форма обробляє POST-дані, оновлюємо queryset для OID для валідації
        if self.is_bound and 'unit' in self.data:
            unit_id_from_data = self.data.get('unit')
            if unit_id_from_data and unit_id_from_data.isdigit():
                self.fields['oid'].queryset = OID.objects.filter(unit_id=int(unit_id_from_data)).order_by('cipher')

    def clean(self):
        cleaned_data = super().clean()
        oid_instance = cleaned_data.get('oid')
        new_status_val = cleaned_data.get('new_status')

        if oid_instance and new_status_val:
            if oid_instance.status == new_status_val:
                self.add_error('new_status', f"ОІД вже має статус '{oid_instance.get_status_display()}'. Оберіть інший статус.")
        
        # Тут можна додати іншу логіку валідації, якщо потрібно
        return cleaned_data
    
class TripResultSendForm(forms.ModelForm):
    trip = forms.ModelChoiceField(
        queryset=Trip.objects.order_by('-start_date'), # Можна додати фільтр, наприклад, тільки завершені відрядження
        label="1. Оберіть Відрядження",
        widget=forms.Select(attrs={'class': 'form-select tomselect-field', 'id': 'id_trip_result_trip'}),
        empty_label="Оберіть відрядження...",
        help_text="Відрядження, результати опрацювання якого (документи) відправляються."
    )
    
    # Це поле буде заповнюватися динамічно на основі обраного відрядження
    units_in_trip = forms.ModelMultipleChoiceField(
        queryset=Unit.objects.none(), 
        label="2. Оберіть Військові Частини з відрядження",
        widget=forms.SelectMultiple(attrs={'class': 'form-select tomselect-field', 'id': 'id_trip_result_units'}),
        required=True,
        help_text="ВЧ, до яких будуть направлені результати."
    )

    # Це поле буде заповнюватися динамічно на основі обраного відрядження та ВЧ
    oids_in_trip_units = forms.ModelMultipleChoiceField(
        queryset=OID.objects.none(),
        label="3. Оберіть ОІДи з обраних ВЧ (учасники відрядження)",
        widget=forms.SelectMultiple(attrs={'class': 'form-select tomselect-field', 'id': 'id_trip_result_oids'}),
        required=True,
        help_text="ОІДи, для яких готуються документи."
    )

    # Це поле буде заповнюватися динамічно на основі обраних ОІДів та логіки (ІК/Атестація)
    documents_to_send = forms.ModelMultipleChoiceField(
        queryset=Document.objects.none(),
        label="4. Документи для відправки",
        widget=forms.SelectMultiple(attrs={'class': 'form-select tomselect-field', 'id': 'id_trip_result_documents', 'size': '10'}),
        required=True,
        help_text="Оберіть документи. Список залежить від типу робіт та статусу реєстрації Актів Атестації."
    )

    class Meta:
        model = TripResultForUnit
        fields = [
            'trip', 
            # 'units', # поле 'units' в TripResultForUnit буде заповнено з 'units_in_trip'
            # 'oids',  # поле 'oids' в TripResultForUnit буде заповнено з 'oids_in_trip_units'
            # 'documents', # поле 'documents' в TripResultForUnit буде заповнено з 'documents_to_send'
			
			'outgoing_letter_number', 
            'outgoing_letter_date', 
            'note',             
        ]
        widgets = {
            'outgoing_letter_number': forms.TextInput(attrs={'class': 'form-control'}),
            'outgoing_letter_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'note': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
        }
        labels = {
            'outgoing_letter_number': "Вихідний номер супровідного листа",
            'outgoing_letter_date': "Дата вихідного супровідного листа",            
            'note': "Примітки до відправки результатів",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Якщо форма обробляє POST-дані, потрібно встановити querysets для валідації
        if self.is_bound:
            print(f"DEBUG TripResultSendForm (is_bound) DATA: {self.data}")
            trip_id_from_data = self.data.get(self.add_prefix('trip'))
            selected_trip = None
            if trip_id_from_data and trip_id_from_data.isdigit():
                try:
                    selected_trip = Trip.objects.prefetch_related('units', 'oids').get(pk=int(trip_id_from_data))
                except Trip.DoesNotExist:
                    pass
            
            if selected_trip:
                # Встановлюємо queryset для units_in_trip
                self.fields['units_in_trip'].queryset = selected_trip.units.all().order_by('code')
                print(f"DEBUG TripResultSendForm (is_bound) Units queryset for trip {selected_trip.id} set.")

                # Встановлюємо queryset для oids_in_trip_units
                unit_ids_from_data = self.data.getlist(self.add_prefix('units_in_trip'))
                valid_unit_ids = [int(uid) for uid in unit_ids_from_data if uid.isdigit()]
                if valid_unit_ids:
                    self.fields['oids_in_trip_units'].queryset = selected_trip.oids.filter(unit_id__in=valid_unit_ids).distinct().order_by('unit__code', 'cipher')
                    print(f"DEBUG TripResultSendForm (is_bound) OIDs queryset for trip {selected_trip.id} and units {valid_unit_ids} set.")

                    # Встановлюємо queryset для documents_to_send
                    oid_ids_from_data = self.data.getlist(self.add_prefix('oids_in_trip_units'))
                    valid_oid_ids = [int(oid_id) for oid_id in oid_ids_from_data if oid_id.isdigit()]
                    if valid_oid_ids:
                        # Ця логіка має точно відтворювати те, що JS показує користувачу
                        # Потрібно отримати work_type для цих ОІДів в контексті цього відрядження
                        # Це може бути складно зробити тут без додаткових даних.
                        # Простіше покластися на те, що JS передасть валідні ID документів.
                        # Для валідації, queryset може бути ширшим, але включати ті, що могли бути обрані.
                        self.fields['documents_to_send'].queryset = Document.objects.filter(oid_id__in=valid_oid_ids).select_related('document_type', 'oid')
                        print(f"DEBUG TripResultSendForm (is_bound) Documents queryset broadly set for OIDs {valid_oid_ids}.")
                else:
                     self.fields['oids_in_trip_units'].queryset = OID.objects.none()
                     self.fields['documents_to_send'].queryset = Document.objects.none()
            else:
                self.fields['units_in_trip'].queryset = Unit.objects.none()
                self.fields['oids_in_trip_units'].queryset = OID.objects.none()
                self.fields['documents_to_send'].queryset = Document.objects.none()
        else: # Для GET запиту
             self.fields['units_in_trip'].queryset = Unit.objects.none()
             self.fields['oids_in_trip_units'].queryset = OID.objects.none()
             self.fields['documents_to_send'].queryset = Document.objects.none()


    def save(self, commit=True):
        # Викликаємо стандартний метод save(), але поки не зберігаємо в базу (commit=False)
        instance = super().save(commit=False)
        
        # Ми зберігаємо екземпляр тільки якщо commit=True
        if commit:
            # Спочатку зберігаємо основний об'єкт TripResultForUnit, щоб він отримав свій ID
            instance.save()
            
            # Тепер, коли об'єкт існує, ми можемо встановити ManyToMany зв'язки.
            # `self.cleaned_data` містить валідовані дані з форми.
            selected_units = self.cleaned_data.get('units_in_trip')
            if selected_units:
                instance.units.set(selected_units)

            selected_oids = self.cleaned_data.get('oids_in_trip_units')
            if selected_oids:
                instance.oids.set(selected_oids)
            
            selected_documents = self.cleaned_data.get('documents_to_send')
            if selected_documents:
                instance.documents.set(selected_documents)
        
        return instance
     
class TechnicalTaskCreateForm(forms.ModelForm):
    unit = forms.ModelChoiceField(
        queryset=Unit.objects.all().order_by('code'),
        label="1. Військова частина",
        widget=forms.Select(attrs={'class': 'form-select tomselect-field', 'id': 'id_tt_create_unit'}),
        empty_label="Оберіть ВЧ..."
    )
    # Поле oid буде ModelChoiceField, але його queryset оновлюється динамічно
    oid = forms.ModelChoiceField(
        queryset=OID.objects.none(), 
        label="2. Об'єкт інформаційної діяльності (ОІД)",
        widget=forms.Select(attrs={'class': 'form-select tomselect-field', 'id': 'id_tt_create_oid'}),
        empty_label="Спочатку оберіть ВЧ...",
        required=True
    )

    class Meta:
        model = TechnicalTask
        fields = [
            # 'unit' не є полем моделі TechnicalTask, він для фільтрації OID
            'oid', 'input_number', 'input_date', 
            'read_till_date', 'note'
            # Поля reviewed_by та review_result будуть встановлені пізніше або матимуть default
        ]
        widgets = {
            'input_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'read_till_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'input_number': forms.TextInput(attrs={'class': 'form-control'}),
            'note': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        initial_unit_id = kwargs.pop('initial_unit_id', None)
        initial_oid_id = kwargs.pop('initial_oid_id', None)
        super().__init__(*args, **kwargs)

        if initial_unit_id:
            self.fields['unit'].initial = initial_unit_id
            self.fields['oid'].queryset = OID.objects.filter(unit_id=initial_unit_id).order_by('cipher')
            if initial_oid_id:
                self.fields['oid'].initial = initial_oid_id
        
        if self.is_bound:
            unit_id_from_data = self.data.get(self.add_prefix('unit'))
            if unit_id_from_data and unit_id_from_data.isdigit():
                self.fields['oid'].queryset = OID.objects.filter(unit_id=int(unit_id_from_data)).order_by('cipher')

# Доступні статуси для форми опрацювання
PROCESS_STATUS_CHOICES = [
    (DocumentReviewResultChoices.AWAITING_DOCS, DocumentReviewResultChoices.AWAITING_DOCS.label),
    (DocumentReviewResultChoices.APPROVED, DocumentReviewResultChoices.APPROVED.label),
    (DocumentReviewResultChoices.FOR_REVISION, DocumentReviewResultChoices.FOR_REVISION.label),
]


class TechnicalTaskProcessForm(forms.ModelForm):
    # Поле для вибору ТЗ, яке потрібно опрацювати
    technical_task_to_process = forms.ModelChoiceField(
        queryset=TechnicalTask.objects.filter(review_result=DocumentReviewResultChoices.READ).select_related('oid__unit').order_by('-input_date'),
        label="1. Оберіть Технічне Завдання для опрацювання (статус 'Опрацювати')",
        widget=forms.Select(attrs={'class': 'form-select tomselect-field', 'id': 'id_tt_process_task_select'}),
        empty_label="Оберіть ТЗ...",
        required=True
    )
    
    # Поле для вибору нового статусу
    new_review_result = forms.ChoiceField(
        choices=PROCESS_STATUS_CHOICES,
        label="2. Встановіть новий результат опрацювання",
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=True
    )
    
    # Поле "Хто опрацював" (reviewed_by)
    # reviewed_by вже є в моделі, але ми можемо його тут перевизначити, якщо потрібно
    # Якщо залишити як є в моделі, то у view при збереженні ми його оновимо.
    # Для простоти, припустимо, що reviewed_by буде заповнюватися у view.
    # Або можна додати його сюди:
    processed_by = forms.ModelChoiceField(
        queryset=Person.objects.filter(is_active=True).order_by('full_name'),
        label="3. Хто опрацював",
        widget=forms.Select(attrs={'class': 'form-select tomselect-field', 'id': 'id_tt_process_processed_by'}),
        required=True # Або False, якщо може бути автоматично
    )
    
    processing_note = forms.CharField(
        label="4. Примітка до опрацювання/відправки (опційно)",
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        required=False
    )
    # Поля для "вихідного номера та дати" ТЗ, якщо вони потрібні окремо.
    # Якщо "відправка" ТЗ означає просто зміну його статусу та додавання reviewed_by,
    # то ці поля можуть бути не потрібні або їх значення можна вносити в 'processing_note'.
    # outgoing_number = forms.CharField(label="Вихідний номер (якщо є)", required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    # outgoing_date = forms.DateField(label="Дата вихідного (якщо є)", required=False, widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))


    class Meta:
        model = TechnicalTask # Ми оновлюємо існуючий TechnicalTask
        # Поля, які ми дозволяємо редагувати через цю форму (крім вибору самого ТЗ)
        fields = [] # Жодних полів моделі напряму не редагуємо тут, все через кастомні поля

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Можна відфільтрувати queryset для technical_task_to_process, якщо потрібно (наприклад, за користувачем)
        # self.fields['technical_task_to_process'].queryset = ...

class OIDCreateForm(forms.ModelForm):
    # Додаємо поле `unit` для вибору ВЧ, оскільки воно є ForeignKey у моделі OID
    unit = forms.ModelChoiceField(
        queryset=Unit.objects.all().order_by('code'),
        label="Військова частина",
        widget=forms.Select(attrs={'class': 'form-select tomselect-field'}), # Клас для TomSelect
        empty_label="Оберіть ВЧ..."
    )

    class Meta:
        model = OID
        # Включаємо всі поля, які користувач має заповнити
        fields = [
            'unit', 'oid_type', 'cipher', 'full_name', 'room', 
            'sec_level', 'status', 
            # Додаємо специфічні для ПЕМІН поля
            'pemin_sub_type', 'serial_number', 'inventory_number',
            'note'
        ]
        
        # Додаємо словник help_texts
        help_texts = {
            'cipher': 'Шифр ОІД має бути !унікальним. --- Порада: додайте номер військової частини після шифру. ОЧ 3001, КЧ 3002 ...',
        }
        
        widgets = {
            'oid_type': forms.Select(attrs={'class': 'form-select'}),
            'cipher': forms.TextInput(attrs={'class': 'form-control'}),
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'room': forms.TextInput(attrs={'class': 'form-control'}),
            'sec_level': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'pemin_sub_type': forms.Select(attrs={'class': 'form-select'}), # Для підтипу теж select
            'serial_number': forms.TextInput(attrs={'class': 'form-control'}),
            'inventory_number': forms.TextInput(attrs={'class': 'form-control'}),
            'note': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        oid_type = cleaned_data.get('oid_type')
        
        # Якщо тип ОІД - ПЕМІН, то підтип стає обов'язковим
        if oid_type == OIDTypeChoices.PEMIN:
            pemin_sub_type = cleaned_data.get('pemin_sub_type')
            if not pemin_sub_type:
                self.add_error('pemin_sub_type', 'Це поле є обов\'язковим для типу ОІД "ПЕМІН".')
            elif pemin_sub_type == PeminSubTypeChoices.SPEAKSUBTYPE:
                self.add_error('pemin_sub_type', 'нє є типу "ПЕМІН".')
                
        # Якщо тип ОІД - МОВНА, автоматично встановлюємо "Клас ОІД" І очищуємо поля, що стосуються тільки ПЕМІН
        elif oid_type == OIDTypeChoices.SPEAK:
            cleaned_data['pemin_sub_type'] = PeminSubTypeChoices.SPEAKSUBTYPE
            cleaned_data['serial_number'] = ''
            cleaned_data['inventory_number'] = ''
        
        # Якщо тип не ПЕМІН, очищаємо специфічні поля, щоб вони не збереглися в БД випадково
        else:
            cleaned_data['pemin_sub_type'] = None
            cleaned_data['serial_number'] = ''
            cleaned_data['inventory_number'] = ''
            
        return cleaned_data
    

