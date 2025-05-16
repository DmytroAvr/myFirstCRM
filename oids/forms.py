# %%%%%ооо111111
# 
# 
# # from django import forms
# from .models import Document, OID, DocumentType

# class DocumentForm(forms.ModelForm):
#     class Meta:
#         model = Document
#         fields = '__all__'

#     def __init__(self, *args, **kwargs):
#         super(DocumentForm, self).__init__(*args, **kwargs)

#         oid = None
#         work_type = None

#         if 'oid' in self.data:
#             try:
#                 oid = OID.objects.get(pk=int(self.data.get('oid')))
#             except (ValueError, OID.DoesNotExist):
#                 pass
#         elif self.instance.pk:
#             oid = self.instance.oid

#         if 'work_type' in self.data:
#             work_type = self.data.get('work_type')
#         elif self.instance.pk:
#             work_type = self.instance.work_type

#         if oid and work_type:
#             self.fields['document_type'].queryset = DocumentType.objects.filter(
#                 oid_type=oid.type,
#                 work_type=work_type
#             )
#         else:
#             self.fields['document_type'].queryset = DocumentType.objects.none()
