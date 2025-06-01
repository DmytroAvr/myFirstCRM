from django.db import models
from multiselectfield import MultiSelectField
from django.utils import timezone
from django.db.models import Q

# --- CONSTANTS / CHOICES ---
# Краще зберігати вибори в окремих файлах або в самих моделях, якщо вони специфічні для моделі.
# Для загальних виборів, які використовуються в кількох моделях, можна тримати їх тут.

class SecLevelChoices(models.TextChoices):
    S = 'Таємно', 'Таємно' 
    TS = 'Цілком таємно', 'Цілком таємно'
    DSK = 'ДСК', 'Для службового користування'
 
class OIDStatusChoices(models.TextChoices):
    NEW = 'створюється', 'Створюється'
    RECEIVED_TZ = 'отримано ТЗ', 'Отримано ТЗ' # Додано з твого опису "Стан ОІД"
    RECEIVED_REQUEST = 'отримано заявку', 'Отримано Заявку' # Додано з твого опису "Стан ОІД"
    ACTIVE = 'активний', 'Активний (наступне проведення робіт)'
    TERMINATED = 'призупинено', 'Призупинено'
    CANCELED = 'скасований', 'Скасований'

class WorkRequestStatusChoices(models.TextChoices): # Перейменовано для кращої читабельності
    PENDING = 'очікує', 'Очікує' # Згідно опису "очікує – тільки введена"
    IN_PROGRESS = 'в роботі', 'В роботі' # Згідно опису "в роботі – заплановано відрядження"
    COMPLETED = 'виконано', 'Виконано' # Згідно опису "виконано – внесена інформацію по опрацьованих документах"
    CANCELED = 'скасовано', 'Скасовано' # Згідно опису "скасовано – заявка втратила чинність"

class OIDTypeChoices(models.TextChoices):
    PEMIN = 'ПЕМІН', 'ПЕМІН'
    SPEAK = 'МОВНА', 'МОВНА'

class WorkTypeChoices(models.TextChoices):
    ATTESTATION = 'Атестація', 'Атестація'
    IK = 'ІК', 'ІК'
    
class DocumentReviewResultChoices(models.TextChoices): 
    READ = 'працювати', 'Опрацювати'
    AWAITING_DOCS = 'очікує в папері', 'Очікує в папері'
    APPROVED = 'погоджено', 'Погоджено'
    FOR_REVISION = 'на доопрацювання', 'На доопрацювання'

class AttestationRegistrationStatusChoices(models.TextChoices):
    SENT = 'sent', 'Відправлено, очікує відповіді'
    RESPONSE_RECEIVED = 'received', 'Відповідь отримано'
    # PARTIALLY_RECEIVED = 'partially_received', 'Відповідь отримано частково' # Можна додати, якщо потрібно
    CANCELED = 'canceled', 'Скасовано (відправку)'
    

# --- Models ---

