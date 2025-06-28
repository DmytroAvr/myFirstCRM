# C:\myFirstCRM\oids\tests\test_views.py

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from ..models import WorkRequest, Unit

class WorkRequestCreateViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='testuser', password='password123')
        cls.unit = Unit.objects.create(name="Тестова частина A0000")
        # Цей reverse тепер 100% правильний
        cls.create_url = reverse('oids:add_work_request')

    def setUp(self):
        self.client = Client()
        self.client.login(username='testuser', password='password123')

    def test_create_view_get_request(self):
        """Тест: чи доступна сторінка створення заявки (GET-запит)."""
        response = self.client.get(self.create_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'oids/forms/add_work_request_form.html')

    def test_create_view_post_request_success(self):
        """Тест: чи створюється заявка при успішному POST-запиті."""
        initial_request_count = WorkRequest.objects.count()
        
        form_data = {
            # --- ОСНОВНА ФОРМА З ПРЕФІКСОМ 'main-' ---
            'main-unit': self.unit.id,
            'main-incoming_number': '124/2024',
            'main-incoming_date': '2024-10-26',
            
            # --- ФОРМСЕТ З ПРЕФІКСОМ 'items-' ---
            'items-TOTAL_FORMS': '1',
            'items-INITIAL_FORMS': '0',
            'items-MIN_NUM_FORMS': '0',
            'items-MAX_NUM_FORMS': '1000',
            'items-0-name': 'Тестовий елемент',
            'items-0-quantity': '2',
            'items-0-id': '', 
            'items-0-request': '',
        }
        
        response = self.client.post(self.create_url, data=form_data)
        
        self.assertEqual(response.status_code, 302, f"Помилка валідації: {response.context['main_form'].errors if response.context else ''} {response.context['formset'].errors if response.context else ''}")
        self.assertEqual(WorkRequest.objects.count(), initial_request_count + 1)
        self.assertTrue(WorkRequest.objects.filter(incoming_number='124/2024').exists())

    def test_create_view_post_request_fail(self):
        """Тест: чи повертається форма з помилками при невалідному POST-запиті."""
        form_data = {
            # Основні дані навмисно пропущені
            # Службові дані для формсету
            'items-TOTAL_FORMS': '1',
            'items-INITIAL_FORMS': '0',
        }
        
        response = self.client.post(self.create_url, data=form_data)
        
        self.assertEqual(response.status_code, 200)
        # --- ПЕРЕВІРЯЄМО ФОРМУ З ПРАВИЛЬНИМ ІМЕНЕМ 'main_form' ---
        self.assertIn('main_form', response.context)
        form = response.context['main_form']
        self.assertTrue(form.errors)
        self.assertIn('incoming_number', form.errors)

    def test_unauthenticated_access(self):
        """Тест: неавтентифікований користувач перенаправляється на сторінку логіну."""
        self.client.logout()
        response = self.client.get(self.create_url)
        login_url = reverse('login')
        self.assertRedirects(response, f'{login_url}?next={self.create_url}')