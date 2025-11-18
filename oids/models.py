from django.db import models
from multiselectfield import MultiSelectField
from django.utils import timezone
import datetime
from django.db.models import Q
from simple_history.models import HistoricalRecords
from dateutil.relativedelta import relativedelta
	
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
    OTHER = 'уточнити', 'уточнити'
    DSK = 'ДСК', 'ДСК'
 
class OIDStatusChoices(models.TextChoices):
    NEW = 'створюється', 'Створюється'
    RECEIVED_TZ = 'отримано ТЗ/МЗ', 'Отримано ТЗ/МЗ'
    RECEIVED_TZ_REPEAT = 'очікуємо ТЗ/МЗ(повторно)', 'Очікуємо ТЗ/МЗ(повторно)'
    RECEIVED_TZ_APPROVE = 'ТЗ/МЗ погоджено', 'ТЗ/МЗ Погоджено' 
    RECEIVED_REQUEST = 'отримано заявку', 'Отримано Заявку уточнити'
    RECEIVED_REQUEST_IK = 'отримано заявку ІК', 'Отримано Заявку ІК' 
    RECEIVED_REQUEST_ATTESTATION = 'отримано заявку Первинна Атестація', 'Отримано Заявку Первинна Атестація' 
    RECEIVED_REQUEST_PLAND_ATTESTATION = 'отримано заявку Чергова Атестація', 'Отримано Заявку Чергова Атестація' 
    ATTESTED = 'атестовано', 'атестовано'
    AZR_SEND = 'АЗР відправлено до ДССЗЗІ', 'АЗР відправлено до ДССЗЗІ' 
    RECEIVED_DECLARATION = 'отримано Декларацію', 'Отримано Декларацію' 
    ACTIVE = 'активний', 'Активний (В дії)'
    TERMINATED = 'призупинено', 'Призупинено'
    CANCELED = 'скасований', 'Скасований'

# перевіряй/оновлюй 
# statuses_to_check_for_attestation
# statuses_for_first_attestation

# OID_to_show_main_dashboard_creating
# OID_to_show_main_dashboard_active
# OID_to_show_main_dashboard_cancel

class WorkRequestStatusChoices(models.TextChoices): 
    PENDING = 'очікує', 'Очікує' # очікує – тільки введена"
    IN_PROGRESS = 'в роботі', 'В роботі' # в роботі – заплановано відрядження"
    TO_SEND = 'відправити в ДССЗЗІ', 'відправити в ДССЗЗІ' # в роботі – заплановано відрядження"
    ON_REGISTRATION = 'на реєстрації в ДССЗЗІ', 'на реєстрації в ДССЗЗІ' # в роботі – заплановано відрядження"
    COMPLETED = 'виконано', 'Виконано' # виконано – внесена інформацію по опрацьованих документах"
    CANCELED = 'скасовано', 'Скасовано' # скасовано – заявка втратила чинність"

class OIDTypeChoices(models.TextChoices):
    PEMIN = 'ПЕМІН', 'ПЕМІН'
    SPEAK = 'МОВНА', 'МОВНА'

class WorkTypeChoices(models.TextChoices):
    ATTESTATION = 'Атестація', 'Атестація'
    PLAND_ATTESTATION = 'Чергова Атестація', 'Чергова Атестація' 
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
    SPEAKSUBTYPE = 'МОВНА', 'МОВНА'   
    VARM = 'ВАРМ', 'ВАРМ'
    ZARM = 'ЗАРМ', 'ЗАРМ'
    AS1_23PORTABLE ='АС1-2/3 портативний', 'АС1-2/3 Портативний'
    AS1_23STAC ='АС1-2/3 Стаціонар', 'АС1-2/3 Стаціонар'
    AS1_4_DSK ='АС1-4 ДСК', 'АС1-4 ДСК'
    AS23_4_DSK ='АС2/3-4 ДСК', 'АС2/3-4 МОСІ Соц і т.п.'

class DocumentProcessingStatusChoices(models.TextChoices):
    DRAFT = 'чернетка', 'Чернетка'
    SENT_FOR_REGISTRATION = 'надіслано на реєстрацію', 'Надіслано на реєстрацію'
    REGISTERED = 'зареєстровано', 'Зареєстровано'
    SENT_TO_UNIT = 'надіслано до в/ч', 'Надіслано до в/ч'
    COMPLETED = 'завершено', 'Завершено'

class ProcessStepStatusChoices(models.TextChoices):
    PENDING = 'очікує', 'Очікує'
    COMPLETED = 'виконано', 'Виконано'
    SKIPPED = 'пропущено', 'Пропущено'
    
class PersonGroup(models.TextChoices):
    ZAG = 'Загальна', 'Загальна'
    GOV = 'Управління', 'Управління'
    ZBSI = 'ЗБСІ', 'ЗБСІ'
    IARM = 'ІАРМ', 'ІАРМ'
    SDKTK = 'СД КТК', 'СД КТК'
    REPAIR = 'Майстерня', 'Майстерня'
    PDTR = 'ПДТР', 'ПДТР'
    SL = 'СлужбаТЗІ', 'Служба ТЗІ'
    # OAB = 'ОАБ', 'ОАБ'

# --- Models ---

