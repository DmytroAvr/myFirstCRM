from django.db import models


class ManagementUnit(models.Model):  # Технічне управління   -територіальне управління
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class MBase(models.Model):  # Військова Частина
    name = models.CharField(max_length=255)
    management_unit = models.ForeignKey(ManagementUnit, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.management_unit} - {self.name}"


class OID(models.Model):  # Об'єкт інформаційної діяльності
    TYPE_CHOICES = [('МОВНА', 'МОВНА'), ('ПЕОМ', 'ПЕОМ')]
    STATUS_CHOICES = [
        ('створюється', 'створюється'),
        ('атестована', 'атестована'),
        ('в експлуатації', 'в експлуатації'),
        ('обробка припинена', 'обробка припинена'),
        ('скасовано', 'скасовано'),
    ]

    MBase = models.ForeignKey(MBase, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    OID_type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    # OID_type = models.CharField(max_length=140, default='SOME STRING')
    status = models.CharField(max_length=100, choices=STATUS_CHOICES)
    location = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class WorkHistory(models.Model):  # Історія робіт
    oid = models.ForeignKey(OID, on_delete=models.CASCADE)
    description = models.TextField()
    date = models.DateField()
    result = models.TextField(blank=True)

    def __str__(self):
        return f"{self.oid.name} — {self.date}"


class Task(models.Model):  # Заявка / Робота
    oid = models.ForeignKey(OID, on_delete=models.CASCADE)
    task_type = models.CharField(max_length=255)
    deadline = models.DateField()
    is_completed = models.BooleanField(default=False)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.task_type} для {self.oid.name}"


class Trip(models.Model):  # Виїзд
    oid = models.ForeignKey(OID, on_delete=models.CASCADE)
    date = models.DateField()
    purpose = models.TextField()

    def __str__(self):
        return f"Виїзд до {self.oid.name} ({self.date})"


class Personnel(models.Model):  # Залучений персонал
    full_name = models.CharField(max_length=255)
    position = models.CharField(max_length=255)
    trips = models.ManyToManyField(Trip, blank=True)

    def __str__(self):
        return self.full_name

# Додаю

class Document(models.Model):
    oid = models.ForeignKey(OID, on_delete=models.CASCADE)
    DOCUMENT_TYPES = [
        ('program', 'Програма'),
        ('plan', 'План'),
        ('act', 'Акт'),
        ('other', 'Інше'),
    ]
    work = models.ForeignKey(WorkHistory, on_delete=models.CASCADE, related_name='documents')
    name = models.CharField(max_length=20, choices=DOCUMENT_TYPES)
    doc_number = models.CharField(max_length=100)
    doc_date = models.DateField()
    expiration_date = models.DateField()


    def __str__(self):
        return f"{self.expiration_date()} №{self.doc_number}"