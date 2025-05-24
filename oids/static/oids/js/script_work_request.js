document.addEventListener('DOMContentLoaded', function () {
    const formset = document.getElementById('formset');
    const addFormBtn = document.getElementById('add-form');
    const totalForms = document.querySelector('#id_form-TOTAL_FORMS');
    const unitSelect = document.getElementById('id_unit');

    function updateSelect2() {
        document.querySelectorAll('.oid-select').forEach(select => {
            if (!$(select).hasClass('select2-hidden-accessible')) {
                $(select).select2();
            }
        });
    }

    function updateAddOidButtons() {
        document.querySelectorAll('.add-oid-button').forEach(button => {
            button.removeEventListener('click', openOidAside);
            button.addEventListener('click', openOidAside);
        });
    }

    function openOidAside(event) {
        const formDiv = event.target.closest('.document-form');
        const unitId = unitSelect.value;

        if (!unitId) {
            alert("Оберіть військову частину!");
            return;
        }

        const aside = document.getElementById('oid-aside');
        const overlay = document.getElementById('overlay');
        const unitSpan = document.getElementById('insert_unit');

        unitSpan.textContent = unitSelect.options[unitSelect.selectedIndex].text;

        aside.style.display = 'block';
        overlay.style.display = 'block';
        aside.dataset.targetForm = formDiv.dataset.formIndex;
    }

    function updateDeleteButtons() {
        document.querySelectorAll('.remove-form').forEach(btn => {
            btn.removeEventListener('click', removeForm);
            btn.addEventListener('click', removeForm);
        });
    }

    function removeForm(e) {
        e.target.closest('.document-form').remove();
        updateFormIndices();
    }

    function updateFormIndices() {
        const forms = document.querySelectorAll('.document-form');
        forms.forEach((form, index) => {
            form.dataset.formIndex = index;
            form.querySelectorAll('input, select, textarea, label').forEach(el => {
                if (el.name) el.name = el.name.replace(/form-\d+-/, `form-${index}-`);
                if (el.id) el.id = el.id.replace(/form-\d+-/, `form-${index}-`);
                if (el.htmlFor) el.htmlFor = el.htmlFor.replace(/form-\d+-/, `form-${index}-`);
            });
        });
        totalForms.value = forms.length;
    }

    addFormBtn.addEventListener('click', function () {
        const formIndex = document.querySelectorAll('.document-form').length;
        const emptyTemplate = document.getElementById('empty-form-template').innerHTML;
        const newFormHtml = emptyTemplate.replace(/__prefix__/g, formIndex);

        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = newFormHtml;
        const newForm = tempDiv.firstElementChild;

        formset.appendChild(newForm);
        totalForms.value = formIndex + 1;

        updateDeleteButtons();
        updateAddOidButtons();
        updateSelect2();
    });

    // Завантаження OID при виборі unit
    unitSelect.addEventListener('change', function () {
        const unitId = this.value;
        fetch(`/oids/ajax/load-oids/?unit=${unitId}`)
            .then(response => response.json())
            .then(data => {
                document.querySelectorAll('.document-form').forEach((formDiv, index) => {
                    const oidSelect = formDiv.querySelector(`select[name="form-${index}-oid"]`);
                    if (oidSelect) {
                        oidSelect.innerHTML = '<option value="">---------</option>';
                        data.forEach(oid => {
                            const option = document.createElement('option');
                            option.value = oid.id;
                            option.textContent = oid.name;
                            oidSelect.appendChild(option);
                        });
                    }
                });
            });
    });

    updateDeleteButtons();
    updateAddOidButtons();
    updateSelect2();
});
