# C:\myFirstCRM\oids\views.py
from django.shortcuts import render, redirect
from .models import Document, Unit, OID
from .forms import DocumentForm, DocumentHeaderForm, DocumentFormSet
from django.http import JsonResponse
import traceback        #check

def load_oids(request):
    try:
        unit_id = request.GET.get('unit')
        oids = OID.objects.filter(unit_id=unit_id).exclude(status='скасовано').order_by('name')
        return JsonResponse(list(oids.values('id', 'name')), safe=False)
    except Exception as e:
        traceback.print_exc()  # ← виведе помилку у консоль VSCode
        return JsonResponse({'error': str(e)}, status=500)

# C:\myFirstCRM\oids\views.py
def document_create(request):
    if request.method == 'POST':
        header_form = DocumentHeaderForm(request.POST)
        formset = DocumentFormSet(request.POST)

        if header_form.is_valid() and formset.is_valid():
            unit = header_form.cleaned_data['unit']
            oid = header_form.cleaned_data['oid']
            work_type = header_form.cleaned_data['work_type']
            work_date = header_form.cleaned_data['work_date']
            author = header_form.cleaned_data['author']
            process_date = header_form.cleaned_data['process_date']
            
            for form in formset:
                if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                    doc = form.save(commit=False)
                    doc.unit = unit
                    doc.oid = oid
                    doc.work_type = work_type
                    doc.work_date = work_date
                    doc.author = author
                    doc.process_date = process_date
                    doc.save()
            return redirect('document_create')
    else:
        header_form = DocumentHeaderForm()
        formset = DocumentFormSet(queryset=Document.objects.none())

    return render(request, 'oids/document_form.html', {
        'header_form': header_form,
        'formset': formset
    })
