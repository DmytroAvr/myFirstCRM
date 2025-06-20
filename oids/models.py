from django.db import models
from multiselectfield import MultiSelectField
from django.utils import timezone
import datetime
from django.db.models import Q
from simple_history.models import HistoricalRecords
	
# --- CONSTANTS / CHOICES ---
# Краще зберігати вибори в окремих файлах або в самих моделях, якщо вони специфічні для моделі.
# Для загальних виборів, які використовуються в кількох моделях, можна тримати їх тут.


def add_working_days(start_date, days_to_add):
    """
    Додає вказану кількість робочих днів до початкової дати.
    start_date - це дата, ПІСЛЯ якої починається відлік.
    days_to_add - кількість робочих днів, які потрібно додати.
    Функція повертає N-й робочий день після start_date.
    """
    if not isinstance(start_date, datetime.date):
        raise ValueError("start_date має бути об'єктом datetime.date")
    if not isinstance(days_to_add, int) or days_to_add <= 0: # days_to_add має бути > 0
        # Якщо days_to_add = 0, то це має бути перший робочий день після start_date,
        # що потребує іншої логіки або days_to_add=1 для "наступного робочого дня".
        # Для нашого випадку "10-й робочий день ПІСЛЯ end_date" -> days_to_add буде 10.
        raise ValueError("days_to_add має бути позитивним цілим числом")

    current_day_iterator = start_date
    work_days_counted = 0
    while work_days_counted < days_to_add:
        current_day_iterator += datetime.timedelta(days=1)
        if current_day_iterator.weekday() < 5: # 0-Mon, 4-Fri
            work_days_counted += 1
    return current_day_iterator


 # Твоя допоміжна функція (залишається без змін, але буде викликатися в AJAX view)


class SecLevelChoices(models.TextChoices):
    S = 'Таємно', 'Таємно' 
    TS = 'Цілком таємно', 'Цілком таємно'
    # DSK = 'ДСК', 'Для службового користування'
 
class OIDStatusChoices(models.TextChoices):
    NEW = 'створюється', 'Створюється'
    RECEIVED_TZ = 'отримано ТЗ', 'Отримано ТЗ' # Додано з твого опису "Стан ОІД"
    RECEIVED_REQUEST = 'отримано заявку', 'Отримано Заявку' # Додано з твого опису "Стан ОІД"
    ACTIVE = 'активний', 'Активний (В дії)'
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
    READ = 'опрацювати', 'Опрацювати'
    AWAITING_DOCS = 'очікуємо в папері', 'Очікуємо в папері'
    APPROVED = 'погоджено', 'Погоджено'
    FOR_REVISION = 'на доопрацювання', 'На доопрацювання'

class AttestationRegistrationStatusChoices(models.TextChoices):
    SENT = 'sent', 'Відправлено, очікує відповіді'
    RESPONSE_RECEIVED = 'received', 'Відповідь отримано'
    # PARTIALLY_RECEIVED = 'partially_received', 'Відповідь отримано частково' # Можна додати, якщо потрібно
    CANCELED = 'canceled', 'Скасовано (відправку)'
    
