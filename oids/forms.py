# C:\myFirstCRM\oids\forms.py

from django import forms
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
        widget=forms.Select(attrs={'class': 'form-select tomselect-field-defer'}) # Клас для TomSelect
    )
    # Поле для вибору ОІДів. Будемо покращувати за допомогою Tom Select.
    # Важливо: queryset тут може бути порожнім або містити всі ОІДи, 
    # оскільки реальне наповнення буде динамічним (залежно від обраної ВЧ).
    oids = forms.ModelMultipleChoiceField(
        queryset=OID.objects.none(), # Початково порожній, заповнюється JS
        label="Оберіть ОІД (будуть відфільтровані після вибору ВЧ)",
        widget=forms.SelectMultiple(attrs={'class': 'form-control tomselect-field-oids', 'size': '10'}), # Клас для TomSelect
        required=True # Або False, якщо заявка може бути без ОІДів на початку
    )
    # Поле для вибору типу робіт, яке буде застосовано до всіх обраних ОІДів
    request_work_type = forms.ChoiceField(
        choices=WorkTypeChoices.choices,
        label="Запитуваний тип роботи для обраних ОІД",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = WorkRequest
        fields = ['unit', 'incoming_number', 'incoming_date', 'request_work_type', 'oids', 'note']
        widgets = {
            'incoming_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'incoming_number': forms.TextInput(attrs={'class': 'form-control'}),
            'note': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }
        labels = {
            'unit': 'Військова частина',
            'incoming_number': 'Вхідний обліковий номер заявки',
            'incoming_date': 'Вхідна дата заявки',
            'note': 'Примітки до заявки',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Якщо форма редагується і вже є обрана ВЧ, можна одразу завантажити ОІДи для неї.
        # Але для нової форми це краще робити через JS.
        if self.instance and self.instance.unit_id:
             self.fields['oids'].queryset = OID.objects.filter(unit=self.instance.unit).order_by('cipher')
        else:
            # Якщо є початкове значення для unit (наприклад, з GET-параметра)
            initial_unit = self.initial.get('unit')
            if initial_unit:
                try:
                    unit_instance = Unit.objects.get(pk=initial_unit)
                    self.fields['oids'].queryset = OID.objects.filter(unit=unit_instance).order_by('cipher')
                except Unit.DoesNotExist:
                    self.fields['oids'].queryset = OID.objects.none() # Або всі, якщо ВЧ не знайдено
            else:
                 self.fields['oids'].queryset = OID.objects.none() # Для нової форми без обраної ВЧ

    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Логіка збереження самої заявки (WorkRequest)
        if commit:
            instance.save() # Спочатку зберігаємо WorkRequest, щоб отримати її ID

            # Тепер створюємо WorkRequestItem для кожного обраного ОІД
            # Ця логіка тепер централізована тут.
            selected_oids = self.cleaned_data.get('oids')
            selected_work_type = self.cleaned_data.get('request_work_type')
            
            if selected_oids and selected_work_type:
                # Видаляємо старі елементи, якщо це редагування і склад OID змінився (опційно, залежить від логіки)
                # instance.items.all().delete() 
                
                items_to_create = []
                for oid in selected_oids:
                    # Перевіряємо, чи такий елемент вже існує, щоб уникнути дублів (якщо потрібно)
                    # if not WorkRequestItem.objects.filter(request=instance, oid=oid, work_type=selected_work_type).exists():
                    items_to_create.append(
                        WorkRequestItem(
                            request=instance,
                            oid=oid,
                            work_type=selected_work_type,
                            status=WorkRequestStatusChoices.PENDING # Початковий статус для нового елемента
                        )
                    )
                if items_to_create:
                    WorkRequestItem.objects.bulk_create(items_to_create)
            
            # Збереження m2m даних форми, якщо вони є (в нашому випадку oids обробляються через WorkRequestItem)
            # self.save_m2m() 
            
        return instance

class TripForm(forms.ModelForm):
    # Використовуємо ModelMultipleChoiceField для ManyToMany зв'язків,
    # Select2 зробить їх зручнішими у шаблоні.
    units = forms.ModelMultipleChoiceField(
        queryset=Unit.objects.all().order_by('name'),
        widget=forms.SelectMultiple(attrs={'class': 'select2'}), # Додаємо клас для Select2
        label="Військові частини призначення",
        required=True
    )
    oids = forms.ModelMultipleChoiceField(
        queryset=OID.objects.filter(status__in=[OIDStatusChoices.ACTIVE, OIDStatusChoices.NEW, OIDStatusChoices.RECEIVED_REQUEST, OIDStatusChoices.RECEIVED_TZ]).order_by('cipher'),
        widget=forms.SelectMultiple(attrs={'class': 'select2'}),
        label="ОІД, що задіяні у відрядженні",
        required=False # Можливо, ОІДи будуть додані пізніше або не всі відомі одразу
    )
    persons = forms.ModelMultipleChoiceField(
        queryset=Person.objects.filter(is_active=True).order_by('full_name'),
        widget=forms.SelectMultiple(attrs={'class': 'select2'}),
        label="Особи у відрядженні",
        required=True
    )
    work_requests = forms.ModelMultipleChoiceField(
        queryset=WorkRequest.objects.filter(
            status__in=[WorkRequestStatusChoices.PENDING, WorkRequestStatusChoices.IN_PROGRESS]
        ).order_by('-incoming_date'),
        widget=forms.SelectMultiple(attrs={'class': 'select2'}),
        label="Пов'язані заявки на проведення робіт (статус 'Очікує' або 'В роботі')",
        required=False # Відрядження може бути не пов'язане з конкретною заявкою
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
        # Якщо потрібно динамічно фільтрувати queryset для OID на основі обраних Unit,
        # це краще робити за допомогою JavaScript на стороні клієнта,
        # або передавати відфільтрований queryset у view.
        # Наразі OID завантажуються всі активні/нові.
        # Приклад: self.fields['oids'].queryset = OID.objects.none() якщо units не обрані спочатку.
        
        # Додавання data-атрибутів для JavaScript фільтрації (приклад)
        # Це потрібно, якщо ти хочеш, щоб вибір Unit фільтрував OID *у цій формі*
        self.fields['units'].widget.attrs.update({'id': 'id_trip_units_form'}) # Даємо унікальний ID
        self.fields['oids'].widget.attrs.update({'id': 'id_trip_oids_form'})
        # У filtering_dynamic.js потрібно буде додати конфігурацію для цієї пари,
        # і на #id_trip_units_form додати data-ajax-url для завантаження OID
        # data-ajax-url="{% url 'oids:ajax_load_oids_for_unit' %}" (якщо такий URL існує)

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