class TerritorialManagement(models.Model):
    code = models.CharField(max_length=50, unique=True, verbose_name="Код управління")
    name = models.CharField(max_length=255, verbose_name="Назва управління")
    note = models.TextField(verbose_name="Примітка", blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Територіальне управління"
        verbose_name_plural = "Територіальні управління"

class UnitGroup(models.Model):
    """
    Група військових частин
    Атрибути: Назва групи, Перелік частин що входять до складу групи, Примітка
    Зв'язки: Має кілька частин
    """
    name = models.CharField(max_length=255, unique=True, verbose_name="Назва групи частин")
    # units = models.ManyToManyField(Unit, blank=True, verbose_name="Військові частини в групі", related_name="groups_they_belong_to") 
    note = models.TextField(verbose_name="Примітка", blank=True, null=True)
    # Зв'язок Many-to-Many з Unit буде визначено в моделі Unit

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Група військових частин (для відряджень)"
        verbose_name_plural = "Групи військових частин (для відряджень)"

class Unit(models.Model): 
    """
    Військова частина
    Атрибути: Код частини, Назва, Місто розташування, Відстань з ГУ до міста розташування,
              Відношення до груп військових частин, Примітки
    Зв'язки: Містить кілька ОІД, Прив'язка до відряджень, Прив'язка до наданих "заявок на проведення робіт"
    """
    territorial_management = models.ForeignKey(
        TerritorialManagement, 
        on_delete=models.SET_NULL, # Якщо ТУ видаляється, частина може залишитися, але без прив'язки до ТУ.
        null=True, 
        blank=True, 
        verbose_name="Територіальне управління",
        related_name='units' # Дозволить отримати всі частини для ТУ: `tu_instance.units.all()`
    )
    code = models.CharField(max_length=50, unique=True, verbose_name="Код частини (номер)")
    name = models.CharField(max_length=255, verbose_name="Назва військової частини", blank=True, null=True) # Можливо, назва не завжди потрібна, якщо є код
    city = models.CharField(max_length=100, verbose_name="Місто розташування") # Збільшив max_length для міст
    distance_from_gu = models.PositiveIntegerField(verbose_name="Відстань від ГУ (км)", blank=True, null=True) # Змінив на PositiveIntegerField
    unit_groups = models.ManyToManyField(
        UnitGroup, 
        blank=True, 
        verbose_name="Групи військових частин",
        related_name='units' # Дозволить отримати всі частини для групи: `group_instance.units.all()`
        # related_name='units_in_group' # Дозволить отримати всі частини для групи: `group_instance.units.all()`
    )
    note = models.TextField(verbose_name="Примітки", blank=True, null=True)

    def __str__(self):
        return f"{self.code} - {self.name or self.city}" # Виводимо код і назву/місто

    class Meta:
        verbose_name = "Військова частина"
        verbose_name_plural = "Військові частини"

class OID(models.Model): 
    """
    Об'єкт інформаційної діяльності (ОІД)
    Атрибути: Тип (МОВНА або ПЕМІН), Шифр, Повна назва, Приміщення, Стан, Має загальну історію робіт (агрегація)
    Зв'язки: Прив'язаний до частини ТУ, Має історію робіт, Має історію відрядження, Має опрацьовані документи
    Додатково - привязка атетсація, стан,
    """
    unit = models.ForeignKey(
        Unit, 
        on_delete=models.CASCADE, 
        verbose_name="Військова частина",
        related_name='oids' # Дозволить отримати всі ОІД для частини: `unit_instance.oids.all()`
    )
    oid_type = models.CharField(max_length=10, choices=OIDTypeChoices.choices, verbose_name="Тип ОІД")
    cipher = models.CharField(max_length=100, verbose_name="Шифр ОІД", unique=True) # Додав шифр, як вказано в описі
    sec_level = models.CharField(max_length=15, choices=SecLevelChoices.choices, verbose_name="Гриф")
    full_name = models.CharField(max_length=255, verbose_name="Повна назва ОІД", blank=True, null=True) # Змінив name на full_name
    room = models.CharField(max_length=255, verbose_name="Приміщення №")
    status = models.CharField(max_length=30, choices=OIDStatusChoices.choices, default=OIDStatusChoices.NEW, verbose_name="Поточний стан ОІД")
    note = models.TextField(verbose_name="Примітка", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата створення запису")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата останнього оновлення")
	# Прив'язка до першого та останнього документа для відстеження
    # OneToOneField для created_by_document може бути проблематичним, якщо один документ може "створити" кілька ОІД.
    # Краще використовувати ForeignKey, і вже на рівні логіки (service/views) забезпечувати, що це перший документ.
    # Я видалив created_by_document і latest_document, оскільки їх можна отримати через related_name
    # до моделі Document (наприклад, oid_instance.documents.order_by('process_date').first()).
    # Це зменшує дублювання даних і забезпечує узгодженість.

    def __str__(self):
        return f"{self.cipher} ({self.get_oid_type_display()}) - {self.unit.code}"

    class Meta:
        verbose_name = "Об’єкт інформаційної діяльності (ОІД)"
        verbose_name_plural = "Об’єкти інформаційної діяльності (ОІД)"

class Person(models.Model):
    """
    Виконавець
    Атрибути: ПІБ, Посада, Активність, Історія участі у відрядженнях / роботах / документах
    Зв'язки: Може бути учасником відрядження, Може бути виконавцем роботи, Може бути автором документа
    """
    full_name = models.CharField(max_length=255, verbose_name="Прізвище, ім'я") # Змінив name на full_name
    position = models.CharField(max_length=255, verbose_name="Посада")
    is_active = models.BooleanField(default=True, verbose_name="Активний") # Додав поле активності

    def __str__(self):
        return self.full_name

    class Meta:
        verbose_name = "Виконавець"
        verbose_name_plural = "Виконавці"

class WorkRequest(models.Model):
    """
    Заявка на проведення робіт
    Атрибути: Вхідний обліковий номер заявки, Вхідна дата заявки, Військова частина,
              ОІД (може бути кілька ОІД), Запитуваний тип роботи (Атестація / ІК),
              Статус заявки, Примітки
    """
    unit = models.ForeignKey(
        Unit, 
        on_delete=models.CASCADE, 
        verbose_name="Військова частина",
        related_name='work_requests' # Дозволить отримати всі заявки для частини
    )
    incoming_number = models.CharField(verbose_name="Вхідний обліковий номер заявки", max_length=50, unique=False)
    incoming_date = models.DateField(verbose_name="Вхідна дата заявки", default=timezone.now) 
    note = models.TextField(verbose_name="Примітки", blank=True, null=True)

    status = models.CharField(
        max_length=30, 
        choices=WorkRequestStatusChoices.choices, 
        default=WorkRequestStatusChoices.PENDING, 
        verbose_name="Статус заявки"
    )
    # Зв'язок Many-to-Many з OID буде через WorkRequestItem, щоб можна було вказувати тип роботи для кожного ОІД в заявці.
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата створення запису")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата останнього оновлення")

    def __str__(self):
        return f"в/ч {self.unit.code} Заявка вх.№{self.incoming_number} від {self.incoming_date} ({self.get_status_display()})"

    class Meta:
        verbose_name = "Заявка на проведення робіт"
        verbose_name_plural = "Заявки на проведення робіт"
        unique_together = ('unit', 'incoming_number') # Заявка унікальна в межах частини

