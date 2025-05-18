# C:\myFirstCRM\oids\models.py
from django.db import models
from multiselectfield import MultiSelectField


class Unit(models.Model):  # Військова частина
    MANAGEMENT_UNIT_CHOICES = [
        ('ПівнічнеТУ', 'ПівнічнеТУ'),
        ('ПівденнеТУ', 'ПівденнеТУ'),
        ('ЗахіднеТУ', 'ЗахіднеТУ'),
        ('СхіднеТУ', 'СхіднеТУ'),
        ('ЦентральнеТУ', 'ЦентральнеТУ'),
    ]
    management_unit = models.CharField(max_length=50, choices=MANAGEMENT_UNIT_CHOICES, verbose_name="Управління")
    name = models.CharField(max_length=255, verbose_name="Військова частина")
    city = models.CharField(max_length=25, verbose_name="Місто")
    distance = models.CharField(max_length=10, verbose_name="відстань КМ")
    directionGroup = models.CharField(max_length=10, verbose_name="грапа частин в які часто їдимо")

    def __str__(self):
        return self.name


class OID(models.Model):  # Об'єкт інформаційної діяльності
    TYPE_CHOICES = [
        ('ПЕМІН', 'ПЕМІН'), ('МОВНА', 'МОВНА'),
    ]

    STATUS_CHOICES = [
        ('створюється', 'створюється'),
        ('атестована', 'атестована'),
        ('в експлуатації', 'в експлуатації'),
        ('обробка припинена', 'обробка припинена'),
        ('скасовано', 'скасовано'),
    ]

    name = models.CharField(max_length=255, verbose_name="Назва")
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, verbose_name="Військова частина")
    room = models.CharField(max_length=255, verbose_name="Приміщення №")  # address -> room
    note = models.TextField(verbose_name="Примітка", blank=True, null=True)  # purpose -> note
    oid_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='ПЕМІН', verbose_name="Тип ОІД")
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='створюється', verbose_name="Поточний стан ОІД")
    
    def __str__(self):
        return self.name


class Person(models.Model):
    name = models.CharField(max_length=255, verbose_name="Призвище, ім'я")
    position = models.CharField(max_length=255, verbose_name="Посада")

    def __str__(self):
        return self.name


class DocumentType(models.Model):
    oid_type = models.CharField(
        "Тип ОІД",
        max_length=20,
        choices=[('МОВНА', 'МОВНА'), ('ПЕМІН', 'ПЕМІН'), ('Спільний', 'Спільний')],
    )
    work_type = models.CharField(
        "Тип робіт",
        max_length=20,
        choices=[('Атестація', 'Атестація'), ('ІК', 'ІК'), ('Спільний', 'Спільний')],
    )
    name = models.CharField("Назва документа", max_length=100, unique=True)
    valid_days = models.PositiveIntegerField(
        "Строк дії (у місяцях)", default=0,
        help_text="Наприклад, 20 або 60. Якщо не обмежений — залишити 0."
    )

    def __str__(self):
        return f"{self.name} ({self.oid_type}, {self.work_type})"

class Document(models.Model):
    WORK_TYPE_CHOICES = [
        ('Атестація', 'Атестація'), ('ІК', 'ІК'),
    ]
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, verbose_name="Військова частина")  # ← Ось це додай
    oid = models.ForeignKey(OID, on_delete=models.CASCADE, verbose_name="ОІД")
   
    work_type = models.CharField(max_length=20, choices=WORK_TYPE_CHOICES, verbose_name="Тип роботи")
    document_type = models.ForeignKey(DocumentType, on_delete=models.CASCADE, verbose_name="Документ")
    document_number = models.CharField(max_length=50, default='27/14-', verbose_name="Підготовлений № документа")
    process_date = models.DateField(verbose_name="Дата опрацювання")
    work_date = models.DateField(verbose_name="Дата проведення робіт")
    author = models.CharField(max_length=255, verbose_name="Виконавець (ПІБ)")
    note = models.TextField(blank=True, null=True, verbose_name="Примітки")

    def __str__(self):
        return f"{self.document_type.name} / {self.document_number}"


class Trip(models.Model):  # Відрядження
    units = models.ManyToManyField(Unit, verbose_name="Військові частини")
    oid = models.ManyToManyField(OID, verbose_name="Які ОІД")
    # oid = models.ForeignKey(OID, on_delete=models.CASCADE, verbose_name="Об'єкт")
    start_date = models.DateField(verbose_name="Дата початку")
    end_date = models.DateField(verbose_name="Дата завершення")
    persons = models.ManyToManyField(Person, verbose_name="Відряджаються")
    # persons = models.CharField(max_length=255, verbose_name="Відряджаються")
    purpose = models.TextField(blank=True, null=True, verbose_name="Примітка", )

    # def __str__(self):
    #     return f"Виїзд на {self.oid.name} ({self.start_date} - {self.end_date})"
    #  дав помилку бо це про один обєкт

    def __str__(self):
        unitss = ", ".join([obj.name for obj in self.units.all()])
        oids = ", ".join([obj.name for obj in self.oid.all()])
        start = self.start_date.strftime("%d-%m-%Y")
        end = self.end_date.strftime("%d-%m-%Y")
        return f"Виїзд з {start} до {end}  Частини: {unitss} --- ОІД: ({oids})"

# C:\myFirstCRM\oids\models.py
class WorkRequest(models.Model):  # Заявка на проведення робіт
    WORK_TYPE_CHOICES = [
        ('Атестація', 'Атестація'), ('ІК', 'ІК'),
    ]

    STATUS_CHOICES = [
        ('очікує', 'очікує'), ('в роботі', 'в роботі'), ('виконано', 'виконано'), ('скасовано', 'скасовано'),
    ]

    unit = models.ForeignKey('Unit', on_delete=models.CASCADE, verbose_name="Військова частина")
    work_type = MultiSelectField(choices=WORK_TYPE_CHOICES, verbose_name="Типи роботи")
    # work_type = models.CharField("Тип роботи", max_length=20, choices=WORK_TYPE_CHOICES)
    oids = models.ManyToManyField('OID', verbose_name="Об’єкти інформаційної діяльності")
    incoming_number = models.CharField(verbose_name="Вхідний номер заявки", max_length=50)
    incoming_date = models.DateField(verbose_name="Дата заявки")
    status = models.CharField(verbose_name="Статус заявки", max_length=20, choices=STATUS_CHOICES, default='очікує')
    note = models.TextField(verbose_name="Примітки", blank=True, null=True)

    def __str__(self):
        return f"{self.incoming_number} — {self.get_status_display()}"

class WorkRequestItem(models.Model):
    WORK_TYPE_CHOICES = [
        ('Атестація', 'Атестація'),
        ('ІК', 'ІК'),
    ]
    
    request = models.ForeignKey(WorkRequest, on_delete=models.CASCADE, related_name="items")
    oid = models.ForeignKey('OID', on_delete=models.CASCADE)
    work_type = models.CharField(max_length=20, choices=WORK_TYPE_CHOICES)

    def __str__(self):
        return f"{self.oid} — {self.work_type}"

