# oids/utils.py
import openpyxl
from django.http import HttpResponse
from openpyxl.utils import get_column_letter

def export_to_excel(queryset, columns, filename='export.xlsx'):
    """
    Експортує queryset в Excel-файл.

    :param queryset: QuerySet з даними для експорту.
    :param columns: Словник, де ключ - це рядок доступу до поля (напр. 'unit__code'), 
                    а значення - це назва стовпця в Excel.
    :param filename: Ім'я файлу для завантаження.
    """
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = 'Data'

    # --- Записуємо заголовки стовпців ---
    for col_num, column_title in enumerate(columns.values(), 1):
        cell = sheet.cell(row=1, column=col_num)
        cell.value = column_title
        cell.font = openpyxl.styles.Font(bold=True)
        # Встановлюємо ширину стовпця
        column_letter = get_column_letter(col_num)
        sheet.column_dimensions[column_letter].width = 25

    # --- Записуємо дані ---
    for row_num, obj in enumerate(queryset, 2):
        for col_num, field_name in enumerate(columns.keys(), 1):
            cell = sheet.cell(row=row_num, column=col_num)
            
            # Обробка вкладених полів (напр. 'request__unit__code')
            value = obj
            try:
                for part in field_name.split('__'):
                    # Перевірка, чи є атрибут методом (напр. get_status_display)
                    if hasattr(value, part):
                         attr = getattr(value, part)
                         if callable(attr):
                             value = attr()
                         else:
                             value = attr
                    else:
                        value = None
                        break
            except AttributeError:
                value = None # Якщо якийсь проміжний об'єкт None
            
            cell.value = str(value) if value is not None else ""

    workbook.save(response)
    return response