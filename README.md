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


<!-- 
 -->
<!-- 
 -->

myApp\Scripts\activate


python manage.py makemigrations
python manage.py migrate
python manage.py runserver
 

python manage.py createsuperuser


 # Видалити старі міграції:
del oids/migrations/0*.py
# (крім __init__.py, його не чіпай!)

# Видалити стару базу (якщо вона неважлива):
del db.sqlite3