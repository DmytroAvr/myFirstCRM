document.addEventListener("DOMContentLoaded", function () {
        document.querySelectorAll("form").forEach(form => {
            form.setAttribute("autocomplete", "off");
        });
    });




    // <button class="theme-toggle" onclick="toggleTheme()">Змінити тему</button>
function toggleTheme() {
    document.body.classList.toggle('dark-theme');
  }