class PeminSubTypeChoices(models.TextChoices):
    VARM = 'ВАРМ', 'ВАРМ'
    AS1Static = 'АС1Стаціонар', 'АС1 Стаціонар'
    AS1Portable = 'АС1Портативний', 'АС1 Портативний'    
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
    cipher = models.CharField(max_length=100, verbose_name="Шифр ОІД", unique=False) # Додав шифр, як вказано в описі
    sec_level = models.CharField(max_length=15, choices=SecLevelChoices.choices, verbose_name="Гриф")
    full_name = models.CharField(max_length=255, verbose_name="Повна назва ОІД", blank=True, null=True) # Змінив name на full_name
    room = models.CharField(max_length=255, verbose_name="Приміщення №")
    status = models.CharField(max_length=30, choices=OIDStatusChoices.choices, default=OIDStatusChoices.NEW, verbose_name="Поточний стан ОІД")
    note = models.TextField(verbose_name="Примітка", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата створення ОІД")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата останнього оновлення")
    pemin_sub_type = models.CharField(
        max_length=20, 
        choices=PeminSubTypeChoices.choices, 
        verbose_name="Тип ЕОТ",
        blank=True, # Дозволяє бути порожнім у формах
        null=True   # Дозволяє бути NULL в базі даних (для МОВНА ОІД)
    )
    serial_number = models.CharField(
        max_length=20, 
        verbose_name="Серійний номер", 
        blank=True, 
        null=True
    )
    inventory_number = models.CharField(
        max_length=20, 
        verbose_name="Інвентарний номер", 
        blank=True, 
        null=True
    )
    history = HistoricalRecords()

	# Прив'язка до першого та останнього документа для відстеження
    # OneToOneField для created_by_document може бути проблематичним, якщо один документ може "створити" кілька ОІД.
    # Краще використовувати ForeignKey, і вже на рівні логіки (service/views) забезпечувати, що це перший документ.
    # Я видалив created_by_document і latest_document, оскільки їх можна отримати через related_name
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
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата внесення заявки")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата останнього оновлення")
    history = HistoricalRecords()
    def check_and_update_status_based_on_documents(self):
        print(f"[WRI_STATUS_CHECKER] Checking WRI ID {self.id} (OID: {self.oid.cipher}, WorkType: {self.work_type}, CurrentStatus: {self.status})")
        if self.status in [WorkRequestStatusChoices.COMPLETED, WorkRequestStatusChoices.CANCELED]:
            print(f"[WRI_STATUS_CHECKER] WRI ID {self.id} already COMPLETED or CANCELED. No update needed.")
            return

        key_document_fulfilled = False
        wri_oid_type = self.oid.oid_type
        
        # Визначаємо необхідний тип ключового документа та умови його "виконання"
        # Це спрощена логіка, вам може знадобитися перевірка кількох обов'язкових типів документів
        
        if self.work_type == WorkTypeChoices.IK:
            # Для ІК, шукаємо "Висновок ІК" (припускаємо, що він має duration_months=20)
            # Або інший надійний спосіб ідентифікації типу документа "Висновок ІК"
            key_doc_types_ik = DocumentType.objects.filter(
                (Q(work_type=WorkTypeChoices.IK) | Q(work_type='СПІЛЬНИЙ')),
                (Q(oid_type=wri_oid_type) | Q(oid_type='СПІЛЬНИЙ')),
                # duration_months=20
				# duration_months=20  привязати до "duration_months" адже цей показник сталий та більш точний фільтр
                name__icontains="Висновок ІК" # Або більш точний фільтр, наприклад, по ID типу
            )
            if key_doc_types_ik.exists():
                if Document.objects.filter(
                    work_request_item=self, # Або просто oid=self.oid, якщо документи не завжди прив'язані до WRI
                    document_type__in=key_doc_types_ik
                ).exists():
                    key_document_fulfilled = True
                    print(f"[WRI_STATUS_CHECKER] Key document (IK Conclusion like) FOUND for WRI ID: {self.id}")
            else:
                print(f"[WRI_STATUS_CHECKER] No DocumentType configured for IK Conclusion for OID Type '{wri_oid_type}'.")

        elif self.work_type == WorkTypeChoices.ATTESTATION:
            # Для Атестації, шукаємо "Акт атестації" (припускаємо duration_months=60),
            # і він має бути зареєстрований в ДССЗЗІ.
            key_doc_types_att = DocumentType.objects.filter(
                (Q(work_type=WorkTypeChoices.ATTESTATION) | Q(work_type='СПІЛЬНИЙ')),
                (Q(oid_type=wri_oid_type) | Q(oid_type='СПІЛЬНИЙ')),
                # duration_months=60  привязати до "duration_months" адже цей показник сталий та більш точний фільтр
				name__icontains="Акт атестації" # Або більш точний фільтр
            )
            if key_doc_types_att.exists():
                if Document.objects.filter(
                    work_request_item=self, # Або oid=self.oid
                    document_type__in=key_doc_types_att,
                    dsszzi_registered_number__isnull=False, # Перевірка, що є номер реєстрації
                    dsszzi_registered_number__ne='',       # І він не порожній
                    dsszzi_registered_date__isnull=False   # І є дата реєстрації
                ).exists():
                    key_document_fulfilled = True
                    print(f"[WRI_STATUS_CHECKER] Key document (Attestation Act REGISTERED) FOUND for WRI ID: {self.id}")
            else:
                print(f"[WRI_STATUS_CHECKER] No DocumentType configured for Attestation Act for OID Type '{wri_oid_type}'.")
        
        if key_document_fulfilled:
            if self.status != WorkRequestStatusChoices.COMPLETED:
                self.status = WorkRequestStatusChoices.COMPLETED
                self.docs_actually_processed_on = timezone.now().date() # Встановлюємо дату фактичного опрацювання
                self.save(update_fields=['status', 'docs_actually_processed_on', 'updated_at'])
                print(f"[WRI_STATUS_CHECKER] WRI ID {self.id} (OID: {self.oid.cipher}) status updated to COMPLETED, processed_on: {self.docs_actually_processed_on}.")
        else:
            print(f"[WRI_STATUS_CHECKER] WRI ID {self.id}: Key document condition NOT fulfilled. Status remains {self.status}.")
    def __str__(self):
        return f"в/ч {self.unit.code} Заявка вх.№ {self.incoming_number} від {self.incoming_date} ({self.get_status_display()})"

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
    doc_processing_deadline = models.DateField(
        verbose_name="Термін опрацювання документів до",
        null=True,
        blank=True
    )
    docs_actually_processed_on = models.DateField(
        verbose_name="Документи фактично опрацьовано (дата)",
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата внесення Item заявки")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата останнього оновлення")
    deadline_trigger_trip = models.ForeignKey(
        'Trip', 
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name="Відрядження, що встановило дедлайн опрацювання",
        related_name="triggered_work_items" 
    )
    docs_actually_processed_on = models.DateField(
        verbose_name="Документи фактично опрацьовано (дата)", # <--- ОСЬ ЦЕ ПОЛЕ
        null=True,
        blank=True
    )
    history = HistoricalRecords()
    class Meta:
        unique_together = ('request', 'oid', 'work_type') # Один ОІД не може мати двічі одну і ту ж роботу в одній заявці
        verbose_name = "Елемент заявки"
        verbose_name_plural = "Елементи заявки"
        # ordering = ['request', 'oid'] # Додано сортування
        ordering = ['request', 'request__incoming_date' ] # Додав сортування за замовчуванням

    def __str__(self):
        # return f"{self.oid.cipher} - {self.get_work_type_display()} ({self.get_status_display()})"
        return f"ОІД: {self.oid.cipher} ({self.oid.oid_type}) - Робота: {self.get_work_type_display()} (Статус: {self.status})"
    # Твоя логіка оновлення статусу заявки:
    def check_and_update_status_based_on_documents(self):
        """
        Перевіряє, чи виконані умови для завершення цього WorkRequestItem,
        ґрунтуючись на наявних та "виконаних" документах.
        Викликається після збереження пов'язаного документа.
        """
        print(f"[WRI_STATUS_CHECKER] Checking completion for WRI ID {self.id} (OID: {self.oid.cipher})")

        if self.status in [WorkRequestStatusChoices.COMPLETED, WorkRequestStatusChoices.CANCELED]:
            print(f"[WRI_STATUS_CHECKER] WRI ID {self.id} is already COMPLETED or CANCELED. No update needed.")
            return # Немає потреби в оновленні

        key_document_fulfilled = False
        wri_oid_type = self.oid.oid_type
        
		
		# 1. Визначаємо, які типи документів є обов'язковими (is_required=True)
        #    для типу ОІД та типу робіт цього WorkRequestItem.
        required_doc_types = DocumentType.objects.filter(
            Q(oid_type=self.oid.oid_type) | Q(oid_type='СПІЛЬНИЙ'),
            Q(work_type=self.work_type) | Q(work_type='СПІЛЬНИЙ'),
            is_required=True
        )
        if not required_doc_types.exists():
            print(f"[WRI_STATUS_CHECKER] No required document types found for OID type '{self.oid.oid_type}' and Work type '{self.work_type}'. Cannot determine completion.")
            # Можливо, в цьому випадку елемент можна вважати виконаним, якщо для нього немає обов'язкових документів.
            # Це залежить від вашої бізнес-логіки. Припустимо, що якщо немає is_required, то нічого не робимо.
            return
        
		# 2. Отримуємо всі документи, вже створені для цього WorkRequestItem.
        existing_docs_for_item = Document.objects.filter(work_request_item=self)
        existing_doc_type_ids = set(existing_docs_for_item.values_list('document_type_id', flat=True))
        
        print(f"[WRI_STATUS_CHECKER] Required DocType IDs: {[dt.id for dt in required_doc_types]}")
        print(f"[WRI_STATUS_CHECKER] Existing DocType IDs for this WRI: {existing_doc_type_ids}")
        
		 # 3. Перевіряємо, чи всі обов'язкові типи документів присутні серед існуючих.
        all_required_docs_are_present = True
        for req_doc_type in required_doc_types:
            if req_doc_type.id not in existing_doc_type_ids:
                all_required_docs_are_present = False
                print(f"[WRI_STATUS_CHECKER] MISSING required document: '{req_doc_type.name}' (ID: {req_doc_type.id})")
                break # Знайшли перший відсутній, можна виходити з циклу
        
        # Додаткова перевірка для Атестації: Акт має бути зареєстрований
        if all_required_docs_are_present and self.work_type == WorkTypeChoices.ATTESTATION:
            # Знайдемо тип "Акт атестації" серед обов'язкових
            # Знову ж, краще мати надійний ідентифікатор, але поки що використовуємо ваш підхід
            attestation_act_doc_type = required_doc_types.filter(duration_months=60).first()
            if attestation_act_doc_type:
                # Перевіряємо, чи існуючий документ цього типу має реєстраційні дані
                is_att_act_registered = existing_docs_for_item.filter(
                    document_type=attestation_act_doc_type,
                    dsszzi_registered_number__isnull=False,
                    dsszzi_registered_number__ne=''
                ).exists()
                if not is_att_act_registered:
                    all_required_docs_are_present = False # Вважаємо, що умова не виконана, бо акт не зареєстрований
                    print(f"[WRI_STATUS_CHECKER] Attestation Act for WRI ID {self.id} exists but is NOT YET REGISTERED.")

        # 4. Якщо всі умови виконані, оновлюємо статус
        if all_required_docs_are_present:
            print(f"[WRI_STATUS_CHECKER] All conditions met for WRI ID {self.id}. Updating status to COMPLETED.")
            self.status = WorkRequestStatusChoices.COMPLETED
            # Дату docs_actually_processed_on ми вже встановили у Document.save()
            # Переконаємось, що вона точно встановлена.
            if not self.docs_actually_processed_on:
                self.docs_actually_processed_on = timezone.now().date()
            
            self.save(update_fields=['status', 'docs_actually_processed_on', 'updated_at']) # Це викличе update_request_status() для WorkRequest
        else:
            print(f"[WRI_STATUS_CHECKER] Conditions NOT met for WRI ID {self.id}. Status remains {self.status}.")









        # if self.work_type == WorkTypeChoices.IK:
        #     target_duration = 20 # Умова для ІК: наявність документа з duration_months=20 для цього work_request_item
        #     # (припускаємо, що це "Висновок ІК")
        #     try:
        #         # Шукаємо тип документа "Висновок ІК" (або аналог з duration_months=20)
        #         # Важливо, щоб цей DocumentType був налаштований для work_type='ІК' або 'СПІЛЬНИЙ'
        #         # та мав oid_type, що відповідає self.oid.oid_type або 'СПІЛЬНИЙ'
        #         key_doc_type_qs = DocumentType.objects.filter(
        #             (Q(work_type=WorkTypeChoices.IK) | Q(work_type='СПІЛЬНИЙ')),
        #             (Q(oid_type=wri_oid_type) | Q(oid_type='СПІЛЬНИЙ')),
        #             duration_months=target_duration
        #         )
        #         if key_doc_type_qs.exists():
        #             for dt_candidate in key_doc_type_qs:
        #                 print(f"[DEBUG] Checking IK with DocumentType candidate: '{dt_candidate.name}' (ID: {dt_candidate.id})")
        #                 if Document.objects.filter(
        #                     work_request_item=self,
        #                     oid=self.oid,
        #                     document_type=dt_candidate
        #                 ).exists():
        #                     key_document_fulfilled = True
        #                     print(f"[DEBUG] >>> Key document for IK FOUND (DocType ID: {dt_candidate.id}) for WRI ID: {self.id}")
        #                     break # Знайшли, виходимо
        #             if not key_document_fulfilled:
        #                  print(f"[DEBUG] No Document found linked to WRI {self.id} for any suitable IK DocumentTypes.")
        #         else:
        #             print(f"[DEBUG] No DocumentType configured for IK (duration={target_duration}, OID Type='{wri_oid_type}' or СПІЛЬНИЙ, Work Type='IK' or СПІЛЬНИЙ).")
        #     except Exception as e:
        #         print(f"[DEBUG] ERROR during IK DocumentType/Document search: {e}")


        # elif self.work_type == WorkTypeChoices.ATTESTATION:
        #     target_duration = 60
        #     # Умова для Атестації: наявність документа з duration_months=60 (Акт атестації),
        #     # який зареєстрований в ДССЗЗІ.
        #     try:
        #         # Шукаємо тип документа "Акт атестації" (або аналог з duration_months=60)
        #         key_doc_type_qs = DocumentType.objects.filter(
        #             (Q(work_type=WorkTypeChoices.ATTESTATION) | Q(work_type='СПІЛЬНИЙ')),
        #             (Q(oid_type=wri_oid_type) | Q(oid_type='СПІЛЬНИЙ')),
        #             duration_months=target_duration
        #         )
        #         print(f"[DEBUG] Found {key_doc_type_qs.count()} potential DocumentType(s) for ATTESTATION.")
        #         if key_doc_type_qs.exists():
        #             for dt_candidate in key_doc_type_qs:
        #                 print(f"[DEBUG] Checking ATTESTATION with DocumentType candidate: '{dt_candidate.name}' (ID: {dt_candidate.id})")
        #                 # Знаходимо всі документи цього типу, пов'язані з WRI
        #                 linked_documents = Document.objects.filter(
        #                     work_request_item=self,
        #                     oid=self.oid,
        #                     document_type=dt_candidate
        #                 )
        #                 if not linked_documents.exists():
        #                     print(f"[DEBUG] No Document of type '{dt_candidate.name}' found for WRI ID {self.id}.")
        #                     continue # Переходимо до наступного кандидата DocumentType

        #                 for doc_instance in linked_documents:
        #                     print(f"[DEBUG] Checking Document ID {doc_instance.id}: DSSZZI Num='{doc_instance.dsszzi_registered_number}', Date={doc_instance.dsszzi_registered_date}")
        #                     if doc_instance.dsszzi_registered_number and \
        #                        doc_instance.dsszzi_registered_number.strip() != '' and \
        #                        doc_instance.dsszzi_registered_date:
        #                         key_document_fulfilled = True
        #                         print(f"[DEBUG] >>> Key document for ATTESTATION FOUND AND REGISTERED (DocType ID: {dt_candidate.id}, Doc ID: {doc_instance.id}) for WRI ID: {self.id}")
        #                         break # Знайшли зареєстрований, виходимо з циклу документів
        #                 if key_document_fulfilled:
        #                     break # Виходимо з циклу DocumentType кандидатів
        #             if not key_document_fulfilled:
        #                  print(f"[DEBUG] No REGISTERED Document found linked to WRI {self.id} for any suitable ATTESTATION DocumentTypes.")
        #         else:
        #             print(f"[DEBUG] No DocumentType configured for ATTESTATION (duration={target_duration}, OID Type='{wri_oid_type}' or СПІЛЬНИЙ, Work Type='ATTESTATION' or СПІЛЬНИЙ).")
        #     except Exception as e:
        #         print(f"[DEBUG] ERROR during ATTESTATION DocumentType/Document search: {e}")

        if key_document_fulfilled:
            if self.status != WorkRequestStatusChoices.COMPLETED:
                self.status = WorkRequestStatusChoices.COMPLETED
                # Зберігаємо тільки якщо статус дійсно змінився, щоб уникнути рекурсії
                # і викликати update_request_status (який вже є в save)
                self.save(update_fields=['status', 'updated_at'])
                print(f"DEBUG: WorkRequestItem ID {self.id} (OID: {self.oid.cipher}) статус оновлено на COMPLETED.")
        # Якщо ключовий документ не виконано, статус WorkRequestItem не змінюється цим методом.
        # Логіка повернення статусу (наприклад, якщо документ видалено) тут не розглядається.

   
    def save(self, *args, **kwargs):
        """
        Викликає оновлення статусу батьківської заявки після збереження елемента.
        """
        # current_status = self.status # Можна зберегти для порівняння, якщо потрібно
        super().save(*args, **kwargs)
              
        # if hasattr(self, 'request') and self.request is not None:
           
        # Викликаємо update_request_status тільки якщо це не створення,
        # або якщо статус змінився (щоб уникнути зайвих викликів при масовому створенні).
        # Однак, простіше викликати завжди, а update_request_status зробить перевірку.
        self.update_request_status()
    def update_request_status(self):
        """
        Оновлює статус батьківської заявки WorkRequest на основі статусів
        всіх її елементів WorkRequestItem.
        """
        work_request = self.request
        all_items = work_request.items.all()

        if not all_items.exists():
            # Якщо заявка не має елементів (наприклад, щойно створена і ще не додані, або всі видалені)
            # Можна встановити PENDING або залишити як є, залежно від бізнес-логіки.
            # Якщо це відбувається після видалення останнього елемента, можливо, заявку треба скасувати або повернути в PENDING.
            if work_request.status != WorkRequestStatusChoices.PENDING: # Якщо вже не PENDING
                work_request.status = WorkRequestStatusChoices.PENDING # або інший логічний статус
                work_request.save(update_fields=['status', 'updated_at'])
            return

        # Перевіряємо, чи всі елементи завершені або скасовані
        is_all_items_processed = all(
            item.status in [WorkRequestStatusChoices.COMPLETED, WorkRequestStatusChoices.CANCELED]
            for item in all_items
        )

        original_request_status = work_request.status
        new_request_status = original_request_status # За замовчуванням не змінюємо


        if is_all_items_processed:
            # Якщо всі елементи оброблені, визначаємо фінальний статус заявки
            if all_items.filter(status=WorkRequestStatusChoices.COMPLETED).exists():
                # Якщо є хоча б один виконаний елемент, заявка вважається виконаною
                new_request_status = WorkRequestStatusChoices.COMPLETED
            elif all_items.filter(status=WorkRequestStatusChoices.CANCELED).count() == all_items.count():
                # Якщо всі елементи скасовані (і немає виконаних)
                new_request_status = WorkRequestStatusChoices.CANCELED
            else:
                # Ситуація, коли всі CANCELED, але був хоча б один COMPLETED, вже покрита першою умовою.
                # Якщо всі CANCELED і не було COMPLETED - це друга умова.
                # Якщо є суміш COMPLETED і CANCELED, то COMPLETED має пріоритет.
                # Якщо логіка інша (напр. "Частково виконано"), її треба додати.
                 new_request_status = WorkRequestStatusChoices.COMPLETED # За замовчуванням для змішаних processed
        else:
            # Якщо не всі елементи оброблені, перевіряємо наявність "В роботі" або "Очікує"
            if all_items.filter(status=WorkRequestStatusChoices.IN_PROGRESS).exists():
                new_request_status = WorkRequestStatusChoices.IN_PROGRESS
            elif all_items.filter(status=WorkRequestStatusChoices.PENDING).exists():
                new_request_status = WorkRequestStatusChoices.PENDING
            # Можливий випадок: немає IN_PROGRESS, немає PENDING, але не всі processed.
            # Це може статися, якщо є власні статуси. Для стандартних це малоймовірно.
            # У такому разі, можна залишити поточний статус заявки або встановити PENDING.
        if original_request_status != new_request_status:
            work_request.status = new_request_status
            work_request.save(update_fields=['status', 'updated_at'])
            print(f"[DEBUG] WorkRequest ID {work_request.id} status successfully saved as '{work_request.get_status_display()}'.")
        else:
            print(f"[DEBUG] WorkRequest ID {work_request.id} status '{work_request.get_status_display()}' remains unchanged.")
        print(f"--- [DEBUG] WRI.update_request_status() FINISHED for WRI ID: {self.id} ---")
