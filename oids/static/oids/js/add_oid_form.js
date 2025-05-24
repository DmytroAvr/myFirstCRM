// // js для один ОІД з requestHeaderForm як фільтр в усі requestItemFormSet
    // document.addEventListener('DOMContentLoaded', function () { 
    //     const unitSelect = document.querySelector('#id_unit');

    //     unitSelect.addEventListener('change', function () {
    //         const unitId = this.value;

    //         fetch(`/oids/ajax/load-oids/?unit=${unitId}`)
    //             .then(response => response.json())
    //             .then(data => {
    //                 // Знайти всі форми
    //                 document.querySelectorAll('.document-form').forEach((formDiv, index) => {
    //                     const oidSelect = formDiv.querySelector(`#id_form-${index}-oid`);
    //                     if (oidSelect) {
    //                         oidSelect.innerHTML = ''; // Очистити

    //                         // Додати порожній варіант
    //                         const emptyOption = document.createElement('option');
    //                         emptyOption.value = '';
    //                         emptyOption.textContent = '---------';
    //                         oidSelect.appendChild(emptyOption);

    //                         // Тепер додати справжні OID
    //                         data.forEach(oid => {
    //                             const option = document.createElement('option');
    //                             option.value = oid.id;
    //                             option.textContent = oid.name;
    //                             oidSelect.appendChild(option);
    //                         });
    //                     }
    //                 });
    //             });
    //     });
    // });
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

   
    // button to add one more form !!!! requestItemFormSet
    document.addEventListener('DOMContentLoaded', function () {
        const formset = document.getElementById('formset');
        const addFormBtn = document.getElementById('add-form');
        const totalForms = document.querySelector('#id_form-TOTAL_FORMS');
        
        
        function updateDeleteButtons() {
            document.querySelectorAll('.remove-form').forEach(btn => {
                btn.removeEventListener('click', removeForm);
                btn.addEventListener('click', removeForm);
            });
        }

        function removeForm(event) {
            const formDiv = event.target.closest('.document-form');
            formDiv.remove();
            // Оновити лічильник форм
            const forms = document.querySelectorAll('.document-form');
            totalForms.value = forms.length;

            // Перенумерація інпутів
            forms.forEach((form, index) => {
                form.querySelectorAll('input, select, textarea, label').forEach(el => {
                    if (el.name) el.name = el.name.replace(/form-\d+-/, `form-${index}-`);
                    if (el.id) el.id = el.id.replace(/form-\d+-/, `form-${index}-`);
                    if (el.htmlFor) el.htmlFor = el.htmlFor.replace(/form-\d+-/, `form-${index}-`);
                });
            });
        }

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

        attachOidAside();
        updateDeleteButtons();
    });