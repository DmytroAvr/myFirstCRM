# views.py
from django.shortcuts import render, redirect
from .models import Document, Unit, OID
from .forms import DocumentForm
from django.http import JsonResponse
import traceback        #check

def document_create(request):
    if request.method == 'POST':
        form = DocumentForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('document_create')  # або інша сторінка
    else:
        form = DocumentForm()
    return render(request, 'oids/document_form.html', {'form': form})

# def load_oids(request):
#     unit_id = request.GET.get('unit')
#     oids = OID.objects.filter(unit_id=unit_id).exclude(status='скасовано').order_by('name')
#     return JsonResponse(list(oids.values('id', 'name')), safe=False)



# for checking
def load_oids(request):
    try:
        unit_id = request.GET.get('unit')
        oids = OID.objects.filter(unit_id=unit_id).exclude(status='скасовано').order_by('name')
        return JsonResponse(list(oids.values('id', 'name')), safe=False)
    except Exception as e:
        traceback.print_exc()  # ← виведе помилку у консоль VSCode
        return JsonResponse({'error': str(e)}, status=500)
