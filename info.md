🔗 1. models.ForeignKey — Many-to-One
Багато об'єктів однієї моделі можуть посилатись на один об'єкт іншої моделі.

📌 Приклад:
python
Копіювати
Редагувати
class Author(models.Model):
    name = models.CharField(max_length=100)

class Book(models.Model):
    title = models.CharField(max_length=100)
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
Один автор → багато книг.

У таблиці Book буде поле author_id, яке є зовнішнім ключем до таблиці Author.

🔗 2. models.OneToOneField — One-to-One
Один об'єкт пов’язаний рівно з одним іншим об'єктом.

📌 Приклад:
python
Копіювати
Редагувати
class User(models.Model):
    username = models.CharField(max_length=100)

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField()
Один User → один Profile.

У БД Profile.user_id є унікальним зовнішнім ключем на User.

🔗 3. models.ManyToManyField — Many-to-Many
Кожен об’єкт з однієї моделі може бути пов’язаний з багатьма об’єктами іншої моделі, і навпаки.

📌 Приклад:
python
Копіювати
Редагувати
class Student(models.Model):
    name = models.CharField(max_length=100)

class Course(models.Model):
    title = models.CharField(max_length=100)
    students = models.ManyToManyField(Student)
Один студент може відвідувати багато курсів.

Один курс може мати багато студентів.

Django створює проміжну таблицю автоматично, наприклад: course_students.

🔧 Додаткові параметри для всіх типів зв’язків:
Параметр	Опис
on_delete	Що робити при видаленні пов’язаного об’єкта (CASCADE, SET_NULL, PROTECT, SET_DEFAULT, DO_NOTHING)
related_name	Ім’я для зворотного зв’язку з іншої моделі
null=True	Дозволяє порожнє значення у БД
blank=True	Дозволяє залишити поле порожнім у формах
unique=True	Поле повинно бути унікальним (актуально для One-to-One або ForeignKey в особливих випадках)




Важливо щодо URL в JavaScript:
Пряме використання {% url 'oids:ajax_load_oids_categorized' %} у зовнішньому .js файлі не спрацює, оскільки Django обробляє ці теги тільки в HTML-шаблонах.
Рішення:

Передати URL через data- атрибут на HTML-елементі:
HTML

<select name="unit" id="id_unit_filter" class="select2" data-ajax-url-categorized="{% url 'oids:ajax_load_oids_categorized' %}" style="width: 100%;">
І в JS зчитувати: url: $(this).data('ajax-url-categorized') або config.url = $sourceElement.data('ajax-url-categorized');.