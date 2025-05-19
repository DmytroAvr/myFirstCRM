# C:\myFirstCRM\oids\views.py
from django.shortcuts import render, redirect
from .models import Document, Unit, OID, WorkRequest, DocumentType, WorkRequestItem
from .forms import DocumentForm, DocumentHeaderForm, DocumentFormSet, requestForm, requestHeaderForm, requestFormSet, requestItemFormSet, requestItemForm, OidCreateForm
from django.http import JsonResponse
import traceback        #check
from django.contrib import messages
from django.views.decorators.http import require_POST


def load_oids(request):
    try:
        unit_id = request.GET.get('unit')
        oids = OID.objects.filter(unit_id=unit_id).exclude(status='скасовано').order_by('name')
        data = [{'id': oid.id, 'name': oid.name} for oid in oids]
 
        return JsonResponse(list(oids.values('id', 'name')), safe=False)
        # return JsonResponse(data, safe=False)  #proposition for request
    except Exception as e:
        traceback.print_exc()  # ← виведе помилку у консоль VSCode
        return JsonResponse({'error': str(e)}, status=500)

def get_oids_by_unit(request):
    unit_id = request.GET.get('unit_id')
    oids = OID.objects.filter(unit__id=unit_id, status__in=['діючий', 'новий'])
    data = [{'id': oid.id, 'name': str(oid)} for oid in oids]
    return JsonResponse(data, safe=False)

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

# C:\myFirstCRM\oids\views.py
def document_request(request):
    if request.method == 'POST':
        header_form = requestHeaderForm(request.POST)
        formset = requestItemFormSet(request.POST)

        if header_form.is_valid() and formset.is_valid():
            work_request = header_form.save()

            for form in formset:
                if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                    item = form.save(commit=False)
                    item.request = work_request
                    item.save() 

                    messages.success(request, "Заявка успішно збережена!")
            return redirect('document_request')  # або інша сторінка
    else:
        header_form = requestHeaderForm()
        formset = requestItemFormSet(queryset=WorkRequestItem.objects.none())

    return render(request, 'oids/document_request.html', {
        'header_form': header_form,
        'formset': formset
    })

# aside for request 
@require_POST
def create_oid_ajax(request):
    form = OidCreateForm(request.POST)
    unit_id = request.POST.get('unit_id')

    if not unit_id:
        return JsonResponse({'success': False, 'errors': {'unit_id': ['Unit ID не передано']}}, status=400)

    if form.is_valid():
        oid = form.save(commit=False)
        try:
            unit = Unit.objects.get(id=unit_id)
            oid.unit = unit
            oid.save()
            return JsonResponse({'success': True, 'oid': {'id': oid.id, 'name': oid.name}})
        except Unit.DoesNotExist:
            return JsonResponse({'success': False, 'errors': {'unit': ['Unit не знайдено']}}, status=400)
    else:
        return JsonResponse({'success': False, 'errors': form.errors}, status=400)
    

    