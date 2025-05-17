# C:\myFirstCRM\oids\forms.py
from django import forms
from .models import Document, OID, Unit, Person
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