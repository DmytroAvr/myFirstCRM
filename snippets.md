
<!-- alert - "Дані збережено" для id="my-form" -->
<script>
    document.getElementById("my-form").addEventListener("submit", function(e) {
        e.preventDefault();  // зупиняє стандартне відправлення
        const formData = new FormData(this);

        fetch(this.action, {
            method: "POST",
            body: formData,
            headers: {
                'X-CSRFToken': getCookie('csrftoken') // якщо треба
            }
        })
        .then(response => {
            if (response.ok) {
                alert("✅ Дані збережено!");
                location.reload();  // або redirect, якщо треба
            } else {
                alert("⚠️ Помилка при збереженні.");
            }
        });
    });

    // Функція для отримання CSRF-токена
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let cookie of cookies) {
                cookie = cookie.trim();
                if (cookie.startsWith(name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
</script>





<!-- views  -->

from django import forms
from .models import TechnicalTask, Person

class TechnicalTaskForm(forms.ModelForm):
    reviewed_by = forms.ModelChoiceField(queryset=Person.objects.all(), label="Хто ознайомився")

    class Meta:
        model = TechnicalTask
        fields = ['oid', 'input_number', 'input_date', 'reviewed_by', 'review_result', 'note']
        widgets = {
            'input_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['input_number'].initial = "24/33-"

        <!-- виключити щось -->
        # Спочатку створюємо список статусів, які потрібно виключити
        exclude_statuses = [
            OIDStatusChoices.NEW,
            OIDStatusChoices.TERMINATED,
            OIDStatusChoices.CANCELED,
        ]
        
        # Тепер фільтруємо choices для поля status
        self.fields['status'].choices = [
            choice for choice in OIDStatusChoices.choices if choice[0] not in exclude_statuses
        ]