class TerritorialManagement(models.Model):
    code = models.CharField(max_length=50, unique=True, verbose_name="Код управління")
    name = models.CharField(max_length=255, verbose_name="Назва управління")
    note = models.TextField(verbose_name="Примітка", blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Структура: Територіальне управління"
        verbose_name_plural = "Структура: Територіальні управління"

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
        verbose_name = "Структура: Група військових частин (для відряджень)"
        verbose_name_plural = "Структура: Групи військових частин (для відряджень)"

class Unit(models.Model): 
    """
    Військова частина
    Атрибути: Номер частини, Назва, Місто розташування, Відстань з ГУ до міста розташування,
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
    is_active = models.BooleanField(default=True, verbose_name="Активний")
    history = HistoricalRecords()
    def __str__(self):
        return f"{self.code} - {self.name or self.city}" # Виводимо код і назву/місто

    class Meta:
        verbose_name = "Структура: Військова частина"
        verbose_name_plural = "Структура: Військові частини"

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
    status = models.CharField(max_length=35, choices=OIDStatusChoices.choices, default=OIDStatusChoices.NEW, verbose_name="Поточний стан ОІД")
    note = models.TextField(verbose_name="Примітка", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата створення ОІД")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата останнього оновлення")
    pemin_sub_type = models.CharField(
        max_length=25, 
        choices=PeminSubTypeChoices.choices, 
        verbose_name="Тип ЕОТ",
        blank=True, # Дозволяє бути порожнім у формах
        null=True   # Дозволяє бути NULL в базі даних (для МОВНА ОІД)
    )
    serial_number = models.CharField(
        max_length=20, 
        verbose_name="s/n", 
        blank=True, 
        null=True
    )
    inventory_number = models.CharField(
        max_length=20, 
        verbose_name="Інв. №", 
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
        unique_together = ('unit', 'cipher')

class Person(models.Model):
    """
    Виконавець
    Атрибути: ПІБ, Посада, Активність, Група, Історія участі у відрядженнях / роботах / документах
    Зв'язки: Може бути учасником відрядження, Може бути виконавцем роботи, Може бути автором документа
    """
    """
    Модель виконавця/користувача
    Зберігає інформацію про працівників організації
    """
    full_name = models.CharField("Прізвище, ім'я",max_length=255,help_text="Введіть прізвище та ім'я працівника")
    surname = models.CharField("Прізвище",max_length=100,blank=True,help_text="Прізвище окремо (опціонально)")
    position = models.CharField("Посада",max_length=255,help_text="Посада працівника")
    group = models.CharField("Підрозділ",max_length=20,choices=PersonGroup.choices,default=PersonGroup.GOV,help_text="Підрозділ, до якого належить працівник")
    is_active = models.BooleanField("Активний",default=True,help_text="Чи активний працівник")
    created_at = models.DateTimeField("Дата створення",auto_now_add=True)
    updated_at = models.DateTimeField("Дата оновлення", auto_now=True)

    class Meta:
        verbose_name = "Виконавець"
        verbose_name_plural = "Довідково: Виконавці"
        ordering = ['full_name']
        indexes = [
            models.Index(fields=['group', 'is_active']),
            models.Index(fields=['full_name']),
        ]

    def __str__(self):
        return f"{self.full_name} ({self.get_group_display()})"

    def get_active_tasks_count(self):
        """Кількість активних завдань виконавця"""
        return self.assigned_tasks.filter(is_completed=False).count()


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
    
    @property
    def get_items_for_export(self):
        """
        Повертає відформатований рядок з інформацією про всі елементи заявки
        для експорту в Excel.
        """
        # Важливо: цей метод буде ефективним, оскільки у work_request_list_view
        # ми вже використовуємо prefetch_related('items'), що завантажує всі
        # пов'язані елементи одним запитом.
        if not self.items.all().exists():
            return "Немає ОІД"
        
        item_strings = []
        for item in self.items.all():
            item_strings.append(
                f"{item.oid.cipher} {item.get_work_type_display()} ({item.get_status_display()})"
            )
        
        # Повертаємо всі записи, розділені символом нового рядка
        return "\n".join(item_strings)
    
    def __str__(self):
        # Безпечно отримуємо дані, щоб уникнути помилок, якщо щось None
        unit_code = self.unit.code if self.unit else 'N/A'
        date_str = self.incoming_date.strftime('%d.%m.%Y') if self.incoming_date else 'N/A'
        number_str = self.incoming_number or 'б/н' # 'б/н' - без номера
        status_str = self.get_status_display() or 'N/A'
        
        # Форматуємо рядок у бажаному вигляді
        return f"Заявка №{number_str} від {date_str} (ВЧ: {unit_code}, Статус: {status_str})"
						# раніше форматував вигляд тут
						# def ajax_load_work_requests_for_oids(request): 
    					# 'text': f"заявка вх.№ {wr.incoming_number} від {wr.incoming_date.strftime('%d.%m.%Y')} (ВЧ: {wr.unit.code}) - {wr.get_status_display()}"
    class Meta:
        verbose_name = "Заявки: Заявка на проведення робіт"
        verbose_name_plural = "Заявки: Заявки на проведення робіт"
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
    history = HistoricalRecords()

	#  логіка оновлення статусу заявки:
    def check_and_update_status_based_on_documents(self):
        """
        Перевіряє, чи виконані умови для завершення цього WorkRequestItem,
        ґрунтуючись на наявності КЛЮЧОВОГО документа.
        """
        print(f"[WRI_STATUS_CHECKER] Checking completion for WRI ID {self.id} (OID: {self.oid.cipher})")

        if self.status in [WorkRequestStatusChoices.COMPLETED, WorkRequestStatusChoices.CANCELED]:
            print(f"[WRI_STATUS_CHECKER] WRI ID {self.id} is already COMPLETED or CANCELED. No update needed.")
            return

        key_document_fulfilled = False
        
        # Отримуємо всі документи, вже створені для цього WorkRequestItem.
        existing_docs_for_item = Document.objects.filter(work_request_item=self)

        # --- Логіка для Атестації ---
        # if self.work_type == WorkTypeChoices.ATTESTATION:
        if self.work_type in [WorkTypeChoices.PLAND_ATTESTATION, WorkTypeChoices.ATTESTATION]:
            # Шукаємо тип документа "Акт атестації"
            attestation_act_type = DocumentType.objects.filter(name__icontains="Акт атестації").first()
             # document_type_act_att = DocumentType.objects.filter(duration_months=60).first() # Ваш спосіб ідентифікації "Акту атестації"
                    # attestation_act_type = DocumentType.objects.get(name__icontains="Акт атестації")
            if attestation_act_type:
                # Перевіряємо, чи існує для цього WRI зареєстрований Акт Атестації
                  if existing_docs_for_item.filter(
                    document_type=attestation_act_type,
                    dsszzi_registered_number__isnull=False
                ).exclude(
                    dsszzi_registered_number='' 
                ).exists():
                    key_document_fulfilled = True
                    print(f"[WRI_STATUS_CHECKER] Key document (Attestation Act REGISTERED) FOUND for WRI ID: {self.id}")

        # --- Логіка для ІК ---
        elif self.work_type == WorkTypeChoices.IK:
            # Шукаємо тип документа "Висновок ІК"
            ik_conclusion_type = DocumentType.objects.filter(duration_months=20).first()
            if ik_conclusion_type:
                # Перевіряємо, чи існує для цього WRI Висновок ІК
                if existing_docs_for_item.filter(document_type=ik_conclusion_type).exists():
                    key_document_fulfilled = True
                    print(f"[WRI_STATUS_CHECKER] Key document (IK Conclusion) FOUND for WRI ID: {self.id}")

        # --- Оновлюємо статус, якщо ключовий документ знайдено ---
        if key_document_fulfilled:
            if self.status != WorkRequestStatusChoices.COMPLETED:
                self.status = WorkRequestStatusChoices.COMPLETED
                if not self.docs_actually_processed_on:
                    self.docs_actually_processed_on = timezone.now().date()
                
                self.save(update_fields=['status', 'docs_actually_processed_on', 'updated_at'])
                print(f"[WRI_STATUS_CHECKER] Key document condition met for WRI ID {self.id}. Updating status to COMPLETED.")
        else:
            print(f"[WRI_STATUS_CHECKER] Key document condition NOT met for WRI ID {self.id}. Status remains {self.status}.")

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
        is_new = self._state.adding

        # Спочатку зберігаємо сам елемент заявки
        super().save(*args, **kwargs)

        # Якщо це новий елемент заявки...
        if is_new and self.oid:
            oid_to_update = self.oid
            old_status = oid_to_update.get_status_display()
            
            # --- ПОЧАТОК ЗМІН ---
            # Визначаємо новий статус ОІД на основі типу робіт у заявці
            new_status_enum = None
            if self.work_type == WorkTypeChoices.IK:
                new_status_enum = OIDStatusChoices.RECEIVED_REQUEST_IK
            elif self.work_type == WorkTypeChoices.ATTESTATION:
                new_status_enum = OIDStatusChoices.RECEIVED_REQUEST_ATTESTATION
            elif self.work_type == WorkTypeChoices.PLAND_ATTESTATION:
                new_status_enum = OIDStatusChoices.RECEIVED_REQUEST_PLAND_ATTESTATION
            else:
                # Залишаємо загальний статус, якщо тип робіт не визначено
                # або для нього немає спеціального статусу "отримано заявку"
                new_status_enum = OIDStatusChoices.RECEIVED_REQUEST 
            
            # --- КІНЕЦЬ ЗМІН ---

            if oid_to_update.status != new_status_enum:
                oid_to_update.status = new_status_enum
                oid_to_update.save(update_fields=['status'])

                # Створюємо запис в історії
                OIDStatusChange.objects.create(
                    oid=oid_to_update,
                    old_status=old_status,
                    new_status=new_status_enum.label,
                    # Додамо тип робіт до причини для ясності
                    reason=f"ОІД додано до заявки №{self.request.incoming_number} (Тип робіт: {self.get_work_type_display()})"
                )
       
        # Викликаємо існуючу логіку для оновлення статусу батьківської заявки
        self.update_parent_request_status()
    
    # ... (решта методів моделі WorkRequestItem, наприклад update_parent_request_status) ...

    def update_parent_request_status(self):
        """
        Перевіряє статуси всіх елементів батьківської заявки і, якщо всі
        завершені, оновлює статус самої заявки.
        """
        parent_request = self.request
        
        # Отримуємо всі "братні" елементи, що належать тій самій заявці
        all_items = parent_request.items.all()
        
        # Якщо елементів у заявці немає, нічого не робимо
        if not all_items.exists():
            return

        # Перевіряємо, чи ВСІ елементи мають статус "Виконано" або "Скасовано"
        all_completed = all(
            item.status in [WorkRequestStatusChoices.COMPLETED, WorkRequestStatusChoices.CANCELED]
            for item in all_items
        )

        # Якщо всі елементи завершені і статус самої заявки ще не "Виконано"
        if all_completed and parent_request.status != WorkRequestStatusChoices.COMPLETED:
            parent_request.status = WorkRequestStatusChoices.COMPLETED
            parent_request.save(update_fields=['status'])
            
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

    def __str__(self):
        # return f"{self.oid.cipher} - {self.get_work_type_display()} ({self.get_status_display()})"
        return f"ОІД: {self.oid.cipher} ({self.oid.oid_type}) - Робота: {self.get_work_type_display()} (Статус: {self.status})"
    
    class Meta:
        unique_together = ('request', 'oid', 'work_type') # Один ОІД не може мати двічі одну і ту ж роботу в одній заявці
        verbose_name = "Заявки: Елемент заявки (ОІД)"
        verbose_name_plural = "Заявки: Елементи заявки (ОІД)"
        # ordering = ['request', 'oid'] # Додано сортування
        ordering = ['request', 'request__incoming_date' ] # Додав сортування за замовчуванням


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
    # is_required = models.BooleanField("Обов'язковість", default=True) # раніше логіка будувалась на обов`язковості документів, зараз перебудував на duration
    history = HistoricalRecords()
    def __str__(self):
    #     return f"{self.name} ({self.oid_type}, {self.work_type})"
        return f"{self.name} ({self.get_oid_type_display()}, {self.get_work_type_display()})"
    
    class Meta:
        unique_together = ('oid_type', 'work_type', 'name') # Документ унікальний для комбінації тип ОІД/робота/назва
        verbose_name = "Довідково: Тип документа"
        verbose_name_plural = "Довідково: Типи документів"
        ordering = ['oid_type', 'work_type', 'name'] # Додано сортування

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
    
    @property    
    def get_documents_for_export(self):
        """
        Повертає рядок з деталями документів, розділеними символом нового рядка.
        """

        return "\n".join(
            [f"{doc.oid.cipher} (підг. № {doc.document_number} від {doc.doc_process_date.strftime('%d.%m.%Y')})" for doc in self.registered_documents.all()]
        )
    
    def __str__(self):
        return f"Відправка до ДССЗЗІ №{self.outgoing_letter_number} від {self.outgoing_letter_date.strftime('%d.%m.%Y')}"
    @property
    def get_units_for_export(self):
        """
        Повертає рядок з кодами ВЧ, розділеними комою.
        """
        # prefetch_related('units') у view робить цей запит ефективним
        return ", ".join([unit.code for unit in self.units.all()])

   
    class Meta:
        verbose_name = "ДССЗЗІ: АА відправка на реєстрацію"
        verbose_name_plural = "ДССЗЗІ: АА відправки на реєстрацію"
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
    
    @property
    def get_registered_acts_for_export(self):
        """
        Повертає відформатований рядок з деталями актів для експорту.
        """
        if not hasattr(self, 'attestation_registration_sent') or not self.attestation_registration_sent:
            return "ші not hasattr"
        
        items = []
        for act_doc in self.attestation_registration_sent.registered_documents.all():
            reg_num = act_doc.dsszzi_registered_number or "немає"
            reg_date_str = act_doc.dsszzi_registered_date.strftime('%d.%m.%Y') if act_doc.dsszzi_registered_date else "N/A"
            items.append(
                f"{act_doc.oid.cipher} (Акт №{act_doc.document_number}, Реєстр.№{reg_num} від {reg_date_str})"
            )
        return "\n".join(items)
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
        verbose_name = "ДССЗЗІ: АА відповідь"
        verbose_name_plural = "ДССЗЗІ: АА відповіді"
        ordering = ['-response_letter_date', '-id']

class WorkCompletionRegistration(models.Model):
    """
    Модель для фіксації відправки Актів Завершення Робіт (АЗР) на реєстрацію.
    Один запис = один вихідний лист, що може містити декілька АЗР.
    """
    outgoing_letter_number = models.CharField(max_length=50, verbose_name="Вихідний номер супровідного листа")
    outgoing_letter_date = models.DateField(verbose_name="Дата вихідного супровідного листа")
    # Зв'язок ManyToMany з ОІД, щоб знати, які ОІДи були в цьому листі
    oids = models.ManyToManyField(OID, verbose_name="ОІДи, що згадуються у відправці")
    note = models.TextField(blank=True, null=True, verbose_name="Примітки до відправки")

    # Ключовий зв'язок: один лист може містити багато документів (АЗР)
    documents = models.ManyToManyField(
        'Document',
        verbose_name="Документи (АЗР), відправлені на реєстрацію",
        related_name="completion_registrations"
    )
    send_by = models.ForeignKey(
        Person,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name="Хто створив запис"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()
    
    def save(self, *args, **kwargs):
        # Спочатку зберігаємо сам об'єкт, щоб він отримав ID
        super().save(*args, **kwargs)
        
        # Використовуємо .all() після збереження, щоб отримати доступ до M2M
        # Цей цикл пройде по всіх документах (АЗР), які були додані до цієї відправки
        for doc in self.documents.all():
            oid_to_update = doc.oid
            if oid_to_update:
                old_status = oid_to_update.get_status_display()
                new_status_enum = OIDStatusChoices.AZR_SEND

                if oid_to_update.status != new_status_enum:
                    oid_to_update.status = new_status_enum
                    oid_to_update.save(update_fields=['status'])
                    
                    # Створюємо запис в історії
                    OIDStatusChange.objects.create(
                        oid=oid_to_update,
                        old_status=old_status,
                        new_status=new_status_enum.label,
                        reason=f"АЗР (документ №{doc.document_number}) відправлено на реєстрацію в складі листа №{self.outgoing_letter_number}",
                        initiating_document=doc
                    )

    def __str__(self):
        return f"Відправка АЗР (лист №{self.outgoing_letter_number} від {self.outgoing_letter_date.strftime('%d.%m.%Y')})"

    class Meta:
        verbose_name = "ДССЗЗІ: АЗР відправка на реєстрацію"
        verbose_name_plural = "ДССЗЗІ: АЗР відправки на реєстрацію"
        ordering = ['-outgoing_letter_date']

class WorkCompletionResponse(models.Model):
    """
    Модель для фіксації отримання відповіді від ДССЗЗІ
    щодо реєстрації Актів Завершення Робіт.
    """
    # Зв'язок "один-до-одного" з відправкою
    registration_request = models.OneToOneField(
        WorkCompletionRegistration,
        on_delete=models.CASCADE,
        verbose_name="Запит на реєстрацію (відправлений лист)",
        related_name="response_received"
    )
    response_letter_number = models.CharField(
        max_length=50,
        verbose_name="Номер листа-відповіді від ДССЗЗІ"
    )
    response_letter_date = models.DateField(
        verbose_name="Дата листа-відповіді"
    )
    note = models.TextField(
        blank=True,
        null=True,
        verbose_name="Примітки до відповіді"
    )
    received_by = models.ForeignKey(
        Person,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name="Хто вніс відповідь"
    )
    received_at = models.DateTimeField(auto_now_add=True)
    history = HistoricalRecords()

    def __str__(self):
        return f"Відповідь на лист № {self.registration_request.outgoing_letter_number}"

    class Meta:
        verbose_name = "ДССЗЗІ: АЗР відповідь ДССЗЗІ"
        verbose_name_plural = "ДССЗЗІ: АЗР відповіді ДССЗЗІ"


class Document(models.Model):
    """
    Опрацьовані документи Залежить від типу ОІД та виду робіт.
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
    document_number = models.CharField(max_length=50, default='27/14-', verbose_name="Підг. № документа")
    doc_process_date = models.DateField(verbose_name="Дата опрацювання документу (Підг.№ від)") # Дата внесення документа
    work_date = models.DateField(verbose_name="Дата проведення робіт на ОІД") # Дата, коли роботи фактично проводилися
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
    processing_status = models.CharField(
        "Статус опрацювання документа",
        max_length=30,
        choices=DocumentProcessingStatusChoices.choices,
        default=DocumentProcessingStatusChoices.DRAFT,
        db_index=True
    )
    history = HistoricalRecords()

    # --- поля для реєстрації в ДССЗЗІ (для актів атестації) ---
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
	# --- НОВЕ ПОЛЕ ---
    # Цей зв'язок показує, в якому "конверті" цей АЗР був відправлений на реєстрацію
    wcr_submission = models.ForeignKey(
        WorkCompletionRegistration,
        on_delete=models.SET_NULL, # Якщо відправку видалять, документ залишиться
        null=True, blank=True,
        verbose_name="Відправка АЗР на реєстрацію",
        related_name="submitted_documents"
    )
    # --- КІНЕЦЬ полів для реєстрації в ДССЗЗІ (для актів атестації) ---
    
    @property
    def get_sent_info_for_export(self):
        """Повертає рядок з інформацією про відправку для експорту."""
        if self.attestation_registration_sent:
            reg = self.attestation_registration_sent
            date_str = reg.outgoing_letter_date.strftime('%d.%m.%Y')
            return f"№ {reg.outgoing_letter_number} від {date_str}"
        return "N/A"
    
    @property
    def get_response_info_for_export(self):
        """Повертає рядок з інформацією про відповідь для експорту."""
        if hasattr(self.attestation_registration_sent, 'response_received'):
            response = self.attestation_registration_sent.response_received
            date_str = response.response_letter_date.strftime('%d.%m.%Y')
            return f"№ {response.response_letter_number} від {date_str}"
        return "N/A"
    
    def save(self, *args, **kwargs):
        # === БЛОК 1: Логіка, що виконується ДО збереження в базу даних ===
		# 1.1. Розрахунок терміну дії (expiration_date)
        if self.document_type and self.document_type.has_expiration and self.document_type.duration_months and self.work_date:
            try:
                duration = int(self.document_type.duration_months)
                print(f"DEBUG: duration (from document_type.duration_months): {duration}")
                
                if duration > 0:
                    delta = relativedelta(months=duration)
                    if isinstance(self.work_date, str):
                        # Використовуємо self._parse_date, якщо він у вас є, 
                        # або просту конвертацію, якщо формат відомий (наприклад, 'YYYY-MM-DD')
                        try:
                            work_date_obj = datetime.datetime.strptime(self.work_date, '%Y-%m-%d').date()
                        except ValueError:
                            # Обробка помилки парсингу, якщо формат невірний
                            print(f"ERROR: work_date '{self.work_date}' має невірний формат!")
                            self.expiration_date = None
                            return super().save(*args, **kwargs) # Перериваємо збереження з None
                    elif self.work_date is not None:
                        work_date_obj = self.work_date
                    else:
                        # Якщо work_date порожній, пропускаємо
                        self.expiration_date = None
                        return super().save(*args, **kwargs)
        
                    # --- Використовуємо об'єкт дати для розрахунку ---
                    self.expiration_date = work_date_obj + delta
    
                    print(f"DEBUG: Calculated self.expiration_date object: {self.expiration_date}")
                else:
                    self.expiration_date = None
                    
            # --- ВИПРАВЛЕНИЙ БЛОК EXCEPT (тепер він має 'as e') ---
            except (ValueError, TypeError) as e:
                print(f"ERROR calculating expiration_date: {e}") 
                self.expiration_date = None
        else:
            self.expiration_date = None
        
        # 1.2. Отримуємо стан об'єкта з бази даних ДО того, як ми його змінимо.
        old_instance = self.__class__.objects.filter(pk=self.pk).first()
        
        # === БЛОК 2: Виконуємо стандартне збереження ===
        super().save(*args, **kwargs)

        # === БЛОК 3: Логіка "ефекту доміно" ПІСЛЯ збереження ===
        
        if not self.work_request_item:
            return
        # 1. Надійно визначаємо типи документів за їхніми назвами
        try:
                attestation_doc_type = DocumentType.objects.get(name__icontains='Акт атестації')
                ik_conclusion_doc_type = DocumentType.objects.get(name__icontains='Висновок')
                azr_act_doc_type = DocumentType.objects.get(name__icontains='Акт завершення')
                declaration_doc_type = DocumentType.objects.get(name__icontains='Декларація')  # НОВИЙ ТИП
        except DocumentType.DoesNotExist:
                # Якщо ключові типи документів не знайдено в базі, нічого не робимо
                return 

        is_attestation_act = self.document_type == attestation_doc_type
        is_ik_conclusion = self.document_type == ik_conclusion_doc_type
        is_azr_act = self.document_type == azr_act_doc_type
        
        
        if (is_attestation_act):
            print(f"DEBUG: save document ID {old_instance} (type: {is_attestation_act}) is_attestation_act ")
        if (is_ik_conclusion):
            print(f"DEBUG: save document ID {old_instance} (type: {is_ik_conclusion}) is_ik_conclusion ")
        if (is_azr_act):
            print(f"DEBUG: save document ID {old_instance} (type: {is_azr_act}) is_azr_act ")
                
        # 2. Перевіряємо умови-тригери для кожного типу документа
        
        # -- УМОВА ДЛЯ АТЕСТАЦІЇ, АЗР ТА ДЕКЛАРАЦІЇ --
        # Тригер: документи, які щойно отримали реєстраційний номер
        is_registered = bool(self.dsszzi_registered_number and self.dsszzi_registered_date)
        was_just_registered = not (old_instance and old_instance.dsszzi_registered_number) and is_registered

        should_process_registration = (is_attestation_act or is_azr_act) and was_just_registered
        
        # -- УМОВА ДЛЯ ІК --
        # Тригер: Просто створення документу "Висновок ІК"
        is_newly_created = old_instance is None
        
        should_process_ik = is_ik_conclusion and is_newly_created

        # --- Застосування логіки ---

        # 3. Обробляємо Work Request Item (якщо є)
        if self.work_request_item and (should_process_registration or should_process_ik):
                wri = self.work_request_item
                
                
                if should_process_registration:
                        # Для атестації, АЗР та декларації встановлюємо різні статуси залежно від типу
                        if is_attestation_act:
                                # Для атестації встановлюємо статус "До відправки"
                                if wri.status != WorkRequestStatusChoices.TO_SEND:
                                        wri.status = WorkRequestStatusChoices.TO_SEND
                                        wri.docs_actually_processed_on = self.doc_process_date or datetime.date.today()
                                        wri.save(update_fields=['status', 'docs_actually_processed_on'])
                        else:  # АЗР або Декларація
                                # Для АЗР та декларації встановлюємо статус "Виконано"
                                if wri.status != WorkRequestStatusChoices.COMPLETED:
                                        wri.status = WorkRequestStatusChoices.COMPLETED
                                        wri.docs_actually_processed_on = self.doc_process_date or datetime.date.today()
                                        wri.save(update_fields=['status', 'docs_actually_processed_on'])
                
                elif should_process_ik:
                        # Для ІК встановлюємо статус "Виконано"
                        if wri.status != WorkRequestStatusChoices.COMPLETED:
                                wri.status = WorkRequestStatusChoices.COMPLETED
                                wri.docs_actually_processed_on = self.doc_process_date or datetime.date.today()
                                wri.save(update_fields=['status', 'docs_actually_processed_on'])

        # 4. Обробляємо ОІД незалежно від наявності work_request_item
        if should_process_registration:
                # Знаходимо ОІД для оновлення
                oid_to_update = None
                
                if self.work_request_item:
                        # Якщо є пов'язаний work_request_item
                        oid_to_update = self.work_request_item.oid
                elif hasattr(self, 'oid') and self.oid:
                        # Якщо документ прямо пов'язаний з ОІД
                        oid_to_update = self.oid
                elif hasattr(self, 'get_related_oid'):
                        # Якщо є спеціальний метод для знаходження ОІД
                        oid_to_update = self.get_related_oid()
                
                if oid_to_update:
                        old_status = oid_to_update.get_status_display()
                        
                        if is_attestation_act:
                                # Логіка для атестації (як було раніше)
                                statuses_for_first_attestation = [
                                        OIDStatusChoices.NEW,
                                        OIDStatusChoices.RECEIVED_TZ, 
                                        OIDStatusChoices.RECEIVED_TZ_REPEAT,
                                        OIDStatusChoices.RECEIVED_TZ_APPROVE,
                                        OIDStatusChoices.RECEIVED_REQUEST_ATTESTATION,
                                        OIDStatusChoices.RECEIVED_REQUEST_PLAND_ATTESTATION,
                                        OIDStatusChoices.TERMINATED
                                ]
                                
                                if oid_to_update.status in statuses_for_first_attestation:
                                        new_status_enum = OIDStatusChoices.ATTESTED
                                        oid_to_update.status = new_status_enum
                                        oid_to_update.note = f"Об'єкт атестовано {self.doc_process_date.strftime('%d.%m.%Y') if self.doc_process_date else ''}. ||"
                                        oid_to_update.save(update_fields=['status', 'note'])
                                        
                                        # Створюємо запис в історії
                                        OIDStatusChange.objects.create(
                                                oid=oid_to_update,
                                                old_status=old_status,
                                                new_status=new_status_enum.label,
                                                reason=f"Атестацію завершено. Зареєстровано Акт атестації №{self.dsszzi_registered_number}",
                                                initiating_document=self
                                        )
                                
                                elif oid_to_update.status == OIDStatusChoices.ACTIVE:
                                        # Повторна атестація
                                        attestation_note = f"Проведено чергову атестацію ({self.doc_process_date.strftime('%d.%m.%Y') if self.doc_process_date else ''}). ||"
                                        oid_to_update.note = f"{attestation_note}\n{oid_to_update.note or ''}".strip()
                                        oid_to_update.save(update_fields=['note'])
                                        
                                        OIDStatusChange.objects.create(
                                                oid=oid_to_update,
                                                old_status=old_status,
                                                new_status=old_status,
                                                reason=f"Проведено чергову атестацію (Акт №{self.dsszzi_registered_number}) ||",
                                                initiating_document=self
                                        )
                        
                        elif is_azr_act:
                                # Логіка для АЗР - статус стає ACTIVE
                                new_status_enum = OIDStatusChoices.ACTIVE
                                if oid_to_update.status != new_status_enum:
                                        oid_to_update.status = new_status_enum
                                        oid_to_update.save(update_fields=['status'])
                                        
                                        # Формуємо причину для запису в історію
                                        reason_text = f"Зареєстровано АЗР №{self.dsszzi_registered_number} від {self.dsszzi_registered_date.strftime('%d.%m.%Y')}"
                                        
                                        OIDStatusChange.objects.create(
                                                oid=oid_to_update,
                                                old_status=old_status,
                                                new_status=new_status_enum.label,
                                                reason=reason_text,
                                                initiating_document=self
                                        )

        # 5. Обробляємо ІК незалежно від наявності work_request_item (як було раніше)
        if should_process_ik:
                # Знаходимо ОІД для оновлення
                oid_to_update = None
                
                if self.work_request_item:
                        # Якщо є пов'язаний work_request_item
                        oid_to_update = self.work_request_item.oid
                elif hasattr(self, 'oid') and self.oid:
                        # Якщо документ прямо пов'язаний з ОІД
                        oid_to_update = self.oid
                elif hasattr(self, 'get_related_oid'):
                        # Якщо є спеціальний метод для знаходження ОІД
                        oid_to_update = self.get_related_oid()
                
                if oid_to_update and oid_to_update.status == OIDStatusChoices.ACTIVE:
                        old_status = oid_to_update.get_status_display()
                        
                        # Додаємо нотатку про ІК
                        ik_note = f"Проведено інструментальний контроль ({self.doc_process_date.strftime('%d.%m.%Y') if self.doc_process_date else ''}). ||"
                        oid_to_update.note = f"{ik_note}\n{oid_to_update.note or ''}".strip()
                        oid_to_update.save(update_fields=['note'])
                        
                        # Створюємо запис в історії, але статус не змінюється (OIDStatusChoices.ACTIVE)
                        OIDStatusChange.objects.create(
                                oid=oid_to_update,
                                old_status=old_status,
                                new_status=old_status,  # Статус залишається ACTIVE
                                reason=f"Проведено інструментальний контроль (Висновок №{self.document_number} від {self.doc_process_date.strftime('%d.%m.%Y')}) ||",
                                initiating_document=self
                        )
                        
                # перевірка статуса на ОК
                elif oid_to_update.status != OIDStatusChoices.ACTIVE:
                        old_status = oid_to_update.get_status_display()
                        new_status_enum = OIDStatusChoices.ACTIVE
                        # Додаємо нотатку про ІК
                        ik_note = f"Уточнити попередній статус ОІД.(був {old_status if old_status else ''}) Проведено інструментальний контроль ({self.doc_process_date.strftime('%d.%m.%Y') if self.doc_process_date else ''}) роботи проводились {self.work_date.strftime('%d.%m.%Y') if self.work_date else ''}. ||"
                        oid_to_update.note = f"{ik_note}\n{oid_to_update.note or ''}".strip()
                        oid_to_update.save(update_fields=['note'])
                        oid_to_update.status = new_status_enum
                        
                        # Створюємо запис в історії, але статус не змінюється (OIDStatusChoices.ACTIVE)
                        OIDStatusChange.objects.create(
                                oid=oid_to_update,
                                old_status=old_status,
                                new_status=old_status,  # Статус залишається ACTIVE
                                reason=f"Проведено інструментальний контроль (Висновок №{self.document_number} від {self.doc_process_date.strftime('%d.%m.%Y')}) роботи проводились {self.work_date.strftime('%d.%m.%Y') if self.work_date else ''}.",
                                initiating_document=self
                        )

    def __str__(self):
        return f"{self.document_type.name} / {self.document_number} (ОІД: {self.oid.cipher})"
    
    class Meta:
        verbose_name = "Опрацьований документ"
        verbose_name_plural = "Опрацьовані документи"
        ordering = ['-doc_process_date', '-work_date']
            

# --------------------------------------------------------------------------
# ## МОДЕЛІ ДЛЯ ПРОЦЕСУ РЕЄСТРАЦІЇ ДЕКЛАРАЦІЙ ВІДПОВІДНОСТІ ##
# --------------------------------------------------------------------------

class DskEot(models.Model):
    """
    Нова сутність: ДСК ЕОТ.
    Це не ОІД, а окремий об'єкт для відстеження Декларацій.
    """
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, verbose_name="Військова частина", related_name="dsk_eots")
    cipher = models.CharField(max_length=200, verbose_name="Шифр")
    serial_number = models.CharField(max_length=200, verbose_name="Серійний номер", blank=True, null=True)
    inventory_number = models.CharField(max_length=200, verbose_name="Інвентарний номер", blank=True, null=True)
    room = models.CharField(max_length=255, verbose_name="Приміщення")
    security_level = models.CharField(max_length=50, default="ДСК", verbose_name="Гриф")
    note = models.TextField(blank=True, null=True, verbose_name="Примітки")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()

    def __str__(self):
        return f"ДСК ЕОТ: {self.cipher} (ВЧ: {self.unit.code})"

    class Meta:
        verbose_name = "ОІД ДСК ЕОТ"
        verbose_name_plural = "ОІД ДСК ЕОТ"
        ordering = ['unit', 'cipher']


