https://packaging.python.org/en/latest/tutorials/installing-packages/



py --version

py -m pip --version
py -m ensurepip --default-pip





py -m venv <DIR>
<DIR>\Scripts\activate


virtualenv <DIR>
<DIR>\Scripts\activate


In both of the above cases, Windows users should not use the source command, but should rather run the activate script directly from the command shell like so:

<DIR>\Scripts\activate

myApp\Scripts\activate


///////////

https://www.w3schools.com/django/django_install_django.php


# install Django
python -m pip install Django
pip install django-multiselectfield
pip install django-tomselect

<!-- 
 -->
<!-- 
 -->

myApp\Scripts\activate

python manage.py makemigrations
python manage.py migrate
python manage.py runserver
 

python manage.py createsuperuser

python manage.py main_unit_data  (створити в/ч з каталогу C:\myFirstCRM\oids\management\commands\main_unit_data.py)


 # Видалити старі міграції:
del oids/migrations/0*.py
# (крім __init__.py, його не чіпай!)

# Видалити стару базу (якщо вона неважлива):
del db.sqlite3

{% extends 'base.html' %}

2. запропонуй атрибути які можуть допомогти узагальнювати інформацію. в яких моделях є потреба в їх доданні. спитай мене про кожній моделі, яка інформація та звязок може бути корисним. на підставі запитань запропонуй нову будову атрибутів та звязків


<!-- Тепер важливий момент. Описую звязок документів який потрібно реалізувати.

цикл може починатись з технічного завдання або заявки.

Отримання ТЗ та МЗ (на погодження) (обліковуємо, прив'язуємо до створеного або створюємо ОІД. маємо облікувати результат ознайомлення з ТЗ. 
атрибути: Вхідний номер/дата, Хто читав, результат (на доопрацювання, погоджено, чекаємо папір)



Отримуємо заявку на створення ОІД (одна заявка на вч, в ній може бути кілька ОІД статус заявки: "виконано" лише коли виконані всі ОІД з заявки мають статус "виконано" або "скасовано") (заявки реалізовано в myFirstCRM\oids\templates\oids\document\_request.html. але потрібно перевірити зв'язки. Важливо зберігати зв'язок заявки з: військова частина, ОІД (статус заявки для ОІД яких стосується), відрядження, опрацювання документів, надсилання документів (myFirstCRM\oids\templates\trip\_result\_form.html, myFirstCRM\oids\templates\attestation\_registration\_form.html)
myFirstCRM\oids\templates\trip\_result\_form.html,  - є завершенням дії частини щодо визначених в заявці ОІД. Після відправки результату до частини - ОІД з заявка отримує статус "Виконано". Також потрібно мати можливість змінити вручну статус окремо ОІД в заявці. Це має бути через окрему форму та містити примітку, для вказання причини скасування



опрацювання відрядження. Термін опрацювання - Атестація 15 днів ІК 10 днів. Відлік починається  з дня після завершення відрядження.

Опрацьовується пакет документів з class Document(models.Model).

якщо це була атестація - лист на ДССЗЗІ про реєстрація Акту Атестація myFirstCRM\oids\templates\attestation\_registration\_form.html
після отримання відповіді вписати реєстраційний номер та опрацьовуємо myFirstCRM\oids\templates\trip\_result\_form.html.
якщо ІК - одразу myFirstCRM\oids\templates\trip\_result\_form.html  -->




http://127.0.0.1:8000/oids/technical_tasks/create/
виправити оновлення форми після створення ОІД

http://127.0.0.1:8000/oids/attestation/new/
додати можливість додавати ОІД. Якщо реєструють ОІД створений самотужки