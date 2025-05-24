let targetSelect = null;

function attachOidAside(unitSelectId = 'id_unit') {
  const unitSelect = document.getElementById(unitSelectId);

  // Відкрити aside
  document.querySelectorAll('.add-oid-button').forEach(button => {
    if (!button.dataset.bound) {
      button.addEventListener('click', function (e) {
        const unitId = unitSelect.value;
        if (!unitId) {
          alert("⚠️ Спершу оберіть військову частину у формі зверху.");
          return;
        }

        const formDiv = e.target.closest('.document-form') || e.target.closest('form');
        targetSelect = formDiv.querySelector('select[name$="-oid"], select[name="oid"]');

        document.getElementById('insert_unit').innerText = unitSelect.options[unitSelect.selectedIndex].text;
        document.getElementById('oid-aside').style.display = "block";
        document.getElementById('overlay').style.display = "block";
      });

      button.dataset.bound = 'true';
    }
  });

  document.getElementById('oid-aside-close').addEventListener('click', function () {
    document.getElementById('oid-aside').style.display = "none";
    document.getElementById('overlay').style.display = "none";
  });

  document.getElementById('oid-create-form').addEventListener('submit', function (e) {
    e.preventDefault();

    const formData = new FormData(this);
    const unitId = unitSelect.value;
    formData.append('unit_id', unitId);

    fetch('/oids/ajax/create/', {
      method: 'POST',
      body: formData,
      headers: {
        'X-CSRFToken': formData.get('csrfmiddlewaretoken')
      }
    })
      .then(response => response.json())
      .then(data => {
        if (data.success) {
          alert("✅ ОІД створено");
          this.reset();
          document.getElementById('oid-aside').style.display = "none";
          document.getElementById('overlay').style.display = "none";

          if (targetSelect) {
            const newOption = new Option(data.oid.name, data.oid.id);
            newOption.selected = true;
            targetSelect.appendChild(newOption);
          }
        } else {
          alert("❌ Помилка:\n" + JSON.stringify(data.errors));
        }
      })
      .catch(err => {
        console.error("❌ Сервер не відповів:", err);
        alert("⚠️ Помилка зв’язку з сервером");
      });
  });
}