class WorkRequestItem(models.Model):
    """
    Елемент заявки на проведення робіт.
    Дозволяє вказати конкретний ОІД та тип роботи для нього в рамках однієї заявки.
    """
    request = models.ForeignKey(
        WorkRequest, 
        on_delete=models.CASCADE, 
        related_name="items", 
        verbose_name="Заявка"
    )
    oid = models.ForeignKey(
        OID, 
        on_delete=models.CASCADE, 
        related_name='work_request_items', # Дозволить знайти всі елементи заявок, що стосуються цього ОІД
        verbose_name="Об’єкт інформаційної діяльності"
    )
    work_type = models.CharField(max_length=20, choices=WorkTypeChoices.choices, verbose_name="Запитуваний тип роботи")
    # Статус для окремого ОІД у заявці може бути корисним для відстеження прогресу по кожному ОІД.
    # Проте, твоя логіка update_request_status вже працює з цим статусом, тому залишаємо.
    status = models.CharField(
        max_length=30, 
        choices=WorkRequestStatusChoices.choices, 
        default=WorkRequestStatusChoices.PENDING, 
        verbose_name="Статус опрацювання ОІД в заявці"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата створення запису")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата останнього оновлення")

    class Meta:
        unique_together = ('request', 'oid', 'work_type') # Один ОІД не може мати двічі одну і ту ж роботу в одній заявці
        verbose_name = "Елемент заявки"
        verbose_name_plural = "Елементи заявки"

    def __str__(self):
        return f"{self.oid.cipher} - {self.get_work_type_display()} ({self.get_status_display()})"

    # Твоя логіка оновлення статусу заявки:
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.update_request_status()

    def update_request_status(self):
        # Якщо всі елементи заявки "Виконано" або "Скасовано", то і заявка "Виконано" або "Скасовано"
        all_items = self.request.items.all()
        completed_items = all_items.filter(status=WorkRequestStatusChoices.COMPLETED).count()
        canceled_items = all_items.filter(status=WorkRequestStatusChoices.CANCELED).count()
        total_items = all_items.count()

        if completed_items + canceled_items == total_items:
            if completed_items == total_items:
                self.request.status = WorkRequestStatusChoices.COMPLETED
            elif canceled_items == total_items:
                self.request.status = WorkRequestStatusChoices.CANCELED
            else: # Частина виконана, частина скасована - вважаємо виконаною (або можна ввести "Частково виконано")
                self.request.status = WorkRequestStatusChoices.COMPLETED 
        elif all_items.filter(status=WorkRequestStatusChoices.IN_PROGRESS).exists() or \
             all_items.filter(status=WorkRequestStatusChoices.PENDING).exists():
            self.request.status = WorkRequestStatusChoices.IN_PROGRESS # Якщо хоча б один елемент в роботі або очікує
        else:
            self.request.status = WorkRequestStatusChoices.PENDING # За замовчуванням
        self.request.save()

