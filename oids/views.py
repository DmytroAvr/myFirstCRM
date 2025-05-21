# C:\myFirstCRM\oids\views.py
from django.shortcuts import render, redirect
from .models import Document, Unit, OID, WorkRequest, DocumentType, WorkRequestItem
from .forms import DocumentForm, DocumentHeaderForm, DocumentFormSet, requestForm, requestHeaderForm, requestFormSet, requestItemFormSet, requestItemForm, OidCreateForm, AttestationRegistrationForm, TripResultForUnitForm, TechnicalTaskForm, OIDStatusChangeForm
from django.http import JsonResponse
import traceback        #check
from django.contrib import messages
from django.views.decorators.http import require_POST

def home_view(request):
    return render(request, 'home.html')


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

def load_oids_for_unit(request):
    unit_id = request.GET.get('unit')
    oids = OID.objects.filter(unit_id=unit_id).exclude(status='скасовано').order_by('name')
    return JsonResponse(list(oids.values('id', 'name')), safe=False)


def load_oids_for_units(request):
    unit_ids = request.GET.getlist('units[]')
    oids = OID.objects.filter(unit__id__in=unit_ids).exclude(status="скасовано").order_by('name')
    return JsonResponse(list(oids.values('id', 'name')), safe=False)

def get_oid_status(request):
    oid_id = request.GET.get('oid_id')
    try:
        oid = OID.objects.get(id=oid_id)
        return JsonResponse({'status': oid.status})
    except OID.DoesNotExist:
        return JsonResponse({'status': ''})
    

def load_documents_for_oids(request):
    oid_ids = request.GET.getlist('oids[]')
    documents = Document.objects.filter(oid__id__in=oid_ids).order_by('document_type__name', 'document_number')
    return JsonResponse(list(documents.values('id', 'document_type__name', 'document_number')), safe=False)


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
    
# додавання документів


def create_attestation_registration(request):
    if request.method == 'POST':
        form = AttestationRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('attestation_new')  # або інша сторінка
    else:
        form = AttestationRegistrationForm()
    return render(request, 'attestation_registration_form.html', {'form': form})

def create_trip_result(request):
    if request.method == 'POST':
        form = TripResultForUnitForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('trip_result_new')  # або інша сторінка
            # return redirect('trip_result_list')  # або інша сторінка
    else:
        form = TripResultForUnitForm()
    return render(request, 'trip_result_form.html', {'form': form})

def trip_result_list(request):
    results = TripResult.objects.all()
    return render(request, 'oids/trip_result_list.html', {'results': results})


# Технічне завдання
def technical_task_create(request):
    if request.method == 'POST':
        form = TechnicalTaskForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('technical_task_create')  # або інша сторінка
    else:
        form = TechnicalTaskForm()
    return render(request, 'oids/technical_task_form.html', {'form': form})


def create_oid(request):
    if request.method == 'POST':
        form = OIDForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('technical_task_form')  # або назад до TechnicalTask
    else:
        form = OIDForm()
    return render(request, 'oids/oid_form.html', {'form': form})

def change_oid_status(request):
    if request.method == 'POST':
        form = OIDStatusChangeForm(request.POST)
        if form.is_valid():
            oid = form.cleaned_data['oid']
            instance = form.save(commit=False)
            instance.old_status = oid.status  # автоматично вставляємо поточний статус
            instance.save()

            # оновлюємо сам OID
            oid.status = form.cleaned_data['new_status']
            oid.save()

            return redirect('oid_status_change')
    else:
        form = OIDStatusChangeForm()
    return render(request, 'oids/oid_status_change_form.html', {'form': form})
