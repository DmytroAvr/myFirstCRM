# C:\myFirstCRM\oids\forms.py

from django import forms
from django.forms import inlineformset_factory, modelformset_factory
from .models import (WorkRequestStatusChoices, WorkTypeChoices, OIDTypeChoices, 
	OIDStatusChoices, AttestationRegistrationStatusChoices, 
)
from .models import (
    WorkRequest, WorkRequestItem, OID, Unit, Person, Trip, Document, DocumentType,
    AttestationRegistration, AttestationResponse,  
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
    
# new form for documents
# new form for documents
# oids/forms.py
from django import forms
from django.forms import formset_factory # Або modelformset_factory
from .models import Document, OID, Unit, WorkRequestItem, DocumentType, Person

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
        label="Підготовлений № документа",
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
        # Поля oid, work_request_item, process_date, work_date, author будуть з головної форми

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
    process_date = forms.DateField(
        label="Дата опрацювання документів (пакету)",
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        required=True
    )
    work_date = forms.DateField(
        label="Дата виконання робіт на ОІД (для цього пакету)",
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
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
    unit = forms.ModelChoiceField(
        queryset=Unit.objects.all().order_by('code'),
        label="1. Військова частина",
        widget=forms.Select(attrs={'class': 'form-select tomselect-field', 'id': 'id_att_reg_send_unit'}),
        empty_label="Оберіть ВЧ...",
        help_text="Оберіть військову частину, для ОІДів якої будуть відправлені акти."
    )
    
    oid = forms.ModelChoiceField(
        queryset=OID.objects.none(), # Заповнюється динамічно JS
        label="2. Об'єкт інформаційної діяльності (ОІД)",
        widget=forms.Select(attrs={'class': 'form-select tomselect-field', 'id': 'id_att_reg_send_oid'}),
        empty_label="Спочатку оберіть ВЧ...",
        required=True, # Потрібно обрати ОІД, щоб побачити його акти
        help_text="Оберіть ОІД, акти якого потрібно відправити."
    )

    attestation_acts = forms.ModelMultipleChoiceField(
        queryset=Document.objects.none(), # Заповнюється динамічно JS
        label="3. Акти Атестації для відправки",
        widget=forms.SelectMultiple(attrs={'class': 'form-select tomselect-field', 'id': 'id_att_reg_send_acts', 'size': '8'}),
        required=True,
        help_text="Оберіть один або декілька Актів Атестації для цього ОІД, які ще не були відправлені."
    )

    # Інші поля залишаються, як у вашій моделі AttestationRegistration
    # Поле 'units' (ManyToMany) з моделі ми будемо заповнювати у view, тому його тут немає
    class Meta:
        model = AttestationRegistration
        fields = [
            'outgoing_letter_number', 
            'outgoing_letter_date', 
            'sent_by', 
            # 'units', # Заповнимо у view
            'note', 
            'attachment'
        ]
        widgets = {
            'outgoing_letter_number': forms.TextInput(attrs={'class': 'form-control'}),
            'outgoing_letter_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'sent_by': forms.Select(attrs={'class': 'form-select tomselect-field'}),
            'note': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'attachment': forms.FileInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'outgoing_letter_number': "Вихідний номер супровідного листа",
            'outgoing_letter_date': "Дата вихідного супровідного листа",
            'sent_by': "Хто відправив (підготував лист)",
            'note': "Примітки до відправки",
            'attachment': "Скан-копія супровідного листа"
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Якщо форма обробляє POST-дані, потрібно оновити querysets для валідації
        if self.is_bound:
            unit_id = self.data.get(self.add_prefix('unit'))
            oid_id = self.data.get(self.add_prefix('oid'))

            if unit_id and unit_id.isdigit():
                self.fields['oid'].queryset = OID.objects.filter(unit_id=int(unit_id)).order_by('cipher')
            
            if oid_id and oid_id.isdigit():
                document_type_act_att = DocumentType.objects.filter(name__icontains='Акт атестації').first()
                if document_type_act_att:
                    self.fields['attestation_acts'].queryset = Document.objects.filter(
                        oid_id=int(oid_id),
                        document_type=document_type_act_att,
                        attestation_registration_sent__isnull=True 
                        # Тут можна додати додаткові фільтри статусу ОІД, якщо потрібно
                    ).order_by('-work_date')
                else:
                    self.fields['attestation_acts'].queryset = Document.objects.none()
            
            # Для поля units (M2M в моделі), якщо воно було б у формі,
            # Django б сам підхопив значення з POST, якщо віджет SelectMultiple.
            # Оскільки ми його прибрали, то нічого тут для нього не робимо.
            

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
            'attachment'
        ]
        widgets = {
            'response_letter_number': forms.TextInput(attrs={'class': 'form-control'}),
            'response_letter_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'received_by': forms.Select(attrs={'class': 'form-select tomselect-field'}),
            'note': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'attachment': forms.FileInput(attrs={'class': 'form-control'}),
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
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control form-control-sm'})
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

ALLOWED_STATUS_CHOICES = [
    (OIDStatusChoices.CANCELED, OIDStatusChoices.CANCELED.label),
    (OIDStatusChoices.TERMINATED, OIDStatusChoices.TERMINATED.label),
    (OIDStatusChoices.ACTIVE, OIDStatusChoices.ACTIVE.label),
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