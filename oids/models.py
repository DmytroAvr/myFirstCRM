# C:\myFirstCRM\oids\models.py
from django.db import models
from multiselectfield import MultiSelectField
from django.utils import timezone

class StatusChoices(models.TextChoices):
    NEW = 'створюється', 'Створюється'
    ATTESTED = 'атестована', 'атестована'
    ACTIVE = 'в експлуатації', 'В експлуатації'
    TERMINATED = 'обробка призупинена', 'обробка призупинена'
    CANCELED = 'скасовано', 'скасовано'

class OIDTypeChoices(models.TextChoices):
    PC = 'ПЕМІН', 'ПЕМІН'
    SPEAK = 'МОВНА', 'МОВНА'

class WorkTypeChoices(models.TextChoices):
    ATTESTATION = 'Атестація', 'Атестація'
    IK = 'ІК', 'ІК'

class ReviewResultChoices(models.TextChoices):
    REVIEWED = 'погоджено', 'Погоджено'
    REWORK = 'на доопрацювання', 'На доопрацювання'
    WAITING = 'чекаємо папір', 'Чекаємо папір'


    # oid_type = models.CharField(max_length=10, choices=OIDTypeChoices.choices, default=OIDTypeChoices.PC, verbose_name="Тип ОІД")
    # work_type = models.CharField(max_length=20, choices=WorkTypeChoices.choices, default=WorkTypeChoices.IK, verbose_name="Тип роботи")
    # status = models.CharField(max_length=30, choices=StatusChoices.choices, default=StatusChoices.NEW, verbose_name="Поточний стан ОІД")
    # review_result = models.CharField(max_length=30, choices=ReviewResultChoices.choices, default=ReviewResultChoices.REVIEWED, verbose_name="Результат розгляду")
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

    name = models.CharField(max_length=255, verbose_name="Назва")
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, verbose_name="Військова частина")
    room = models.CharField(max_length=255, verbose_name="Приміщення №")  # address -> room
    note = models.TextField(verbose_name="Примітка", blank=True, null=True)  # purpose -> note
    oid_type = models.CharField(max_length=10, choices=OIDTypeChoices.choices, default=OIDTypeChoices.PC, verbose_name="Тип ОІД")
    status = models.CharField(max_length=30, choices=StatusChoices.choices, default=StatusChoices.NEW, verbose_name="Поточний стан ОІД")
    created_by_document = models.OneToOneField(
        'Document',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='first_doc_for_oid',
        verbose_name="Перший документ (Атестація/ІК)"
    )

    latest_document = models.ForeignKey(
        'Document',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='latest_doc_for_oid',
        verbose_name="Останній документ"
    )

    def __str__(self):
        return self.name

# C:\myFirstCRM\oids\models.py
class OIDStatusChange(models.Model):
    unit = models.ForeignKey('Unit', on_delete=models.CASCADE, verbose_name="Військова частина")
    oid = models.ForeignKey('OID', on_delete=models.CASCADE, verbose_name="ОІД")
    old_status = models.CharField(max_length=30, verbose_name="Попередній статус")
    incoming_number = models.CharField(max_length=50, blank=True, null=True, verbose_name="Вхідний номер документа")
    new_status = models.CharField(max_length=30, verbose_name="Новий статус")
    reason = models.TextField(blank=True, null=True, verbose_name="Причина зміни")
    changed_by = models.CharField(max_length=100, verbose_name="Хто змінив")
    changed_at = models.DateField(auto_now_add=True, verbose_name="Дата зміни")


    def __str__(self):
        return f"{self.oid.name}: {self.old_status} → {self.new_status} ({self.changed_at})"


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

    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, verbose_name="Військова частина")
    oid = models.ForeignKey(OID, on_delete=models.CASCADE, verbose_name="ОІД")
    
    oid_type = models.CharField(max_length=20, choices=OIDTypeChoices.choices, default=OIDTypeChoices.PC, verbose_name="Тип ОІД")

    work_type = models.CharField(max_length=20, choices=WorkTypeChoices.choices, default=WorkTypeChoices.IK, verbose_name="Тип роботи")
    document_type = models.ForeignKey(DocumentType, on_delete=models.CASCADE, verbose_name="Документ")
    document_number = models.CharField(max_length=50, default='27/14-', verbose_name="Підготовлений № документа")
    process_date = models.DateField(verbose_name="Дата опрацювання")
    work_date = models.DateField(verbose_name="Дата проведення робіт")
    author = models.CharField(max_length=255, verbose_name="Виконавець (ПІБ)")
    note = models.TextField(blank=True, null=True, verbose_name="Примітки")
    created_at = models.DateField(auto_now_add=True, verbose_name="Дата внесення в систему")

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
    unit = models.ForeignKey('Unit', on_delete=models.CASCADE, verbose_name="Військова частина")
    work_type = models.CharField(max_length=20, choices=WorkTypeChoices.choices, default=WorkTypeChoices.IK, verbose_name="Тип роботи")
    oids = models.ManyToManyField('OID', verbose_name="Об’єкти інформаційної діяльності")
    incoming_number = models.CharField(verbose_name="Вхідний номер заявки", max_length=50)
    incoming_date = models.DateField(verbose_name="Дата заявки")
    status = models.CharField(max_length=30, choices=StatusChoices.choices, default=StatusChoices.NEW, verbose_name="Поточний стан ОІД")
    note = models.TextField(verbose_name="Примітки", blank=True, null=True)

    def __str__(self):
        return f"{self.incoming_number} — {self.get_status_display()}"