class DocumentType(models.Model):
    """
    Тип документа
    Для динамічного визначення, які документи очікуються при опрацюванні конкретного ОІД.
    """
    # oid_type = models.CharField(max_length=30, choices=OIDTypeChoices.choices, default=OIDTypeChoices.SAMEDOC, verbose_name="Тип ОІД")
    # work_type = models.CharField(max_length=30, choices=WorkTypeChoices.choices, default=WorkTypeChoices.SAMEDOC, verbose_name="Тип робіт")

    oid_type = models.CharField(
        "Тип ОІД",
        max_length=20,
        choices=[('МОВНА', 'МОВНА'), ('ПЕМІН', 'ПЕМІН'), ('СПІЛЬНИЙ', 'СПІЛЬНИЙ')],
    )
    work_type = models.CharField(
        "Тип робіт",
        max_length=20,
        choices=[('Атестація', 'Атестація'), ('ІК', 'ІК'), ('СПІЛЬНИЙ', 'СПІЛЬНИЙ')], 
    )
    name = models.CharField("Назва документа", max_length=100) # Прибрав unique=True, оскільки назва може повторюватись для різних типів ОІД/робіт (наприклад, "План пошуку ЗП")
    has_expiration = models.BooleanField("Має термін дії", default=False) # Змінив на Boolean
    duration_months = models.PositiveIntegerField(
        "Тривалість (у місяцях)", 
        default=0, 
        help_text="Якщо документ має термін дії, вкажіть тривалість у місяцях. Якщо не обмежений — залишити 0."
    )
    is_required = models.BooleanField("Обов'язковість", default=True) # Додав поле обов'язковості

    class Meta:
        unique_together = ('oid_type', 'work_type', 'name') # Документ унікальний для комбінації тип ОІД/робота/назва
        verbose_name = "Тип документа"
        verbose_name_plural = "Типи документів"
        ordering = ['oid_type', 'work_type', 'name'] # Додано сортування
    def __str__(self):
    #     return f"{self.name} ({self.oid_type}, {self.work_type})"
        return f"{self.name} ({self.get_oid_type_display()}, {self.get_work_type_display()})"

class AttestationRegistration(models.Model):
    """
    Відправка пакету актів атестації на реєстрацію в ДССЗЗІ (вихідний лист).
    """
    units = models.ManyToManyField(
        Unit,
        verbose_name="Військові частини (акти яких включено)",
        related_name='sent_for_attestation_registrations',
        blank=True 
    )
    outgoing_letter_number = models.CharField(
        max_length=50,
        verbose_name="Вихідний номер листа до ДССЗЗІ"
    )
    outgoing_letter_date = models.DateField(
        verbose_name="Дата вихідного листа"
    )
    sent_by = models.ForeignKey(
        Person,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Хто відправив лист",
        related_name='sent_attestation_packages'
    )
    status = models.CharField(
        max_length=25,
        choices=AttestationRegistrationStatusChoices.choices,
        default=AttestationRegistrationStatusChoices.SENT,
        verbose_name="Статус відправки"
    )
    # Поле attachment видалено
    # attachment = models.FileField(...) 
    note = models.TextField(
        blank=True,
        null=True,
        verbose_name="Примітка до відправки"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата створення запису")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата останнього оновлення")

    def __str__(self):
        return f"Відправка до ДССЗЗІ №{self.outgoing_letter_number} від {self.outgoing_letter_date.strftime('%d.%m.%Y')}"

    class Meta:
        verbose_name = "Відправка актів на реєстрацію (ДССЗЗІ)"
        verbose_name_plural = "Відправки актів на реєстрацію (ДССЗЗІ)"
        ordering = ['-outgoing_letter_date', '-id']     

