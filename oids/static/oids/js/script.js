


document.addEventListener("DOMContentLoaded", function () {
        document.querySelectorAll("form").forEach(form => {
            form.setAttribute("autocomplete", "off");
        });
    });

    // <button class="theme-toggle" onclick="toggleTheme()">Змінити тему</button>
function toggleTheme() {
    document.body.classList.toggle('dark-theme');
  }

// створити фільтр в календарі. початок та кінець 
document.getElementById('id_start_date').addEventListener('change', function() {
  document.getElementById('id_end_date').setAttribute('min', this.value);
});

document.getElementById('id_end_date').addEventListener('change', function() {
  document.getElementById('id_start_date').setAttribute('max', this.value);
});
