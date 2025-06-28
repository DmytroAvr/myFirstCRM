# oids/tests/test_forms.py

from django.test import TestCase
from ..forms import WorkRequestForm
from ..models import Unit

class WorkRequestFormTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.unit = Unit.objects.create(name="Тестова частина A0000")

    def test_work_request_form_valid_data(self):
        """Тест: форма валідна з коректними даними."""
        form_data = {
            'unit': self.unit.id,
            # ВИПРАВЛЕНО: використовуємо правильні імена полів
            'incoming_number': '123/2024', 
            'incoming_date': '2024-10-25',
        }
        form = WorkRequestForm(data=form_data)
        
        # Ця перевірка тепер має пройти
        self.assertTrue(form.is_valid(), msg=f"Форма невалідна, помилки: {form.errors.as_json()}")

    def test_work_request_form_no_data(self):
        """Тест: форма невалідна, якщо не передати дані."""
        form = WorkRequestForm(data={})
        
        self.assertFalse(form.is_valid())
        # Перевіримо, що є помилки для 3 обов'язкових полів
        self.assertEqual(len(form.errors), 3) 
        
        # ВИПРАВЛЕНО: шукаємо помилки для правильних полів
        self.assertIn('unit', form.errors)
        self.assertIn('incoming_number', form.errors)
        self.assertIn('incoming_date', form.errors)

    def test_work_request_form_missing_number(self):
        """Тест: форма невалідна, якщо відсутній номер заявки."""
        form_data = {
            'unit': self.unit.id,
            'incoming_date': '2024-10-25',
        }
        form = WorkRequestForm(data=form_data)
        
        self.assertFalse(form.is_valid())
        # ВИПРАВЛЕНО: шукаємо помилку для правильного поля
        self.assertIn('incoming_number', form.errors)