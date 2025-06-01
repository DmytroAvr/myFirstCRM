import os
import django
from django.core.management.base import BaseCommand

# Налаштуйте змінну оточення DJANGO_SETTINGS_MODULE
# Замініть 'your_project.settings' на фактичний шлях до файлу налаштувань вашого проекту
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings') 
django.setup()

from oids.models import TerritorialManagement, Unit # Замініть 'oids' на назву вашого додатку

DATA = [
    {"otu": "Західне оперативно-територіальне об'єднання НГУ (м. Львів)", "unit_name": "Територіальне управління", "unit_code": "2250", "city": "м. Львів", "distance": 544},
    {"otu": "Західне оперативно-територіальне об'єднання НГУ (м. Львів)", "unit_name": "2 окрема Галицька бригада", "unit_code": "3002", "city": "м. Львів", "distance": 544},
    {"otu": "Західне оперативно-територіальне об'єднання НГУ (м. Львів)", "unit_name": "15-й окремий батальйон", "unit_code": "3055", "city": "м. Рівне", "distance": 324},
    {"otu": "Західне оперативно-територіальне об'єднання НГУ (м. Львів)", "unit_name": "14 бригада оперативного призначення імені Івана Богуна", "unit_code": "3028", "city": "м. Калинівка Вінницької області", "distance": 242},
    {"otu": "Західне оперативно-територіальне об'єднання НГУ (м. Львів)", "unit_name": "13 окремий батальйон", "unit_code": "3053", "city": "м. Хмельницький", "distance": 348},
    {"otu": "Західне оперативно-територіальне об'єднання НГУ (м. Львів)", "unit_name": "32 окремий батальйон", "unit_code": "1141", "city": "м. Луцьк", "distance": 398},
    {"otu": "Західне оперативно-територіальне об'єднання НГУ (м. Львів)", "unit_name": "40 полк", "unit_code": "3008", "city": "м. Вінниця", "distance": 266},
    {"otu": "Західне оперативно-територіальне об'єднання НГУ (м. Львів)", "unit_name": "45 полк оперативного призначення імені Олександра Красіцького", "unit_code": "4114", "city": "м. Львів", "distance": 544},
    {"otu": "Західне оперативно-територіальне об'єднання НГУ (м. Львів)", "unit_name": "50 полк", "unit_code": "1241", "city": "м. Івано-Франківськ", "distance": 599},
    {"otu": "Південне оперативно-територіальне об'єднання НГУ (м. Одеса)", "unit_name": "Територіальне управління", "unit_code": "3003", "city": "м. Одеса", "distance": 480},
    {"otu": "Південне оперативно-територіальне об'єднання НГУ (м. Одеса)", "unit_name": "15-та бригада оперативного призначення", "unit_code": "3029", "city": "м. Запоріжжя", "distance": 637},
    {"otu": "Південне оперативно-територіальне об'єднання НГУ (м. Одеса)", "unit_name": "11-та окрема бригада охорони громадського порядку", "unit_code": "3012", "city": "м. Одеса", "distance": 480},
    {"otu": "Південне оперативно-територіальне об'єднання НГУ (м. Одеса)", "unit_name": "18-й окремий батальйон", "unit_code": "3058", "city": "м. Ізмаїл", "distance": 677},
    {"otu": "Південне оперативно-територіальне об'єднання НГУ (м. Одеса)", "unit_name": "34-й окремий полк", "unit_code": "3056", "city": "м. Херсон", "distance": 533},
    {"otu": "Південне оперативно-територіальне об'єднання НГУ (м. Одеса)", "unit_name": "19 полк охорони громадського порядку", "unit_code": "3039", "city": "м. Миколаїв", "distance": 466},
    {"otu": "Південне оперативно-територіальне об'єднання НГУ (м. Одеса)", "unit_name": "19 окремий батальйон (конвойний)", "unit_code": "3026", "city": "м. Запоріжжя", "distance": 637},
    {"otu": "Південне оперативно-територіальне об'єднання НГУ (м. Одеса)", "unit_name": "23 окрема бригада охорони громадського порядку", "unit_code": "3033", "city": "м. Запоріжжя", "distance": 637},
    {"otu": "Південне оперативно-територіальне об'єднання НГУ (м. Одеса)", "unit_name": "34 окремий батальйон (конвойний)", "unit_code": "3014", "city": "м. Одеса", "distance": 480},
    {"otu": "Північне оперативно-територіальне об'єднання НГУ (м. Київ)", "unit_name": "Територіальне управління", "unit_code": "3001", "city": "м. Київ", "distance": 0},
    {"otu": "Північне оперативно-територіальне об'єднання НГУ (м. Київ)", "unit_name": "1 Президентська бригада оперативного призначення імені гетьмана Петра Дорошенка", "unit_code": "3027", "city": "смт. Нові Петрівці Київської області", "distance": 25},
    {"otu": "Північне оперативно-територіальне об'єднання НГУ (м. Київ)", "unit_name": "25 окрема бригада охорони громадського порядку", "unit_code": "3030", "city": "м. Київ", "distance": 0},
    {"otu": "Північне оперативно-територіальне об'єднання НГУ (м. Київ)", "unit_name": "25 окремий батальйон", "unit_code": "3061", "city": "м. Черкаси", "distance": 201},
    {"otu": "Північне оперативно-територіальне об'єднання НГУ (м. Київ)", "unit_name": "27 окрема бригада (конвойна)", "unit_code": "3066", "city": "м. Київ", "distance": 0},
    {"otu": "Північне оперативно-територіальне об'єднання НГУ (м. Київ)", "unit_name": "22 окремий батальйон", "unit_code": "3082", "city": "м. Чернігів", "distance": 151},
    {"otu": "Північне оперативно-територіальне об'єднання НГУ (м. Київ)", "unit_name": "75 окремий батальйон", "unit_code": "3047", "city": "м. Житомир", "distance": 140},
    {"otu": "Північне оперативно-територіальне об'єднання НГУ (м. Київ)", "unit_name": "Міжнародний міжвідомчий багатопрофільний центр підготовки підрозділів", "unit_code": "3070", "city": "с. Старе Київської області", "distance": 60},
    {"otu": "Східне оперативно-територіальне об'єднання НГУ (м. Харків)", "unit_name": "Територіальне управління", "unit_code": "2240", "city": "м. Харків (м. Донецьк)", "distance": 487},
    {"otu": "Східне оперативно-територіальне об'єднання НГУ (м. Харків)", "unit_name": "3 бригада оперативного призначення", "unit_code": "3017", "city": "м. Харків", "distance": 487},
    {"otu": "Східне оперативно-територіальне об'єднання НГУ (м. Харків)", "unit_name": "5 окрема Слобожанська бригада", "unit_code": "3005", "city": "м. Харків", "distance": 487},
    {"otu": "Східне оперативно-територіальне об'єднання НГУ (м. Харків)", "unit_name": "11 окремий батальйон", "unit_code": "3051", "city": "м. Суми", "distance": 339},
    {"otu": "Східне оперативно-територіальне об'єднання НГУ (м. Харків)", "unit_name": "15 окремий полк", "unit_code": "3035", "city": "м. Слов’янськ", "distance": 600},
    {"otu": "Східне оперативно-територіальне об'єднання НГУ (м. Харків)", "unit_name": "Навчальний центр з підготовки та перепідготовки військовослужбовців за контрактом", "unit_code": "3071", "city": "с. Малинівка Харківської області", "distance": 490},
    {"otu": "Центральне оперативно-територіальне об'єднання НГУ (м. Дніпро)", "unit_name": "Територіальне управління", "unit_code": "3006", "city": "м. Дніпро", "distance": 479},
    {"otu": "Центральне оперативно-територіальне об'єднання НГУ (м. Дніпро)", "unit_name": "12 окремий батальйон", "unit_code": "3052", "city": "м. Полтава", "distance": 343},
    {"otu": "Центральне оперативно-територіальне об'єднання НГУ (м. Дніпро)", "unit_name": "14 окремий батальйон (конвойний)", "unit_code": "3054", "city": "м. Дніпро", "distance": 479},
    {"otu": "Центральне оперативно-територіальне об'єднання НГУ (м. Дніпро)", "unit_name": "16 полк охорони громадського порядку", "unit_code": "3036", "city": "м. Дніпро", "distance": 479},
    {"otu": "Центральне оперативно-територіальне об'єднання НГУ (м. Дніпро)", "unit_name": "21 окрема бригада охорони громадського порядку", "unit_code": "3011", "city": "м. Кривий Ріг", "distance": 420},
    {"otu": "Центральне оперативно-територіальне об'єднання НГУ (м. Дніпро)", "unit_name": "26 окремий батальйон", "unit_code": "3059", "city": "м. Кременчук", "distance": 350},
    {"otu": "Головне управління (м. Київ)", "unit_name": "4 бригада оперативного призначення", "unit_code": "3018", "city": "смт. Гостомель Київської області", "distance": 30},
    {"otu": "Головне управління (м. Київ)", "unit_name": "1 полк охорони особливо важливих державних об'єктів", "unit_code": "3021", "city": "м. Дніпро", "distance": 479},
    {"otu": "Головне управління (м. Київ)", "unit_name": "2 полк охорони особливо важливих державних об'єктів", "unit_code": "3022", "city": "м. Шостка Сумської області", "distance": 355},
    {"otu": "Головне управління (м. Київ)", "unit_name": "3 полк охорони особливо важливих державних об'єктів", "unit_code": "3023", "city": "м. Донецьк", "distance": 729},
    {"otu": "Головне управління (м. Київ)", "unit_name": "4 полк охорони особливо важливих державних об'єктів", "unit_code": "3024", "city": "м. Павлоград", "distance": 520},
    {"otu": "Головне управління (м. Київ)", "unit_name": "1 окремий батальйон охорони ОВДО", "unit_code": "3041", "city": "м. Славутич Київської області", "distance": 200},
    {"otu": "Головне управління (м. Київ)", "unit_name": "3 окремий батальйон охорони ОВДО", "unit_code": "3043", "city": "м. Нетішин Хмельницької області", "distance": 350},
    {"otu": "Головне управління (м. Київ)", "unit_name": "4 окремий батальйон охорони ОВДО", "unit_code": "3044", "city": "м. Южноукраїнськ Миколаївської області", "distance": 400},
    {"otu": "Головне управління (м. Київ)", "unit_name": "5 окремий батальйон охорони ОВДО", "unit_code": "3045", "city": "м. Вараш Рівненської області", "distance": 400},
    {"otu": "Головне управління (м. Київ)", "unit_name": "22 окрема бригада з охорони дипломатичних представництв і консульських установ іноземних держав", "unit_code": "2260", "city": "м. Київ", "distance": 0},
    {"otu": "Головне управління (м. Київ)", "unit_name": "Гвардійська авіаційна база", "unit_code": "2269", "city": "м. Олександрія Кіровоградської області", "distance": 530},
    {"otu": "Головне управління (м. Київ)", "unit_name": "Об'єднаний вузол зв'язку", "unit_code": "3077", "city": "смт. Нові Петрівці Київської області", "distance": 24},
    {"otu": "Головне управління (м. Київ)", "unit_name": "Окремий батальйон охорони та забезпечення ГУ НГУ", "unit_code": "3078", "city": "м. Київ", "distance": 0},
    {"otu": "Головне управління (м. Київ)", "unit_name": "Центральна база зберігання зброї та боєприпасів", "unit_code": "2276", "city": "м. Охтирка Сумської області", "distance": 300},
    {"otu": "Головне управління (м. Київ)", "unit_name": "Центральна база забезпечення пально-мастильних матеріалів", "unit_code": "2274", "city": "м. Запоріжжя", "distance": 637},
    {"otu": "Головне управління (м. Київ)", "unit_name": "Військовий госпіталь", "unit_code": "3080", "city": "м. Золочів Львівської області", "distance": 532},
    {"otu": "Головне управління (м. Київ)", "unit_name": "Військовий ансамбль", "unit_code": "3081", "city": "м. Київ", "distance": 0},
    {"otu": "Головне управління (м. Київ)", "unit_name": "Навчальний центр Національної гвардії України", "unit_code": "3007", "city": "м. Золочів Львівської області", "distance": 532},
]