class AttestationResponse(models.Model):
    """
    Відповідь від ДССЗЗІ на відправку актів атестації (вхідний лист).
    """
    attestation_registration_sent = models.OneToOneField( 
        AttestationRegistration, 
        on_delete=models.CASCADE, 
        verbose_name="Пов'язана відправка (вихідний лист)",
        related_name='response_received' 
    )
    response_letter_number = models.CharField(
        max_length=50, 
        verbose_name="Вхідний номер листа-відповіді"
    )
    response_letter_date = models.DateField(
        verbose_name="Дата вхідного листа-відповіді"
    )
    received_by = models.ForeignKey(
        Person,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Хто отримав/вніс відповідь",
        related_name='processed_attestation_responses'
    )
    note = models.TextField(blank=True, null=True, verbose_name="Примітка до відповіді")
    created_at = models.DateTimeField(auto_now_add=True) 
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Відповідь №{self.response_letter_number} від {self.response_letter_date.strftime('%d.%m.%Y')} на вих. №{self.attestation_registration_sent.outgoing_letter_number}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Після збереження відповіді, оновлюємо статус батьківської відправки
        if self.attestation_registration_sent:
            # Тут можна додати логіку перевірки, чи всі акти з відправки отримали реєстраційні номери,
            # щоб встановити статус RESPONSE_RECEIVED або PARTIALLY_RECEIVED.
            # Поки що просто змінюємо на RESPONSE_RECEIVED.
            if self.attestation_registration_sent.status == AttestationRegistrationStatusChoices.SENT:
                self.attestation_registration_sent.status = AttestationRegistrationStatusChoices.RESPONSE_RECEIVED
                self.attestation_registration_sent.save(update_fields=['status', 'updated_at'])


    class Meta:
        verbose_name = "Відповідь на реєстрацію (ДССЗЗІ)"
        verbose_name_plural = "Відповіді на реєстрацію (ДССЗЗІ)"
        ordering = ['-response_letter_date', '-id']
   
