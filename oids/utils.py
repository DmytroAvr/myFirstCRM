# oids/utils.py
import openpyxl
from django.http import HttpResponse
from openpyxl.utils import get_column_letter
from openpyxl.styles import Font

def export_to_excel(queryset, columns, filename='export.xlsx', include_row_numbers=False):
    """
    :param queryset: QuerySet з даними для експорту.
    :param columns: Словник, де ключ - це рядок доступу до поля (напр. 'unit__code'), 
                    а значення - це назва стовпця в Excel.
    :param filename: Ім'я файлу для завантаження.
    :param include_row_numbers: Якщо True, додає стовпець '№' з нумерацією рядків.

    """
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = 'NGUOID info system'

    # --- Записуємо заголовки ---
    start_col = 1
    header_font = Font(bold=True)
    if include_row_numbers:
        cell = sheet.cell(row=1, column=1)
        cell.value = '№'
        cell.font = header_font
        sheet.column_dimensions[get_column_letter(1)].width = 5
        start_col = 2

    for col_num, column_title in enumerate(columns.values(), start_col):
        cell = sheet.cell(row=1, column=col_num)
        cell.value = column_title
        cell.font = header_font
        column_letter = get_column_letter(col_num)
        sheet.column_dimensions[column_letter].width = 30

    # --- Записуємо дані ---
    for row_num, obj in enumerate(queryset, 2):
        row_in_list = row_num - 1
        
        if include_row_numbers:
            # --- ФОРМАТ НОМЕРА РЯДКА ---
            sheet.cell(row=row_num, column=1).value = f"{row_in_list}."

        for col_num, field_name in enumerate(columns.keys(), start_col):
            cell = sheet.cell(row=row_num, column=col_num)
            
            value = obj
            try:
                for part in field_name.split('__'):
                    attr = getattr(value, part)
                    if callable(attr):
                        value = attr()
                    else:
                        value = attr
            except (AttributeError, TypeError):
                value = None
            
            cell.value = str(value) if value is not None else ""

    # --- НАЛАШТУВАННЯ ДРУКУ ---
    # Визначаємо діапазон даних
    max_row = sheet.max_row
    max_col_letter = get_column_letter(sheet.max_column)
    
    # Встановлюємо область друку
    if max_row > 0 and sheet.max_column > 0:
        sheet.print_area = f'A1:{max_col_letter}{max_row}'
    
    # Додаткові налаштування сторінки для друку
    sheet.page_setup.orientation = sheet.ORIENTATION_PORTRAIT  # Альбомна орієнтація PORTRAIT   LANDSCAPE
    sheet.page_setup.paperSize = sheet.PAPERSIZE_A4         # Формат А4
    sheet.page_setup.fitToPage = True                        # Ввімкнути масштабування
    sheet.page_setup.fitToWidth = 1                          # Масштабувати по ширині однієї сторінки
    sheet.page_setup.fitToHeight = 0                         # Висота може бути автоматичною (кілька сторінок)

    workbook.save(response)
    return response