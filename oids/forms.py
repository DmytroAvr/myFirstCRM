# C:\myFirstCRM\oids\forms.py
from django import forms
from .models import Document, OID, Unit, Person, WorkRequest, WorkRequestItem, AttestationRegistration, TripResultForUnit, TechnicalTask, AttestationResponse, OIDStatusChange
from django.forms import modelformset_factory
from django_select2.forms import Select2MultipleWidget
# from django_select2.forms import Select2MultipleWidget, ModelSelect2MultipleWidget
from .models import OIDStatusChoices, OIDTypeChoices, WorkTypeChoices, ReviewResultChoices, WRequestStatusChoices, Trip


class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['document_type', 'document_number', 'note']

class DocumentHeaderForm(forms.Form):
    unit = forms.ModelChoiceField(queryset=Unit.objects.all(), label="Військова частина")
    oid = forms.ModelChoiceField(queryset=OID.objects.none(), label="ОІД")
    work_type = forms.ChoiceField(choices=WorkTypeChoices.choices, label="Тип роботи")
    work_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), label="Дата роботи на ОІД")
    author = forms.ModelChoiceField(queryset=Person.objects.all(), label="Хто виконав документи")
    # author = forms.CharField(label="Хто виконав документи", max_length=100) #add to fild #manual enter
    process_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), label="Дата опрацювання документів")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'unit' in self.data:
            try:
                unit_id = int(self.data.get('unit'))
                self.fields['oid'].queryset = OID.objects.filter(unit_id=unit_id).exclude(status='скасовано').order_by('name')
            except (ValueError, TypeError):
                pass

DocumentFormSet = modelformset_factory(
    Document,
    form=DocumentForm,
    extra=3,
    can_delete=True
)

# C:\myFirstCRM\oids\forms.py
class requestForm(forms.ModelForm):
    class Meta:
        model = WorkRequest
        fields = ['oids', 'work_type','status']
        # fields = ['Unit', 'work_type', 'oids', 'incoming_number', 'incoming_date', 'status']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['oid'].widget.attrs.update({'id': 'id_oid'})
    

# test field
class requestHeaderForm(forms.ModelForm):
    class Meta:
        model = WorkRequest
        fields = ['unit', 'incoming_number', 'incoming_date', 'status', 'note']
        widgets = {
            'work_type': forms.Select(),  # одиночний вибір
            'incoming_date': forms.DateInput(attrs={'type': 'date'}),
        }

class requestItemForm(forms.ModelForm):
    class Meta:
        model = WorkRequestItem
        fields = ['oid', 'work_type']

class requestHeaderForm(forms.ModelForm):
    class Meta:
        model = WorkRequest
        fields = ['unit', 'incoming_number', 'incoming_date', 'status', 'note']
        widgets = {
            'unit': forms.Select(attrs={'id': 'id_unit'}),
            'incoming_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['incoming_number'].initial = "тип/щось"

        # Спочатку створюємо список статусів, які потрібно виключити
        exclude_statuses = [
            WRequestStatusChoices.COMPLETED, 
            WRequestStatusChoices.CANCELED,
        ]
        
        # Тепер фільтруємо choices для поля status
        self.fields['status'].choices = [
            choice for choice in WRequestStatusChoices.choices if choice[0] not in exclude_statuses
        ]

requestFormSet = modelformset_factory(
    WorkRequest,
    form=requestForm,
    extra=2,
    can_delete=True
)

requestItemFormSet = modelformset_factory(
    WorkRequestItem,
    form=requestItemForm,
    extra=2,
    can_delete=True
)

# oids/forms.py

# aside oid create form
class OidCreateForm(forms.ModelForm):
    class Meta:
        model = OID
        fields = ['name', 'sec_level', 'room', 'note', 'oid_type', 'status']  # без 'unit'
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'sec_level': forms.Select(attrs={'class': 'form-control'}),
            'room': forms.TextInput(attrs={'class': 'form-control'}),
            'note': forms.Textarea(attrs={'class': 'form-control'}),
            'oid_type': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }

class OIDStatusChangeForm(forms.ModelForm):
    # unit = forms.ModelChoiceField(queryset=Unit.objects.all(), label="Військова частина", required=False)
    class Meta:
        model = OIDStatusChange
        fields = ['unit', 'oid', 'old_status', 'incoming_number', 'new_status', 'reason', 'changed_by'] 

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # old_status readonly
        self.fields['old_status'].disabled = True

        # new_status only two choices
        self.fields['new_status'].widget = forms.Select(choices=[
            ('обробка призупинено', 'обробка призупинено'),
            ('скасовано', 'скасовано'),
            ('діючий', 'діючий'),
        ])

        # Якщо форма вже заповнюється (POST), дозволяємо валідацію будь-якого OID:
        if self.is_bound:
            self.fields['oid'].queryset = OID.objects.all()
        else:
            # Порожній список при першому завантаженні
            self.fields['oid'].queryset = OID.objects.none()

        # Вставляємо поточний статус, якщо OID вже вибрано (при сабміті або редагуванні)
        if 'oid' in self.data:
            try:
                oid = OID.objects.get(pk=int(self.data.get('oid')))
                # Автоматично підставляємо old_status
                self.fields['old_status'].initial = oid.status
            except (ValueError, OID.DoesNotExist):
                pass
        elif self.instance.pk:
            self.fields['old_status'].initial = self.instance.oid.status

#  нові поля. додати АА, відправку документів до частини
class AttestationRegistrationForm(forms.ModelForm):
    class Meta:
        model = AttestationRegistration
        fields = '__all__'
        widgets = {
            'units': Select2MultipleWidget,
            'oids': Select2MultipleWidget,
        }

class TripResultForUnitForm(forms.ModelForm):
    class Meta:
        model = TripResultForUnit
        fields = '__all__'
        widgets = {
            'units': Select2MultipleWidget,
            'oids': Select2MultipleWidget,
            'documents': Select2MultipleWidget,
        }

# Технічне завдання
class TechnicalTaskForm(forms.ModelForm):
    unit = forms.ModelChoiceField(queryset=Unit.objects.all(), label="Військова частина", required=True)
    oid = forms.ModelChoiceField(queryset=OID.objects.none(), label="ОІД", required=True)

    class Meta:
        model = TechnicalTask
        fields = ['oid', 'input_number', 'input_date', 'reviewed_by', 'review_result', 'note']
        widgets = {
            'input_date': forms.DateInput(attrs={'type': 'date'}),
        }

    # reviewed_by = forms.ModelChoiceField(queryset=Person.objects.all(), label="Хто ознайомився")
   
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'unit' in self.data:
            try:
                unit_id = int(self.data.get('unit'))
                self.fields['oid'].queryset = OID.objects.filter(unit_id=unit_id).exclude(status='скасовано')
            except (ValueError, TypeError):
                pass
        elif self.instance.pk:
            self.fields['oid'].queryset = OID.objects.filter(unit=self.instance.oid.unit)



class TripForm(forms.ModelForm):
    class Meta:
            model = Trip
            fields = '__all__'
            widgets = {
                'start_date': forms.DateInput(attrs={'type': 'date'}),
                'end_date': forms.DateInput(attrs={'type': 'date'}),
                'work_requests': forms.SelectMultiple(),  # ← для підтримки вибору кількох заявок
            }


# 