class Declaration(models.Model):
    """
    НОВА, ОКРЕМА СУТНІСТЬ: Декларація відповідності.
    Не пов'язана з моделлю Document.
    """
    dsk_eot = models.ForeignKey(
        DskEot, 
        on_delete=models.CASCADE,
        verbose_name="Об'єкт ДСК ЕОТ",
        related_name="declarations"
    )
    prepared_number = models.CharField(
        max_length=50, 
        verbose_name="Підготовлений № Декларації"
    )
    prepared_date = models.DateField(
        verbose_name="Дата опрацювання Декларації"
    )
    # Поля для відповіді від ДССЗЗІ
    registered_number = models.CharField(
        max_length=50,
        blank=True, null=True,
        verbose_name="Зареєстрований № в ДССЗЗІ"
    )
    registered_date = models.DateField(
        blank=True, null=True,
        verbose_name="Дата реєстрації в ДССЗЗІ"
    )
    note = models.TextField(blank=True, null=True, verbose_name="Примітки")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()
    
    @property
    def get_status_display(self):
        if self.registered_number:
            return "Зареєстровано"
        if self.registrations.exists():
            return "Відправлено на реєстрацію"
        return "Чернетка"

    @property
    def get_submission_info(self):
        submission = self.registrations.first()
        if submission:
            return f"Лист №{submission.outgoing_letter_number} від {submission.outgoing_letter_date.strftime('%d.%m.%Y')}"
        return "-"
    def __str__(self):
        return f"Декларація №{self.prepared_number} для {self.dsk_eot.cipher}"

    class Meta:
        verbose_name = "ДССЗЗІ: Декларація відповідності відправка"
        verbose_name_plural = "ДССЗЗІ: Декларації відповідності відправка"
        ordering = ['-prepared_date']


