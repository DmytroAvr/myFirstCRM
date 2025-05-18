# C:\myFirstCRM\oids\views.py
from django.shortcuts import render, redirect
from .models import Document, Unit, OID, WorkRequest, DocumentType, WorkRequestItem
from .forms import DocumentForm, DocumentHeaderForm, DocumentFormSet, requestForm, requestHeaderForm, requestFormSet, requestItemFormSet, requestItemForm
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

# C:\myFirstCRM\oids\views.py
# def document_request(request):
#     if request.method == 'POST':
#         header_form = requestHeaderForm(request.POST)
#         formset = requestFormSet(request.POST)

#         if header_form.is_valid() and formset.is_valid():
#             unit = header_form.cleaned_data['unit']
#             oid = header_form.cleaned_data['oid']
#             incoming_number = header_form.cleaned_data['incoming_number']
#             incoming_date = header_form.cleaned_data['incoming_date']

#             for form in formset:
#                 if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
#                     doc = form.save(commit=False)
#                     doc.unit = unit
#                     doc.oid = oid
#                     doc.work_type = work_type
#                     doc.work_date = work_date
#                     doc.incoming_number = incoming_number
#                     doc.incoming_date = incoming_date
#                     doc.save()
#             return redirect('document_create')
#     else:
#         header_form = requestHeaderForm()
#         formset = requestFormSet(queryset=WorkRequest.objects.none())

#     return render(request, 'oids/document_request.html', {
#         'header_form': header_form,
#         'formset': formset
#     })

# def document_request(request):
#     if request.method == 'POST':
#         header_form = requestHeaderForm(request.POST)
#         formset = requestFormSet(request.POST)

#         if header_form.is_valid() and formset.is_valid():
#             unit = header_form.cleaned_data['unit']
#             incoming_number = header_form.cleaned_data['incoming_number']
#             incoming_date = header_form.cleaned_data['incoming_date']

#             for form in formset:
#                 if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
#                     req = form.save(commit=False)
#                     req.Unit = unit
#                     req.incoming_number = incoming_number
#                     req.incoming_date = incoming_date
#                     req.save()
#                     form.save_m2m()  # для oids і work_type
#             return redirect('document_request')
#     else:
#         header_form = requestHeaderForm()
#         formset = requestFormSet(queryset=WorkRequest.objects.none())

#     return render(request, 'oids/document_request.html', {
#         'header_form': header_form,
#         'formset': formset
#     })

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

            return redirect('document_request')  # або інша сторінка
    else:
        header_form = requestHeaderForm()
        formset = requestItemFormSet(queryset=WorkRequestItem.objects.none())

    return render(request, 'oids/document_request.html', {
        'header_form': header_form,
        'formset': formset
    })
