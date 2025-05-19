# C:\myFirstCRM\oids\forms.py
from django import forms
from .models import Document, OID, Unit, Person, WorkRequest, WorkRequestItem, AttestationRegistration, TripResultForUnit
from django.forms import modelformset_factory


class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['document_type', 'document_number', 'note']

class DocumentHeaderForm(forms.Form):
    unit = forms.ModelChoiceField(queryset=Unit.objects.all(), label="Військова частина")
    oid = forms.ModelChoiceField(queryset=OID.objects.none(), label="ОІД")
    work_type = forms.ChoiceField(choices=Document.WORK_TYPE_CHOICES, label="Тип роботи")
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

# 



# C:\myFirstCRM\oids\forms.py
class requestForm(forms.ModelForm):
    class Meta:
        model = WorkRequest
        fields = ['oids', 'work_type','status']
        # fields = ['Unit', 'work_type', 'oids', 'incoming_number', 'incoming_date', 'status']


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

# class requestForm(forms.ModelForm):
#     class Meta:
#         model = WorkRequest
#         fields = ['oids', 'work_type', 'status']
#         widgets = {
#             'oids': forms.SelectMultiple(attrs={'size': 5}),
#             'work_type': forms.CheckboxSelectMultiple(),  # або SelectMultiple
#         }

# class requestHeaderForm(forms.Form):
#     unit = forms.ModelChoiceField(queryset=Unit.objects.all(), label="Військова частина")
#     incoming_number = forms.CharField(label="Вхідний номер заявки", max_length=50)
#     incoming_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), label="Дата вхідного")

#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
class requestHeaderForm(forms.ModelForm):
    class Meta:
        model = WorkRequest
        fields = ['unit', 'incoming_number', 'incoming_date', 'status', 'note']
        widgets = {
            'unit': forms.Select(attrs={'id': 'id_unit'}),
            'incoming_date': forms.DateInput(attrs={'type': 'date'}),
        }


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
        fields = ['name', 'room', 'note', 'oid_type', 'status']  # без 'unit'
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'room': forms.TextInput(attrs={'class': 'form-control'}),
            'note': forms.Textarea(attrs={'class': 'form-control'}),
            'oid_type': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }

# 
class AttestationRegistrationForm(forms.ModelForm):
    class Meta:
        model = AttestationRegistration
        fields = '__all__'

class TripResultForUnitForm(forms.ModelForm):
    class Meta:
        model = TripResultForUnit
        fields = '__all__'