class Document(models.Model):
    """
    Опрацьовані документи
    Залежить від типу ОІД та виду робіт.
    """
    oid = models.ForeignKey(
        OID, 
        on_delete=models.CASCADE, 
        verbose_name="ОІД",
        related_name='documents'
    )
    work_request_item = models.ForeignKey(
        WorkRequestItem, 
        on_delete=models.SET_NULL, 
        blank=True, 
        null=True, 
        verbose_name="Елемент заявки",
        related_name='produced_documents'
    )
    document_type = models.ForeignKey(
        DocumentType, 
        on_delete=models.PROTECT,
        verbose_name="Тип документа"
    )
    document_number = models.CharField(max_length=50, default='27/14-', verbose_name="Підготовлений № документа")
    process_date = models.DateField(verbose_name="Дата опрацювання") # Дата внесення документа
    work_date = models.DateField(verbose_name="Дата проведення робіт") # Дата, коли роботи фактично проводилися
    author = models.ForeignKey(
        Person, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        verbose_name="Автор документа",
        related_name='authored_documents'
    )
    attachment = models.FileField(upload_to="attestation_docs/", blank=True, null=True, verbose_name="Прикріплений файл (Опційно)")
    note = models.TextField(blank=True, null=True, verbose_name="Примітки")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата створення запису")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата останнього оновлення")
    expiration_date = models.DateField(verbose_name="Дата завершення дії", blank=True, null=True)

    # --- НОВІ ПОЛЯ для реєстрації в ДССЗЗІ (для актів атестації) ---
    # Посилання на запис про відправку (вихідний лист)
    attestation_registration_sent = models.ForeignKey(
        AttestationRegistration,
        on_delete=models.SET_NULL, # Якщо запис про відправку видаляється, інформація в документі залишається, але без зв'язку
        null=True,
        blank=True,
        verbose_name="Відправлено на реєстрацію ДССЗЗІ (в складі листа)",
        related_name="registered_documents" # Дозволить отримати всі документи в цій відправці
    )
    # Номер, присвоєний ДССЗЗІ цьому конкретному акту
    dsszzi_registered_number = models.CharField(
        max_length=50, 
        blank=True, 
        null=True, 
        verbose_name="Зареєстрований номер в ДССЗЗІ (для цього акту)"
    )
    # Дата, якою ДССЗЗІ зареєстрував цей акт
    dsszzi_registered_date = models.DateField(
        blank=True, 
        null=True, 
        verbose_name="Дата реєстрації в ДССЗЗІ (для цього акту)"
    )
    # Можна додати статус реєстрації саме для цього документа, якщо потрібно більш детально
    # dsszzi_document_status = models.CharField(max_length=20, choices=..., null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.document_type and self.document_type.has_expiration and self.document_type.duration_months > 0 and self.work_date:
            # Приблизне обчислення, можна уточнити за допомогою dateutil.relativedelta
            from dateutil.relativedelta import relativedelta 
            self.expiration_date = self.work_date + relativedelta(months=self.document_type.duration_months)
        else:
            # Якщо у документа немає терміну дії або не вказана дата робіт, дата завершення дії не встановлюється
             if not (self.document_type and self.document_type.has_expiration and self.document_type.duration_months > 0):
                self.expiration_date = None # Очищаємо, якщо умови не виконані
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.document_type.name} / {self.document_number} (ОІД: {self.oid.cipher})"

    class Meta:
        verbose_name = "Опрацьований документ"
        verbose_name_plural = "Опрацьовані документи"
        ordering = ['-process_date', '-work_date']
        
class Trip(models.Model):
    """
    Відрядження
    Атрибути: Дата відрядження з / по, Призначення (до яких військових частин),
              Які ОІД військових частин, Особи у відрядження, Мета відрядження
    """
    units = models.ManyToManyField(
        Unit, 
        verbose_name="Військові частини призначення",
        related_name='trips' # Дозволить знайти всі відрядження для частини
    )
    oids = models.ManyToManyField(
        OID, 
        verbose_name="Об’єкти інформаційної діяльності, задіяні у відрядженні",
        related_name='trips' # Дозволить знайти всі відрядження, що стосуються цього ОІД
    )
    # Зв'язок з WorkRequest через WorkRequestItem вже є.
    # Якщо відрядження планується на основі заявок, то work_requests можна отримати через items
    # або зробити ManyToManyField для прямого зв'язку, але це може призвести до дублювання інформації.
    # Якщо work_requests - це "мета" відрядження, то краще залишити як є.
    work_requests = models.ManyToManyField(
        WorkRequest, 
        verbose_name="Пов'язані заявки на проведення робіт",
        related_name='trips' # Дозволить знайти всі відрядження, пов'язані з заявкою
    ) 
    start_date = models.DateField(verbose_name="Дата початку відрядження")
    end_date = models.DateField(verbose_name="Дата завершення відрядження")
    persons = models.ManyToManyField(
        Person, 
        verbose_name="Особи у відрядженні",
        related_name='trips' # Дозволить знайти всі відрядження, в яких брала участь особа
    )
    purpose = models.TextField(blank=True, null=True, verbose_name="Мета відрядження")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата створення запису")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата останнього оновлення")

    def __str__(self):
        unit_names = ", ".join(unit.name for unit in self.units.all())
        return f"Відрядження {self.start_date}—{self.end_date} до {unit_names or 'немає частин'}"

    class Meta:
        verbose_name = "Відрядження"
        verbose_name_plural = "Відрядження"