class DeclarationRegistration(models.Model):
    """
    НОВА, ОБ'ЄДНАНА МОДЕЛЬ.
    Відстежує весь цикл реєстрації Декларації: відправку та отримання відповіді.
    Один запис = один вихідний лист.
    """
    # === ПОЛЯ, ЩО СТОСУЮТЬСЯ ВІДПРАВКИ ===
    outgoing_letter_number = models.CharField(
        max_length=50,
        verbose_name="Вихідний номер супровідного листа"
    )
    outgoing_letter_date = models.DateField(
        verbose_name="Дата вихідного супровідного листа"
    )
    # Зв'язок з деклараціями, які були в цьому листі
    declarations = models.ManyToManyField(
        Declaration,
        verbose_name="Декларації у відправці",
        related_name="registrations"
    )
    note = models.TextField(
        blank=True, null=True,
        verbose_name="Примітки до відправки"
    )
    created_by = models.ForeignKey(
        Person, on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name="Хто створив запис",
        related_name="created_declaration_registrations"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # === ПОЛЯ, ЩО СТОСУЮТЬСЯ ОТРИМАННЯ ВІДПОВІДІ (необов'язкові) ===
    response_letter_number = models.CharField(
        max_length=50, blank=True, null=True,
        verbose_name="Номер листа-відповіді"
    )
    response_letter_date = models.DateField(
        blank=True, null=True,
        verbose_name="Дата листа-відповіді"
    )
    response_note = models.TextField(
        blank=True, null=True,
        verbose_name="Примітки до відповіді"
    )
    response_by = models.ForeignKey(
        Person, on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name="Хто вніс відповідь",
        related_name="recorded_declaration_responses"
    )
    response_at = models.DateTimeField(
        blank=True, null=True,
        verbose_name="Дата внесення відповіді"
    )

    history = HistoricalRecords()

    def __str__(self):
        return f"Реєстрація Декларацій (лист №{self.outgoing_letter_number} від {self.outgoing_letter_date.strftime('%d.%m.%Y')})"
    
    @property
    def is_response_received(self):
        """Перевіряє, чи була внесена відповідь."""
        return bool(self.response_letter_number and self.response_letter_date)

    class Meta:
        verbose_name = "ДССЗЗІ: Декларація відповідь"
        verbose_name_plural = "ДССЗЗІ: Декларація відповіді"
        ordering = ['-outgoing_letter_date']


# --------------------------------------------------------------------------
# ## КІНЕЦЬ МОДЕЛІ ДЛЯ ПРОЦЕСУ РЕЄСТРАЦІЇ ДЕКЛАРАЦІЙ ВІДПОВІДНОСТІ ##
# --------------------------------------------------------------------------

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
    history = HistoricalRecords()
    def __str__(self):
        return f"{self.oid.cipher}: {self.old_status} → {self.new_status} ({self.changed_at.strftime('%Y-%m-%d')})"

    class Meta:
        verbose_name = "ДССЗЗІ: Зміна статусу ОІД"
        verbose_name_plural = "ДССЗЗІ: Зміни статусу ОІД"
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
        verbose_name = "Опрацювання результат відрядження для частини"
        verbose_name_plural = "Опрацювання результати відрядження для частин"
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
        related_name='processed_technical_tasks'
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
    
    def save(self, *args, **kwargs):
        is_new = self._state.adding
        # Отримуємо старий стан об'єкта з бази даних ДО збереження
        old_instance = TechnicalTask.objects.filter(pk=self.pk).first()

        # Виконуємо збереження
        super().save(*args, **kwargs)
        
        oid_to_update = self.oid
        if not oid_to_update:
            return # Якщо ОІД не вказано, нічого не робимо

        # --- Логіка для створення ---
        if is_new:
            old_status = oid_to_update.get_status_display()
            new_status_enum = OIDStatusChoices.RECEIVED_TZ
            
            if oid_to_update.status != new_status_enum:
                oid_to_update.status = new_status_enum
                oid_to_update.save(update_fields=['status'])

        # --- Логіка для погодження ---
        # Перевіряємо, чи змінився статус на "Погоджено"
        elif old_instance and old_instance.review_result != self.review_result:
            old_status = oid_to_update.get_status_display()
            if self.review_result == DocumentReviewResultChoices.FOR_REVISION:
                new_status_enum = OIDStatusChoices.RECEIVED_TZ_REPEAT
                reason = f"ТЗ №{self.input_number} відправлено на доопрацювання"
                
                if oid_to_update.status != new_status_enum:
                    oid_to_update.status = new_status_enum
                    oid_to_update.save(update_fields=['status'])
                    
                    OIDStatusChange.objects.create(
						oid=oid_to_update,
						old_status=old_status,
						new_status=new_status_enum.label,
						reason=reason
					)
					
            elif self.review_result == DocumentReviewResultChoices.AWAITING_DOCS:
                new_status_enum = OIDStatusChoices.RECEIVED_TZ_REPEAT
                reason = f"ТЗ №{self.input_number} очікує додаткові документи"
                if oid_to_update.status != new_status_enum:
                    oid_to_update.status = new_status_enum
                    oid_to_update.save(update_fields=['status'])
                    OIDStatusChange.objects.create(
						oid=oid_to_update,
						old_status=old_status,
						new_status=new_status_enum.label,
						reason=reason
					)
            elif self.review_result == DocumentReviewResultChoices.APPROVED:
                new_status_enum = OIDStatusChoices.RECEIVED_TZ_APPROVE
                reason = f"ТЗ №{self.input_number} погоджено"
                if oid_to_update.status != new_status_enum:
                    oid_to_update.status = new_status_enum
                    oid_to_update.save(update_fields=['status'])
                    OIDStatusChange.objects.create(
						oid=oid_to_update,
						old_status=old_status,
						new_status=new_status_enum.label,
						reason=reason
					)
    def __str__(self):
        return f"ТЗ/МЗ від в/ч {self.oid.unit.code} на ОІД: {self.oid.cipher} (статус : {self.get_review_result_display()}) від {self.input_date.strftime("%d.%m.%Y")} вх.№{self.input_number}"

    class Meta:
        verbose_name = "Технічне Завдання" # Змінено
        verbose_name_plural = "Технічні Завдання" # Змінено
        ordering = ['-input_date', '-read_till_date', '-created_at'] # Додав created_at
# 



# --- Створення системи процесів ---
class ProcessTemplate(models.Model):
    """Шаблон процесу, """
    name = models.CharField("Назва шаблону процесу", max_length=255, unique=True)
    description = models.TextField("Опис", blank=True)
    # Поля для визначення, до якого типу ОІД застосовується цей шаблон
    applies_to_oid_type = MultiSelectField(
        "Тип ОІД", choices=OIDTypeChoices.choices, max_length=100
    )
    applies_to_pemin_subtype = MultiSelectField(
        "Підтип ПЕМІН", choices=PeminSubTypeChoices.choices, max_length=100, blank=True, null=True
    )
    is_active = models.BooleanField("Активний", default=True, help_text="Чи можна використовувати цей шаблон для нових ОІД")

    def __str__(self):
        return self.name
    class Meta:
        verbose_name = "Шаблон процесу"
        verbose_name_plural = "БізнесПроцес: 1. Шаблони процесів"
        ordering = ['-id']
        
class ProcessStep(models.Model):
    """Один крок у шаблоні процесу."""
    class ResponsiblePartyChoices(models.TextChoices):
        VTZI = 'ВТЗІ', 'ВТЗІ'
        GU = 'ГУ', 'ГУ'
        UNIT = 'в/ч', 'в/ч'
        DSSZZI = 'ДССЗЗІ', 'ДССЗЗІ'

    template = models.ForeignKey(ProcessTemplate, on_delete=models.CASCADE, related_name="steps", verbose_name="Шаблон")
    name = models.CharField("Назва кроку", max_length=255)
    order = models.PositiveIntegerField("Порядок виконання", default=10)
    
    # Який документ має бути створений/опрацьований на цьому кроці
    document_type = models.ForeignKey(DocumentType, on_delete=models.PROTECT, verbose_name="Тип документа для кроку")
    
    # Який статус документа завершує цей крок
    trigger_document_status = models.CharField(
        "Статус документа, що завершує крок",
        max_length=30,
        choices=DocumentProcessingStatusChoices.choices,
        default=DocumentProcessingStatusChoices.COMPLETED
    )
    
    responsible_party = models.CharField("Відповідальний за крок", max_length=20, choices=ResponsiblePartyChoices.choices)
    description = models.TextField("Інструкції до кроку", blank=True)

    class Meta:
        verbose_name = "Крок у шаблоні процесу"
        verbose_name_plural = "БізнесПроцес: 2. Кроки у шаблоні процесу"
        ordering = ['template', 'order']
        unique_together = ('template', 'order')

    def __str__(self):
        return f"{self.template.name} - Крок {self.order}: {self.name}"

  
class OIDProcess(models.Model):
    """Екземпляр процесу для конкретного ОІД."""
    oid = models.OneToOneField(OID, on_delete=models.CASCADE, related_name="active_process", verbose_name="ОІД")
    template = models.ForeignKey(ProcessTemplate, on_delete=models.PROTECT, verbose_name="Використаний шаблон")
    start_date = models.DateTimeField(auto_now_add=True, verbose_name="Дата початку")
    end_date = models.DateTimeField("Дата завершення", null=True, blank=True)
    status = models.CharField("Статус процесу", max_length=20, choices=ProcessStepStatusChoices.choices, default=ProcessStepStatusChoices.PENDING)

    def __str__(self):
        return f"Процес '{self.template.name}' для ОІД {self.oid.cipher}"
    class Meta:
        verbose_name = "Екземпляр процесу для конкретного ОІД."
        verbose_name_plural = "БізнесПроцес: 3. Екземпляри процесів для конкретних ОІД."
        ordering = ['-id']
        
class OIDProcessStepInstance(models.Model):
    """Конкретний екземпляр кроку для процесу ОІД."""
    oid_process = models.ForeignKey(OIDProcess, on_delete=models.CASCADE, related_name="step_instances", verbose_name="Процес ОІД")
    process_step = models.ForeignKey(ProcessStep, on_delete=models.PROTECT, verbose_name="Крок з шаблону")
    status = models.CharField("Статус кроку", max_length=20, choices=ProcessStepStatusChoices.choices, default=ProcessStepStatusChoices.PENDING)
    linked_document = models.ForeignKey(
        Document, on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name="Документ, що виконав крок"
    )
    completed_at = models.DateTimeField("Дата виконання", null=True, blank=True)

    class Meta:
        ordering = ['oid_process', 'process_step__order']

    def __str__(self):
        return f"{self.oid_process.oid.cipher}: {self.process_step.name} ({self.get_status_display()})"
    class Meta:
        verbose_name = "Конкретні екземпляри кроків для процесу ОІД."
        verbose_name_plural = "БізнесПроцес: 4. Екземпляри кроку для процесу ОІД."
        ordering = ['-id']


# tast manager 
# Припускаємо, що модель Person імпортована або знаходиться в цьому ж файлі
# from .models import Person 

# --- Модель Проєкту (Project) ---
class Project(models.Model):
    name = models.CharField("Назва проєкту", max_length=255)
    description = models.TextField("Опис", blank=True, null=True)
    is_active = models.BooleanField("Активний", default=True)
    group = models.CharField("Відділ/Група", max_length=20, choices=PersonGroup.choices, default=PersonGroup.ZAG)
    class Meta:
        verbose_name = "Проєкт"
        verbose_name_plural = "Проєкти"

# --- Модель Статусу (Status) ---
# Статуси можуть бути глобальними або прив'язаними до проєкту. 
# Зробимо їх глобальними з можливістю прив'язати до проєкту
class Status(models.Model):
    name = models.CharField("Назва статусу", max_length=50)
    color = models.CharField("Колір (HEX або назва)", max_length=20, default="#d1d5db") # Приклад: сірий
    is_default = models.BooleanField("Стандартний", default=False)
    # Якщо status прив'язаний до певного проекту, він буде відображатися тільки там
    project = models.ForeignKey(Project, on_delete=models.CASCADE, null=True, blank=True, related_name='custom_statuses')

    class Meta:
        verbose_name = "Статус завдання"
        verbose_name_plural = "Статуси завдання"
        unique_together = ('name', 'project') # Статус має бути унікальним в рамках проєкту

# --- Модель Завдання (Task) ---
class Task(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks', verbose_name="Проєкт")
    title = models.CharField("Заголовок", max_length=255)
    description = models.TextField("Опис", blank=True, null=True)
    assignee = models.ForeignKey(Person, on_delete=models.SET_NULL, null=True, related_name='assigned_tasks', verbose_name="Виконавець")
    due_date = models.DateField("Термін виконання", null=True, blank=True)
    created_by = models.ForeignKey(Person, on_delete=models.SET_NULL, null=True, related_name='created_tasks', verbose_name="Автор")
    status = models.ForeignKey(Status, on_delete=models.PROTECT, related_name='tasks', verbose_name="Поточний статус")
    is_completed = models.BooleanField("Виконано", default=False)
    completed_at = models.DateTimeField("Дата виконання", null=True, blank=True)
    
    class Meta:
        verbose_name = "Завдання"
        verbose_name_plural = "Завдання"