#

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
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата внесення інф. про реєстрацію Атестації")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата останнього оновлення")
    history = HistoricalRecords()

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
    history = HistoricalRecords()

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
        'Person', # Використовуємо рядок
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        verbose_name="Автор документа",
        related_name='authored_documents'
    )
    attachment = models.FileField(upload_to="attestation_docs/", blank=True, null=True, verbose_name="Прикріплений файл (Опційно)")
    note = models.TextField(blank=True, null=True, verbose_name="Примітки")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата внесення документу")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата останнього оновлення")
    expiration_date = models.DateField(verbose_name="Дата завершення дії", blank=True, null=True)
    history = HistoricalRecords()

    # --- НОВІ ПОЛЯ для реєстрації в ДССЗЗІ (для актів атестації) ---
    # Посилання на запис про відправку (вихідний лист)
    attestation_registration_sent = models.ForeignKey(
        'AttestationRegistration', # Використовуємо рядок
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
         # Логіка обчислення expiration_date
        if self.document_type and self.document_type.has_expiration and self.document_type.duration_months > 0 and self.work_date:
            from dateutil.relativedelta import relativedelta 
            self.expiration_date = self.work_date + relativedelta(months=self.document_type.duration_months)
        else:
            # Якщо у документа немає терміну дії або не вказана дата робіт, дата завершення дії не встановлюється
             if not (self.document_type and self.document_type.has_expiration and self.document_type.duration_months > 0):
                self.expiration_date = None # Очищаємо, якщо умови не виконані
        super().save(*args, **kwargs)
        if self.work_request_item:
            wri = self.work_request_item
            
            # Переконуємося, що work_request_item ще не COMPLETED або CANCELED,
            # і що тип роботи work_request_item відповідає типу роботи документа (або документ "СПІЛЬНИЙ")
            if self.work_request_item.status not in [WorkRequestStatusChoices.COMPLETED, WorkRequestStatusChoices.CANCELED] and \
               (self.work_request_item.work_type == self.document_type.work_type or self.document_type.work_type == 'СПІЛЬНИЙ'):
                self.work_request_item.check_and_update_status_based_on_documents()
            if wri.docs_actually_processed_on is None or self.process_date > wri.docs_actually_processed_on:
                wri.docs_actually_processed_on = self.process_date
                wri.save(update_fields=['docs_actually_processed_on', 'updated_at'])
                print(f"DOCUMENT_SAVE: Set docs_actually_processed_on for WRI ID {wri.id} to {self.process_date}")
            # Тепер викликаємо перевірку, чи можна завершити WorkRequestItem
            # Ця функція має бути методом моделі WorkRequestItem
            wri.check_and_update_status_based_on_documents()

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
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата створення відрядження")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата останнього оновлення")
    history = HistoricalRecords()

    def __str__(self):
        unit_codes = ", ".join(unit.code for unit in self.units.all()[:3]) # Обмежимо кількість для читабельності
        if self.units.count() > 3:
            unit_codes += "..."
        return f"Відрядження {self.start_date.strftime('%d.%m.%Y')}—{self.end_date.strftime('%d.%m.%Y')} до ВЧ: {unit_codes or 'не вказано'}"

    def save(self, *args, **kwargs):
        # Тут може бути інша логіка, специфічна для збереження Trip,
        # але розрахунок дедлайнів для WorkRequestItem тепер обробляється сигналом.
        print(f"TRIP_MODEL_SAVE: Saving Trip ID {self.pk} with end_date: {self.end_date}")
        super().save(*args, **kwargs)
        # НЕМАЄ логіки розрахунку дедлайнів тут
    
    class Meta:
        verbose_name = "Відрядження"
        verbose_name_plural = "Відрядження"
        ordering = ['-start_date', '-id']

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
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата створення запису про зміну статусу")
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
    note = models.TextField(blank=True, null=True, verbose_name="Примітка")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата внесення запису про опрацювання відрядження")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата останнього оновлення")
    history = HistoricalRecords()
    # related_request - можна отримати через trip.work_requests.all() або через documents.work_request_item.request
    # Тому, якщо це не критично для прямого доступу, можна прибрати для уникнення дублювання.
    # related_request = models.ForeignKey('WorkRequest', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Пов’язана заявка")
    
    def __str__(self):
        return f"Відправка результатів від {self.outgoing_letter_date}"
    
    class Meta:
        verbose_name = "Результати відрядження для частини"
        verbose_name_plural = "Результати відрядження для частин"
        ordering = ['-outgoing_letter_date', '-id']
        
