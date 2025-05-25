let targetSelect = null;

// updateAddOidButtons + openOidAside працюють гарно. оновлює та додає нові кнопки
 function updateAddOidButtons() {
        document.querySelectorAll('.add-oid-button').forEach(button => {
            button.removeEventListener('click', openOidAside);
            button.addEventListener('click', openOidAside);
        });
    }
  function openOidAside(event) {
        const formDiv = event.target.closest('.document-form');
        const unitSelect = document.querySelector('#id_unit');
        const unitId = unitSelect ? unitSelect.value : null;

        if (!unitId) {
            alert("Будь ласка, спочатку оберіть військову частину.");
            return;
        }

        const aside = document.getElementById('oid-aside');
        const overlay = document.getElementById('overlay');
        const unitSpan = document.getElementById('insert_unit');

        unitSpan.textContent = unitSelect.options[unitSelect.selectedIndex].text;

        aside.style.display = 'block';
        overlay.style.display = 'block';
        aside.dataset.targetForm = formDiv.dataset.formIndex; // для подальшої логіки
    }

document.addEventListener('DOMContentLoaded', function () {
    const formset = document.getElementById('formset');
    const addFormBtn = document.getElementById('add-form');
    const totalForms = document.querySelector('#id_form-TOTAL_FORMS');
    // console.log("Formset:", formset, "Add Form Button:", addFormBtn, "Total Forms Input:", totalForms.value);
    
    addFormBtn.addEventListener('click', function () {
      const forms = document.querySelectorAll('.document-form');
      const newForm = forms[0].cloneNode(true);
      const newIndex = forms.length;

      newForm.dataset.formIndex = newIndex;

      newForm.querySelectorAll('input, select, textarea').forEach(el => {
          if (el.type !== 'hidden') el.value = '';
      });

      newForm.querySelectorAll('input, select, textarea, label').forEach(el => {
          if (el.name) el.name = el.name.replace(/form-\d+-/, `form-${newIndex}-`);
          if (el.id) el.id = el.id.replace(/form-\d+-/, `form-${newIndex}-`);
          if (el.htmlFor) el.htmlFor = el.htmlFor.replace(/form-\d+-/, `form-${newIndex}-`);
      });

      formset.appendChild(newForm);
      totalForms.value = newIndex + 1;
      updateDeleteButtons();
      updateAddOidButtons();  // ✅ додай сюди
      attachOidAside();
    });
});

// кнопка видалення форми
    function updateDeleteButtons() {
        document.querySelectorAll('.remove-form').forEach(btn => {
            btn.removeEventListener('click', removeForm);
            btn.addEventListener('click', removeForm);
            btn.classList.add('delete-button');
        });
    }
    function removeForm(event) {
        const formDiv = event.target.closest('.document-form');
        formDiv.remove();
        // Оновити лічильник форм
        const forms = document.querySelectorAll('.document-form');
        let totalForms = 2;

        totalForms.value = forms.length;
        if (forms.length == 1) {
            let delBTN = document.querySelectorAll('.delete-button');
            delBTN[0].style.display = 'none';
        } else {
            delBTN.forEach(btn => btn.style.display = 'block');
        }

        // Перенумерація інпутів
        forms.forEach((form, index) => {
            form.querySelectorAll('input, select, textarea, label').forEach(el => {
                if (el.name) el.name = el.name.replace(/form-\d+-/, `form-${index}-`);
                if (el.id) el.id = el.id.replace(/form-\d+-/, `form-${index}-`);
                if (el.htmlFor) el.htmlFor = el.htmlFor.replace(/form-\d+-/, `form-${index}-`);
            });
        });
    }

// aside для створення OID
  function attachOidAside(unitSelectId = 'id_unit') {
    const unitSelect = document.getElementById(unitSelectId);

  // Відкрити aside. кнопка працює лиши на .add-oid-button якуі були створені на сторінці. Динамічно не оновлюється список кнопок
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

    document.addEventListener('DOMContentLoaded', function () {
        attachOidAside();
        updateDeleteButtons();
    });