class OIDStatusChange(models.Model):
    """
    Історія змін статусу ОІД.
    """
    oid = models.ForeignKey(
        OID, 
        on_delete=models.CASCADE, 
        verbose_name="ОІД",
        related_name='status_changes' # Дозволить отримати всі зміни статусу для ОІД
    )
    # unit можна отримати через oid.unit, тому не дублюємо.
    old_status = models.CharField(max_length=30, verbose_name="Попередній статус")
    new_status = models.CharField(max_length=30, verbose_name="Новий статус")
    # incoming_number та reason можуть бути частиною нотатки, або окремим полем.
    # Якщо incoming_number - це номер документа, який ініціював зміну, то краще зв'язати з Document.
    initiating_document = models.ForeignKey(
        Document, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        verbose_name="Документ, що ініціював зміну статусу",
        related_name='oid_status_changes'
    )
    reason = models.TextField(blank=True, null=True, verbose_name="Причина зміни")
    changed_by = models.ForeignKey(
        Person, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        verbose_name="Хто змінив",
        related_name='oid_status_changes'
    )
    changed_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата зміни") # Змінив на DateTimeField
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата створення запису")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата останнього оновлення")

    def __str__(self):
        return f"{self.oid.cipher}: {self.old_status} → {self.new_status} ({self.changed_at.strftime('%Y-%m-%d')})"

    class Meta:
        verbose_name = "Зміна статусу ОІД"
        verbose_name_plural = "Зміни статусу ОІД"
        ordering = ['-changed_at'] # За замовчуванням сортувати за датою зміни

# --- Додаткові сутності, які були в оригінальному файлі, але не були інтегровані в бізнес-логіку ---

     
class TripResultForUnit(models.Model):
    """
    Результати відрядження, що відправляються до військових частин.
    """
    # Зв'язок з Trip є важливим, оскільки це "результат відрядження".
    trip = models.ForeignKey(
        Trip, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        verbose_name="Пов’язане відрядження",
        related_name='trip_results_for_units' # Дозволить отримати всі результати для відрядження
    )
    units = models.ManyToManyField(
        Unit, 
        verbose_name="Військові частини призначення",
        related_name='received_trip_results'
    )
    oids = models.ManyToManyField(
        OID, 
        verbose_name="ОІД призначення",
        related_name='received_trip_results'
    )
    documents = models.ManyToManyField(
        Document, 
        verbose_name="Документи до відправки",
        related_name='sent_in_trip_results' # Дозволить дізнатися, в яких результатах відрядження був відправлений документ
    )
    outgoing_letter_number = models.CharField(
        max_length=50,
        verbose_name="Вих. номер супровідного листа"
    )
    outgoing_letter_date = models.DateField(
        verbose_name="Вих. дата супровідного листа"
    )
    process_date = models.DateField(verbose_name="Дата відправки до частини")
    note = models.TextField(blank=True, null=True, verbose_name="Примітка")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата створення запису")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата останнього оновлення")
    # related_request - можна отримати через trip.work_requests.all() або через documents.work_request_item.request
    # Тому, якщо це не критично для прямого доступу, можна прибрати для уникнення дублювання.
    # related_request = models.ForeignKey('WorkRequest', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Пов’язана заявка")

    def __str__(self):
        return f"Відправка результатів від {self.process_date}"

    class Meta:
        verbose_name = "Результати відрядження для частини"
        verbose_name_plural = "Результати відрядження для частин"

class TechnicalTask(models.Model):
    """
    Технічне завдання
    """
    oid = models.ForeignKey(
        OID, 
        on_delete=models.CASCADE, 
        verbose_name="ОІД", 
        related_name='technical_tasks' 
    )
    input_number = models.CharField(max_length=50, verbose_name="Вхідний номер")
    input_date = models.DateField(verbose_name="Вхідна дата")
    read_till_date = models.DateField(verbose_name="Опрацювати до")
    reviewed_by = models.ForeignKey(
        Person, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        verbose_name="Хто ознайомився",
        related_name='reviewed_technical_tasks' # Додав related_name
    )
    review_result = models.CharField(
        max_length=30, 
        choices=DocumentReviewResultChoices.choices, 
        default=DocumentReviewResultChoices.APPROVED, 
        verbose_name="Результат розгляду"
    )
    note = models.TextField(blank=True, null=True, verbose_name="Примітка")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата створення запису")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата останнього оновлення")

    def __str__(self):
        return f"ТЗ №{self.input_number} для {self.oid.cipher}"