# oids/models.py
class TechnicalTask(models.Model):
    # ... (поля як у вас)
    oid = models.ForeignKey(OID, on_delete=models.CASCADE, verbose_name="ОІД", related_name='technical_tasks')
    input_number = models.CharField(max_length=50, verbose_name="Вхідний номер")
    input_date = models.DateField(verbose_name="Вхідна дата")
    read_till_date = models.DateField(verbose_name="Опрацювати до")
    reviewed_by = models.ForeignKey(
        Person, 
        on_delete=models.SET_NULL, 
        null=True, blank=True, 
        verbose_name="Хто ознайомився/опрацював", # Оновлено для ясності
        related_name='processed_technical_tasks' # <--- ЗМІНЕНО ТУТ
    )
    review_result = models.CharField(
        max_length=30, 
        choices=DocumentReviewResultChoices.choices, 
        # default=DocumentReviewResultChoices.APPROVED, # Можна прибрати default, якщо встановлюється у view
        verbose_name="Результат розгляду / Статус ТЗ" # Змінено verbose_name
    )
    note = models.TextField(blank=True, null=True, verbose_name="Примітка")
    updated_at = models.DateTimeField(null=True, blank=True, verbose_name="Дата опрацювання")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата внесення ТЗ\МЗ")
    history = HistoricalRecords()

    def __str__(self):
        return f"ТЗ\МЗ для ОІД: {self.oid.cipher} (статус: {self.get_review_result_display()}) від {self.input_date.strftime("%d.%m.%Y")} вх.№{self.input_number}"

    class Meta:
        verbose_name = "Технічне Завдання" # Змінено
        verbose_name_plural = "Технічні Завдання" # Змінено
        ordering = ['-input_date', '-read_till_date', '-created_at'] # Додав created_at
# 