class Command(BaseCommand):
    help = 'Populates the database with TerritorialManagements and Units'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting data population...'))

        territorial_managements_cache = {}

        # Перший прохід: створюємо TerritorialManagement
        # і кешуємо їх для подальшого використання
        for item_data in DATA:
            otu_name = item_data['otu']
            unit_name = item_data['unit_name']
            unit_code_for_tm = item_data['unit_code']

            if otu_name not in territorial_managements_cache:
                # "Головне управління (м. Київ)" не має окремого рядка "Територіальне управління" з кодом.
                # Для нього код ТУ будемо генерувати або використовувати спеціальний.
                # В даному випадку, оскільки "Головне управління (м. Київ)" є ТУ для багатьох частин,
                # але не має власної "в/ч ТУ" у списку, ми можемо припустити, що код для нього
                # може бути не таким важливим, або ми можемо використовувати спеціальний.
                # Поки що, якщо "unit_name" == "Територіальне управління", то це код ТУ.
                # Для "Головного управління" створимо ТУ, якщо воно ще не створене,
                # з кодом, наприклад, "ГУНГУ" або кодом першої в/ч, що до нього належить.
                # В даному прикладі, ми очікуємо, що для кожного ОТУ буде рядок "Територіальне управління".
                
                tm_code = None
                # Шукаємо рядок, що визначає код для цього ОТУ
                for tm_data_lookup in DATA:
                    if tm_data_lookup['otu'] == otu_name and tm_data_lookup['unit_name'] == "Територіальне управління":
                        tm_code = tm_data_lookup['unit_code']
                        break
                
                if not tm_code and otu_name == "Головне управління (м. Київ)":
                    # Спеціальний випадок для Головного управління, якщо воно не має явного коду ТУ
                    # Можна використати, наприклад, код першої його частини або спеціальний код
                    # Для простоти, зараз візьмемо код першої частини, що належить до ГУ
                    # Або ж, можна задати йому фіксований код.
                    # Наприклад, "ГУНГУ01"
                    # Важливо: код ТУ має бути унікальним.
                    # У наданих даних для "Головне управління (м. Київ)" немає рядка "Територіальне управління",
                    # тому ми не можемо взяти код звідти.
                    # Припустимо, що для "Головне управління (м. Київ)" кодом буде назва самого управління,
                    # або ми можемо вибрати код однієї з його частин як "представницький".
                    # Для прикладу, зробимо його код "GU_KYIV", але краще б він був у даних.
                    # Якщо "Головне управління (м. Київ)" вказано як ОТУ для якоїсь частини,
                    # але не має "Територіальне управління" як окремої частини з кодом,
                    # то створимо його з унікальним кодом.
                    # Давайте перевіримо, чи є рядок "Територіальне управління" для "Головне управління (м. Київ)"
                    gu_tu_exists = any(d['otu'] == "Головне управління (м. Київ)" and d['unit_name'] == "Територіальне управління" for d in DATA)
                    if not gu_tu_exists:
                         # Якщо для ГУ немає рядка "Територіальне управління", але воно використовується як ТУ
                         # для інших частин, створимо його з унікальним кодом.
                         # Важливо: для цього прикладу я використаю "GU_NGU_KYIV" як код.
                         # В реальному сценарії, краще мати це визначено в даних.
                        tm_code = "GU_NGU_KYIV" # Потенційно, це може бути не унікальним, якщо вже є такий код.
                                                # Краще, якщо б дані для ГУ також мали рядок "Територіальне управління" з кодом.
                                                # Оскільки "Головне управління (м. Київ)" є в списку ОТУ, але для нього немає
                                                # рядка з unit_name="Територіальне управління", ми створимо ТУ з кодом,
                                                # наприклад, згенерованим або фіксованим.
                                                # В наданих даних немає окремої в/ч "Територіальне управління" для "Головне управління (м. Київ)"
                                                # Отже, ми створимо ТУ для "Головне управління (м. Київ)" з його назвою як кодом (або іншим унікальним ідентифікатором).
                                                # Проте, модель вимагає унікальний `code`.
                                                # Для "Головне управління (м. Київ)" у вас немає рядка "Територіальне управління"
                                                # та відповідного "Номер в/ч". Це потрібно визначити.
                                                # Як тимчасове рішення, я використаю фіксований код "0000" для ГУ,
                                                # припускаючи, що він буде унікальним і що ви потім його оновить.
                                                # АБО, якщо "Головне управління (м. Київ)" є ОТУ, але не має рядка "Територіальне управління",
                                                # то ми НЕ створюємо для нього окремий запис ТУ на цьому етапі, а обробляємо це пізніше.
                                                # Це складний момент, бо структура даних не повністю відповідає.
                                                # Давайте припустимо, що якщо для ОТУ немає рядка "Територіальне управління",
                                                # то ми не можемо створити для нього TerritorialManagement на основі цих даних.
                                                # Однак, "Головне управління (м. Київ)" явно виступає як ТУ для інших частин.
                                                # Краще додати рядок для ГУ:
                                                # {"otu": "Головне управління (м. Київ)", "unit_name": "Територіальне управління", "unit_code": "ГУ01", "city": "м. Київ", "distance": 0},

                        # Оновлений підхід: Якщо для ОТУ немає "Територіального управління" з кодом,
                        # але він використовується як ТУ, ми створимо його з унікальним кодом (наприклад, на основі назви).
                        # Для "Головне управління (м. Київ)", оскільки немає явного коду ТУ в даних,
                        # використаємо код "GU_MAIN_KYIV". Переконайтесь, що цей код унікальний.
                        if otu_name == "Головне управління (м. Київ)" and not tm_code:
                            tm_code = "GU_KYIV_HEAD" # Унікальний код для ГУ

                if tm_code: # Створюємо ТУ тільки якщо є код
                    management, created = TerritorialManagement.objects.get_or_create(
                        code=tm_code,
                        defaults={'name': otu_name}
                    )
                    if created:
                        self.stdout.write(self.style.SUCCESS(f'Successfully created TerritorialManagement: {management.name} with code {management.code}'))
                    else:
                        # Якщо вже існує, оновимо назву, якщо вона змінилася (хоча тут вона буде та сама)
                        if management.name != otu_name:
                            management.name = otu_name
                            management.save()
                            self.stdout.write(self.style.WARNING(f'TerritorialManagement with code {tm_code} already existed. Updated name to: {otu_name}'))
                        else:
                             self.stdout.write(self.style.WARNING(f'TerritorialManagement with code {tm_code} ({otu_name}) already exists.'))
                    territorial_managements_cache[otu_name] = management
                elif otu_name == "Головне управління (м. Київ)": # Спеціальна обробка для ГУ, якщо не знайдено коду
                     management, created = TerritorialManagement.objects.get_or_create(
                        code="GU_KYIV_HEAD", # Повинно бути унікальним
                        defaults={'name': otu_name}
                    )
                     if created:
                        self.stdout.write(self.style.SUCCESS(f'Successfully created TerritorialManagement (special case for GU): {management.name} with code {management.code}'))
                     else:
                        self.stdout.write(self.style.WARNING(f'TerritorialManagement with code GU_KYIV_HEAD ({otu_name}) already exists.'))
                     territorial_managements_cache[otu_name] = management
                else:
                    self.stdout.write(self.style.ERROR(f'Could not find or create TerritorialManagement for OTU: {otu_name} due to missing TM code line.'))


        # Другий прохід: створюємо Units і пов'язуємо їх з TerritorialManagement
        created_units_count = 0
        updated_units_count = 0
        skipped_units_count = 0
        
        # Перевірка дублікатів unit_code перед створенням
        existing_unit_codes = set(Unit.objects.values_list('code', flat=True))
        
        for item_data in DATA:
            unit_code = item_data['unit_code']
            unit_name = item_data['unit_name']
            city = item_data['city']
            distance = item_data['distance']
            otu_name = item_data['otu']

            current_tm = territorial_managements_cache.get(otu_name)

            if not current_tm:
                self.stdout.write(self.style.ERROR(f'TerritorialManagement for {otu_name} not found in cache. Skipping unit {unit_code} - {unit_name}. Ensure TM for this OTU is correctly defined.'))
                skipped_units_count += 1
                continue
            
            # Обробка випадків, коли unit_name може бути порожнім або "Територіальне управління"
            # Якщо назва "Територіальне управління", то це сама в/ч ТУ.
            # Якщо назва порожня, то використовуємо місто.
            display_unit_name = unit_name
            if not display_unit_name or display_unit_name.strip() == "":
                display_unit_name = city # Як запасний варіант, якщо назва порожня

            try:
                unit, created = Unit.objects.get_or_create(
                    code=unit_code,
                    defaults={
                        'territorial_management': current_tm,
                        'name': display_unit_name,
                        'city': city,
                        'distance_from_gu': distance if distance is not None else 0, # обробка null distance
                        # 'note': '' # За замовчуванням порожньо
                    }
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f'Successfully created Unit: {unit.code} - {unit.name}'))
                    created_units_count +=1
                else:
                    # Оновлення, якщо потрібно (наприклад, якщо змінилися дані)
                    updated = False
                    if unit.name != display_unit_name:
                        unit.name = display_unit_name
                        updated = True
                    if unit.city != city:
                        unit.city = city
                        updated = True
                    if unit.distance_from_gu != (distance if distance is not None else 0):
                        unit.distance_from_gu = (distance if distance is not None else 0)
                        updated = True
                    if unit.territorial_management != current_tm:
                        unit.territorial_management = current_tm
                        updated = True
                    
                    if updated:
                        unit.save()
                        self.stdout.write(self.style.WARNING(f'Unit {unit.code} already existed. Updated fields.'))
                        updated_units_count +=1
                    else:
                        self.stdout.write(self.style.WARNING(f'Unit {unit.code} - {unit.name} already exists. No changes made.'))
                        # Якщо не було оновлень, зарахуємо як пропущений, щоб не плутати з реальними пропусками через помилки
                        # skipped_units_count += 1 # Або просто не збільшувати жоден лічильник
                
                # unit_groups залишається порожнім згідно з вимогою

            except django.db.utils.IntegrityError as e:
                self.stdout.write(self.style.ERROR(f'IntegrityError for unit {unit_code}: {e}. This might be due to a non-unique code if get_or_create logic failed or a concurrent operation.'))
                skipped_units_count += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'An error occurred while creating/updating unit {unit_code}: {e}'))
                skipped_units_count += 1


        self.stdout.write(self.style.SUCCESS('------------------------------------'))
        self.stdout.write(self.style.SUCCESS(f'Data population finished.'))
        self.stdout.write(self.style.SUCCESS(f'Territorial Managements processed: {len(territorial_managements_cache)}'))
        self.stdout.write(self.style.SUCCESS(f'Units created: {created_units_count}'))
        self.stdout.write(self.style.SUCCESS(f'Units updated: {updated_units_count}'))
        self.stdout.write(self.style.WARNING(f'Units skipped (already existed or error): {skipped_units_count}'))