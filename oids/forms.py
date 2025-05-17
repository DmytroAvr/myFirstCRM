# C:\myFirstCRM\oids\forms.py
from django import forms
from .models import Document, OID, Unit
from django.forms import modelformset_factory


# C:\myFirstCRM\oids\forms.py
class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['document_type', 'document_number', 'process_date', 'work_date', 'author', 'note']

class DocumentHeaderForm(forms.Form):
    unit = forms.ModelChoiceField(queryset=Unit.objects.all(), label="Військова частина")
    oid = forms.ModelChoiceField(queryset=OID.objects.none(), label="Об'єкт")
    work_type = forms.ChoiceField(choices=Document.WORK_TYPE_CHOICES, label="Тип роботи")

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
    extra=5,
    can_delete=True
)