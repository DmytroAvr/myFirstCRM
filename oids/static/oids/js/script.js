
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
document.addEventListener("DOMContentLoaded", function () {
  const startDateInput = document.getElementById("id_start_date");
  const endDateInput = document.getElementById("id_end_date");

  if (startDateInput && endDateInput) {
    startDateInput.addEventListener("change", function () {
      endDateInput.setAttribute("min", this.value);
    });

    endDateInput.addEventListener("change", function () {
      startDateInput.setAttribute("max", this.value);
    });
  }
});