class WorkRequestItem(models.Model):
    request = models.ForeignKey(WorkRequest, on_delete=models.CASCADE, related_name="items")
    oid = models.ForeignKey('OID', on_delete=models.CASCADE)
    work_type = models.CharField(max_length=20, choices=WorkTypeChoices.choices, default=WorkTypeChoices.IK, verbose_name="Тип роботи")

    def __str__(self):
        return f"{self.oid} — {self.work_type}"


# нові процесси
class AttestationRegistration(models.Model):
    units = models.ManyToManyField("Unit", verbose_name="Військові частини")
    oids = models.ManyToManyField("OID", through='AttestationItem', verbose_name="ОІД що реєструються")
    registration_number = models.CharField(max_length=50, blank=True, null=True, verbose_name="Реєстраційний номер листа до ДССЗЗІ")
    process_date = models.DateField(verbose_name="Дата відправки на реєстрацію в ДССЗЗІ")
    attachment = models.FileField(upload_to="attestation_docs/", blank=True, null=True, verbose_name="Файл (опційно)")
    note = models.TextField(blank=True, null=True, verbose_name="Примітка")

    def __str__(self):
        return f"Акти від {self.process_date}"

class AttestationItem(models.Model):
    registration = models.ForeignKey(AttestationRegistration, on_delete=models.CASCADE)
    oid = models.ForeignKey("OID", on_delete=models.CASCADE, verbose_name="ОІД")
    document_number = models.CharField(max_length=50, verbose_name="Номер Акту Атестації")

    def __str__(self):
        return f"{self.oid.name} — {self.document_number}"

class AttestationResponse(models.Model):
    registration = models.OneToOneField(AttestationRegistration, on_delete=models.CASCADE)
    registered_number = models.CharField(max_length=50, verbose_name="Зареєстровано за номером")
    registered_date = models.DateField(verbose_name="Дата реєстрації")
    note = models.TextField(blank=True, null=True, verbose_name="Примітка")
    recorded_date = models.DateField(auto_now_add=True, verbose_name="Дата внесення")

class TripResultForUnit(models.Model):
    units = models.ManyToManyField("Unit", verbose_name="Військові частини призначення")
    oids = models.ManyToManyField("OID", verbose_name="ОІД призначення")
    
    documents = models.ManyToManyField("Document", verbose_name="Документи до відправки")
    
    process_date = models.DateField(verbose_name="Дата відправки до частини")
    attachment = models.FileField(upload_to="trip_results_docs/", blank=True, null=True, verbose_name="Файл (опційно)")
    note = models.TextField(blank=True, null=True, verbose_name="Примітка")
    # пропозиція додавати відрядження 
    # trip = models.ForeignKey(Trip, on_delete=models.CASCADE, verbose_name="Відрядження", related_name='trip_result')
    trip = models.ForeignKey('Trip', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Пов’язане відрядження")
    related_request = models.ForeignKey('WorkRequest', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Пов’язана заявка")

    def __str__(self):
        return f"Відправка {self.process_date} — {self.documents.count()} документів"

# Технічне завдання 
class TechnicalTask(models.Model):

    oid = models.ForeignKey('OID', on_delete=models.CASCADE, verbose_name="ОІД", related_name='TechnicalTasks')
    input_number = models.CharField(max_length=50, verbose_name="Вхідний номер")
    input_date = models.DateField(verbose_name="Вхідна дата")
    reviewed_by = models.CharField(max_length=255, verbose_name="Хто ознайомився")
    # reviewed_by = models.ForeignKey('Person', on_delete=models.SET_NULL, null=True, verbose_name="Хто ознайомився")
    
    review_result = models.CharField(max_length=30, choices=ReviewResultChoices.choices, default=ReviewResultChoices.REVIEWED, verbose_name="Результат розгляду")
    note = models.TextField(blank=True, null=True, verbose_name="Примітка")

    created_at = models.DateField(auto_now_add=True, verbose_name="Дата додання інформації")
    def __str__(self):
        return f"{self.input_number} / {self.input_date}"

