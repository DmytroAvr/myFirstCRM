# C:\myFirstCRM\oids\forms.py
from django import forms
from .models import Document, OID
from django.forms import modelformset_factory


class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['oid'].queryset = OID.objects.none()

        if 'unit' in self.data:
            try:
                unit_id = int(self.data.get('unit'))
                self.fields['oid'].queryset = OID.objects.filter(unit_id=unit_id).exclude(status='скасовано').order_by('name')
            except (ValueError, TypeError):
                pass
        elif self.instance.pk:
            self.fields['oid'].queryset = self.instance.unit.oid_set.exclude(status='скасовано').order_by('name')


