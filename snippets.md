
<!-- alert - "Дані збережено" для id="my-form" -->
<!-- for js form -->
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






<!--  add message succsess -->
<!-- to html -->

        {% if messages %}
            {% for message in messages %}
                <div class="alert alert-success">{{ message }}</div>
            {% endfor %}
        {% endif %}

<!-- to form -->


         for form in formset:
                if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                    item = form.save(commit=False)
                    item.request = work_request
                    item.save() 
            
            messages.success(request, "Заявка успішно збережена!")




<!-- select2 -->
<script>
    $(document).ready(function() {
        $('select').select2();
    });
</script> 
<script>
    // script for select2 with search
    $(document).ready(function() {
    $('select').select2();
        $('#id_units').on('change', function() {
            const unitIds = $(this).val();
            if (!unitIds.length) return;

            $.ajax({
                url: "{% url 'ajax_load_oids_for_units' %}",
                data: {
                    'units[]': unitIds
                },
                success: function(data) {
                    const $oidSelect = $('#id_oids');
                    $oidSelect.empty();
                    data.forEach(function(oid) {
                        $oidSelect.append($('<option>', {
                            value: oid.id,
                            text: oid.name
                        }));
                    });
                    $oidSelect.trigger('change');
                }
            });
        });
    });
</script>


<!-- autocomplete off -->
<script>
    document.addEventListener("DOMContentLoaded", function () {
        document.querySelectorAll("form").forEach(form => {
            form.setAttribute("autocomplete", "off");
        });
    });
</script>


    input[type="checkbox"][name$="-DELETE"] {
        display: none;
    }
    label[for$="-DELETE"] {
        display: none;
    }   
    .alert-success {
        color: rgb(69, 143, 9);
        text-align: center;
        font-size: 30;
        font-weight: 700;
    }   



{% block extra_css %}
<!-- <link rel="stylesheet" href="{% static 'oids\css\select2_many_to_many.css' %}"> -->
{% endblock %}