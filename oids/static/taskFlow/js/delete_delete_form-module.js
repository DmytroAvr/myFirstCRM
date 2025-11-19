
// ====================================================================================================
// ====================================================================================================
// ====================================================================================================
// ====================================================================================================
function DjangoFormsetManager(options) {
    const container = document.querySelector(options.containerSelector);
    const addButton = document.querySelector(options.addButtonSelector);
    const emptyFormTemplateHtml = document.getElementById(options.emptyFormTemplateId)?.innerHTML;
    const formsetPrefix = options.formsetPrefix;
    const formClass = options.formClass; // Наприклад, '.document-item-form'
    const removeButtonClass = options.removeButtonClass; // Наприклад, '.remove-document-item-button'
    
    // Елементи управління формсетом Django
    const totalFormsInput = document.getElementById(`id_${formsetPrefix}-TOTAL_FORMS`);
    const minFormsInput = document.getElementById(`id_${formsetPrefix}-MIN_NUM_FORMS`);
    const maxFormsInput = document.getElementById(`id_${formsetPrefix}-MAX_NUM_FORMS`);
    // const canDeleteInput = document.getElementById(`id_${formsetPrefix}-CAN_DELETE`); // Django не створює це поле

    const minFormsCount = minFormsInput ? parseInt(minFormsInput.value) : 0;
    const maxFormsCount = maxFormsInput ? parseInt(maxFormsInput.value) : 1000; // Типове значення Django
    // const canDelete = options.canDelete || (canDeleteInput && canDeleteInput.value === 'True'); // Отримуємо з опцій або атрибута
    const canDelete = options.canDelete || false; // Краще передавати явно

    if (!container || !addButton || !emptyFormTemplateHtml || !totalFormsInput) {
        console.warn(`FORMSET_MANAGER [${formsetPrefix}]: Required elements for formset management not found. Manager not fully initialized.`);
        return null; // Або кидати помилку
    }
    console.log(`FORMSET_MANAGER [${formsetPrefix}]: Initializing. Min: ${minFormsCount}, Max: ${maxFormsCount}, CanDelete: ${canDelete}`);

    function updateFormAttributes(formElement, index) {
        console.log(`FORMSET_MANAGER [${formsetPrefix}]: Updating attributes for form at index ${index}`);
        formElement.querySelectorAll('input, select, textarea, label').forEach(el => {
            ['name', 'id', 'for'].forEach(attr => {
                const currentAttrVal = el.getAttribute(attr);
                if (currentAttrVal && currentAttrVal.includes('__prefix__')) {
                    el.setAttribute(attr, currentAttrVal.replace(/__prefix__/g, index));
                } else if (currentAttrVal && currentAttrVal.startsWith(formsetPrefix + '-')) {
                    // Для вже існуючих форм, якщо потрібна пере-індексація (складніше)
                    // Зазвичай Django сам обробляє індекси існуючих форм, нам потрібно лише __prefix__ для нових
                }
            });
        });
    }

    function addForm() {
        console.log(`FORMSET_MANAGER [${formsetPrefix}]: Add button clicked.`);
        const currentForms = container.querySelectorAll(formClass);
        let formIdx = parseInt(totalFormsInput.value); // Поточна кількість форм для наступного індексу

        if (formIdx >= maxFormsCount) {
            alert(`Досягнуто максимальну кількість елементів (${maxFormsCount}) для "${formsetPrefix}".`);
            return;
        }

        const newFormHtml = emptyFormTemplateHtml.replace(/__prefix__/g, formIdx);
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = newFormHtml;
        const newFormElement = tempDiv.firstElementChild; // Має бути обгортка форми, наприклад <div class="document-item-form">...</div>
        
        if (!newFormElement) {
            console.error(`FORMSET_MANAGER [${formsetPrefix}]: Empty form template did not produce a valid element.`);
            return;
        }
        // Переконаємося, що newFormElement має правильний клас
        if (!newFormElement.classList.contains(formClass.substring(1))) { // substring(1) щоб прибрати точку з класу
            console.warn(`FORMSET_MANAGER [${formsetPrefix}]: New form element does not have class '${formClass}'. Adding it. OuterHTML:`, newFormElement.outerHTML);
            // newFormElement.classList.add(formClass.substring(1)); // Може бути непотрібно, якщо шаблон правильний
        }


        container.appendChild(newFormElement);
        totalFormsInput.value = formIdx + 1;
        console.log(`FORMSET_MANAGER [${formsetPrefix}]: Form ${formIdx} added. New TOTAL_FORMS: ${totalFormsInput.value}`);

        // Виклик колбеку для ініціалізації полів у новій формі
        if (typeof options.initializeNewFormCallback === 'function') {
            console.log(`FORMSET_MANAGER [${formsetPrefix}]: Calling initializeNewFormCallback for form ${formIdx}`);
            options.initializeNewFormCallback(newFormElement, formIdx);
        }
        
        updateDeleteButtonsVisibility();
    }

    function removeForm(formDivToRemove) {
        console.log(`FORMSET_MANAGER [${formsetPrefix}]: removeForm called for:`, formDivToRemove);
        const deleteCheckbox = formDivToRemove.querySelector(`input[type="checkbox"][name^="${formsetPrefix}-"][name$="-DELETE"]`);

        if (deleteCheckbox && formDivToRemove.dataset.isSaved === 'true') { // Або інший спосіб визначити, чи форма збережена
            console.log(`FORMSET_MANAGER [${formsetPrefix}]: Marking existing form for deletion.`);
            deleteCheckbox.checked = true;
            formDivToRemove.style.display = 'none'; 
        } else {
            console.log(`FORMSET_MANAGER [${formsetPrefix}]: Removing new form from DOM.`);
            // Колбек перед видаленням, наприклад, для destroy TomSelect
            if (typeof options.beforeRemoveFormCallback === 'function') {
                options.beforeRemoveFormCallback(formDivToRemove);
            }
            formDivToRemove.remove();
        }
        
        // Оновлення TOTAL_FORMS та індексів (це складна частина, особливо якщо форми не видаляються послідовно)
        // Django зазвичай сам обробляє індексацію при POST, якщо TOTAL_FORMS правильний.
        // Для форм, видалених з DOM, TOTAL_FORMS має зменшитись.
        // Для форм, позначених DELETE, TOTAL_FORMS не змінюється, але Django їх не обробляє як нові.
        let visibleFormCount = 0;
        container.querySelectorAll(formClass).forEach((form, index) => {
            const currentDeleteInput = form.querySelector(`input[type="checkbox"][name^="${formsetPrefix}-"][name$="-DELETE"]`);
            if (!currentDeleteInput || !currentDeleteInput.checked) { // Тільки видимі/активні
                // Можливо, потрібно пере-індексувати тут, якщо це критично для валідації на клієнті
                // Але Django має впоратися з пропусками в індексах при POST
                visibleFormCount++;
            }
        });
        // Якщо ми видаляємо з DOM, то totalForms має бути кількістю тих, що відправляються.
        // Якщо тільки позначаємо, то totalForms має бути початковою кількістю + додані - ті, що були повністю видалені (не просто позначені)
        // Поки що, для простоти, припустимо, що Django сам розбереться з індексами,
        // якщо TOTAL_FORMS відображає загальну кількість форм (включаючи ті, що позначені DELETE).
        // Тому totalFormsInput.value оновлюємо лише при фізичному додаванні/видаленні нових форм.
        if (!deleteCheckbox) { // Якщо це була нова форма, яку ми фізично видалили
             totalFormsInput.value = parseInt(totalFormsInput.value) - 1;
        }
        console.log(`FORMSET_MANAGER [${formsetPrefix}]: TOTAL_FORMS is now: ${totalFormsInput.value}`);

        updateDeleteButtonsVisibility();
    }

    function updateDeleteButtonsVisibility() {
        const forms = container.querySelectorAll(formClass);
        let visibleFormsCount = 0;
        forms.forEach(form => {
            const delCheckbox = form.querySelector(`input[type="checkbox"][name^="${formsetPrefix}-"][name$="-DELETE"]`);
            if (!delCheckbox || !delCheckbox.checked) {
                visibleFormsCount++;
            }
        });

        console.log(`FORMSET_MANAGER [${formsetPrefix}]: Updating delete buttons. Visible forms: ${visibleFormsCount}, Min forms: ${minFormsCount}`);
        forms.forEach((form) => {
            const deleteButton = form.querySelector(removeButtonClass);
            if (deleteButton) {
                const delCheckbox = form.querySelector(`input[type="checkbox"][name^="${formsetPrefix}-"][name$="-DELETE"]`);
                if (delCheckbox && delCheckbox.checked) {
                    deleteButton.style.display = 'none';
                } else {
                    deleteButton.style.display = (visibleFormsCount > minFormsCount) ? 'inline-block' : 'none';
                }
            }
        });
    }

    function init() {
        console.log(`FORMSET_MANAGER [${formsetPrefix}]: Initializing event listeners.`);
        addButton.addEventListener('click', addForm);
        container.addEventListener('click', function(event) {
            const targetButton = event.target.closest(removeButtonClass);
            if (targetButton) {
                removeForm(targetButton.closest(formClass));
            }
        });

        // Ініціалізація для вже існуючих форм
        container.querySelectorAll(formClass).forEach((formElement, index) => {
            // Маркуємо існуючі форми, якщо вони мають ID (для логіки видалення)
            if (formElement.querySelector(`input[name^="${formsetPrefix}-"][name$="-id"][value]`)) {
                formElement.dataset.isSaved = 'true';
            }
            // Колбек для ініціалізації полів в існуючих формах (наприклад, TomSelect)
            if (typeof options.initializeNewFormCallback === 'function') {
                 options.initializeNewFormCallback(formElement, index);
            }
            // Додаємо кнопку видалення до існуючих форм, якщо її немає в шаблоні, а can_delete=true
            // Це складніше, бо Django зазвичай рендерить поле DELETE.
            // Краще, щоб кнопка видалення була в шаблоні, а JS керував її видимістю.
            // Або options.initializeNewFormCallback може додати її.
        });
        updateDeleteButtonsVisibility();
    }
    
    // Повертаємо тільки метод init, якщо менеджер повністю самодостатній
    // або інші методи, якщо вони потрібні ззовні
    return { init }; 
}

// ====================================================================================================
// ====================================================================================================
// --- Використання у DOMContentLoaded ---
document.addEventListener("DOMContentLoaded", function () {
    console.log("Global JS: DOMContentLoaded - Initializing page specific formsets.");

    // --- Для сторінки "Додати опрацювання документів" (DocumentItemFormSet) ---
    const docItemFormsetContainer = document.getElementById('document-items-formset-container');
    if (docItemFormsetContainer) {
        console.log("Global JS: Found DocumentItemFormSet container. Initializing manager.");
        DjangoFormsetManager({
            containerSelector: '#document-items-formset-container',
            addButtonSelector: '#add-document-item-button',
            emptyFormTemplateId: 'document-item-empty-form-template',
            formsetPrefix: '{{ formset.prefix }}', // Передаємо префікс з Django контексту
            formClass: '.document-item-form',
            removeButtonClass: '.remove-document-item-button', // Клас для кнопки "Видалити"
            canDelete: "{{ formset.can_delete|yesno:'true,false' }}" === 'true',
            initializeNewFormCallback: function(newFormElement, formIndex) {
                console.log(`DOC_FORMSET_CALLBACK: Initializing fields for new document form ${formIndex}`);
                // Ініціалізація TomSelect для поля document_type у новій формі
                const docTypeSelect = newFormElement.querySelector('select[name$="-document_type"]');
                if (docTypeSelect && typeof TomSelect !== 'undefined') {
                    // Тут ви можете передати опції, які залежать від головної форми,
                    // наприклад, з MainFormManager.getCurrentOidType() та getCurrentWorkType()
                    // Для простоти, поки що використовуємо базову конфігурацію
                    const config = getTomSelectConfig( // getTomSelectConfig має бути доступна глобально або передана
                        docTypeSelect.id || `${formsetPrefix}-${formIndex}-document_type`, // Генеруємо ID, якщо його немає
                        'Оберіть тип документа', 
                        false, // isDisabled
                        [],    // initialOptions (мають завантажуватися динамічно або бути в empty_form)
                        true,  // allowClear
                        [],    // plugins
                        false  // isMulti
                    );
                    // Якщо DocumentItemForm.document_type має queryset=all(), TomSelect їх підхопить.
                    // Якщо потрібно динамічно, то тут буде логіка оновлення.
                    // Зараз стоїть заглушка, тому options будуть ті, що в empty_form.
                    const instance = new TomSelect(docTypeSelect, config);
                    docTypeSelect.tomselectInstance = instance;
                     console.log(`DOC_FORMSET_CALLBACK: TomSelect for DocumentType initialized for ${docTypeSelect.id || 'new_doc_type_select'}`);
                     // Оновлення на основі головної форми (заглушка)
                     DocumentItemFormsetManager.updateAllDocTypes( // Потрібно, щоб ця функція була доступна
                         MainFormManager.getCurrentOidId(), 
                         MainFormManager.getCurrentOidType(),
                         MainFormManager.getCurrentWorkType()
                     ); 
                }
                // Додати тут ініціалізацію інших полів для нової форми, якщо потрібно
            },
            beforeRemoveFormCallback: function(formToRemove) {
                // Знищення TomSelect перед видаленням форми
                const docTypeSelect = formToRemove.querySelector('select[name$="-document_type"]');
                if (docTypeSelect && docTypeSelect.tomselectInstance) {
                    docTypeSelect.tomselectInstance.destroy();
                }
            }
        }).init();
    }

    // --- Для сторінки "Запланувати відрядження" (якщо там теж є формсет) ---
    // Приклад:
    // const tripItemsFormsetContainer = document.getElementById('trip-items-formset-container');
    // if (tripItemsFormsetContainer) {
    //     DjangoFormsetManager({
    //         containerSelector: '#trip-items-formset-container',
    //         // ... інші параметри ...
    //         formsetPrefix: '{{ trip_item_formset.prefix }}', 
    //         initializeNewFormCallback: function(newFormElement, formIndex) {
    //             // Специфічна ініціалізація для полів у формсеті відряджень
    //         }
    //     }).init();
    // }
    
    // Ініціалізація MainFormManager для сторінки "Додати опрацювання документів"
    // (переконайтесь, що відповідні ID елементів є на сторінці)
    if (document.getElementById('id_proc_form_unit')) { // Перевірка, чи ми на правильній сторінці
        MainFormManager.init();
    }

});
// ====================================================================================================
// ====================================================================================================
// ====================================================================================================
// ====================================================================================================
// ====================================================================================================












































// УВАГА: Цей DjangoFormsetManager - це загальна основа. 
// Його, ймовірно, краще винести у ваш main.js або окремий utility.js файл.
// Тут він для повноти прикладу.
function DjangoFormsetManager(options) {
    const container = document.querySelector(options.containerSelector);
    const addButton = document.querySelector(options.addButtonSelector);
    const emptyFormTemplateHtml = document.getElementById(options.emptyFormTemplateId)?.innerHTML;
    const formsetPrefix = options.formsetPrefix;
    const formClass = options.formClass.startsWith('.') ? options.formClass : '.' + options.formClass; // Ensure class selector
    const removeButtonClass = options.removeButtonClass.startsWith('.') ? options.removeButtonClass : '.' + options.removeButtonClass;

    const totalFormsInput = document.getElementById(`id_${formsetPrefix}-TOTAL_FORMS`);
    const minFormsInput = document.getElementById(`id_${formsetPrefix}-MIN_NUM_FORMS`);
    const maxFormsInput = document.getElementById(`id_${formsetPrefix}-MAX_NUM_FORMS`);
    
    const minFormsCount = minFormsInput ? parseInt(minFormsInput.value, 10) : 0;
    const maxFormsCount = maxFormsInput ? parseInt(maxFormsInput.value, 10) : 1000; // Default Django max
    const canDelete = options.canDelete || false; // Отримуємо з опцій

    let formCounter = 0; // Для підрахунку форм, що додаються/існують

    if (!container || !addButton || !emptyFormTemplateHtml || !totalFormsInput) {
        console.warn(`FORMSET_MGR [${formsetPrefix}]: Required elements not found. Init aborted. Need:`, 
            {container, addButton, emptyFormTemplateHtml, totalFormsInput});
        return { init: () => console.error(`FormsetManager for ${formsetPrefix} not properly initialized.`) };
    }
    console.log(`FORMSET_MGR [${formsetPrefix}]: Initializing. Prefix: ${formsetPrefix}, Min: ${minFormsCount}, Max: ${maxFormsCount}, CanDelete: ${canDelete}`);

    function updateFormAttributes(formElement, index) {
        // Ця функція оновлює __prefix__ на актуальний індекс
        // Django empty_form використовує __prefix__, тому це важливо
        console.log(`FORMSET_MGR [${formsetPrefix}]: Updating attrs for new form, index ${index}`);
        formElement.innerHTML = formElement.innerHTML.replace(/__prefix__/g, index);
        // Для вже відрендерених форм Django індекси зазвичай правильні,
        // ця функція більше для нових форм з empty_form.
    }

    function addForm() {
        console.log(`FORMSET_MGR [${formsetPrefix}]: Add button clicked.`);
        // Поточна кількість форм, які будуть відправлені (не видалені з DOM і не позначені DELETE)
        // Або просто беремо значення з TOTAL_FORMS як наступний індекс
        let currentNumberOfForms = parseInt(totalFormsInput.value, 10);

        if (currentNumberOfForms >= maxFormsCount) {
            alert(`Досягнуто максимальну кількість елементів (${maxFormsCount}).`);
            return;
        }

        const newFormHtml = emptyFormTemplateHtml.replace(/__prefix__/g, currentNumberOfForms);
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = newFormHtml;
        const newFormElement = tempDiv.firstElementChild;

        if (!newFormElement) {
            console.error(`FORMSET_MGR [${formsetPrefix}]: Empty form template did not produce valid element.`);
            return;
        }
        // Переконайтеся, що новий елемент має правильний клас
        if (!newFormElement.classList.contains(formClass.substring(1))) {
            newFormElement.classList.add(formClass.substring(1));
        }
        
        container.appendChild(newFormElement);
        totalFormsInput.value = currentNumberOfForms + 1;
        console.log(`FORMSET_MGR [${formsetPrefix}]: Form ${currentNumberOfForms} added. New TOTAL_FORMS: ${totalFormsInput.value}`);

        if (typeof options.initializeNewFormCallback === 'function') {
            options.initializeNewFormCallback(newFormElement, currentNumberOfForms);
        }
        updateDeleteButtonsVisibility();
    }

    function removeForm(formDivToRemove) {
        console.log(`FORMSET_MGR [${formsetPrefix}]: removeForm called for:`, formDivToRemove);
        const deleteCheckbox = formDivToRemove.querySelector(`input[type="checkbox"][name$="-DELETE"]`);

        if (typeof options.beforeRemoveFormCallback === 'function') {
            options.beforeRemoveFormCallback(formDivToRemove);
        }

        if (deleteCheckbox) { // Для форм, що вже існують (мають ID і поле DELETE)
            console.log(`FORMSET_MGR [${formsetPrefix}]: Marking existing form for deletion.`);
            deleteCheckbox.checked = true;
            formDivToRemove.style.display = 'none'; 
            // TOTAL_FORMS не змінюємо, Django це обробить
        } else { // Для нових форм, які ще не збережені
            console.log(`FORMSET_MGR [${formsetPrefix}]: Removing new form from DOM.`);
            formDivToRemove.remove();
            // Оновлюємо TOTAL_FORMS, оскільки форма фізично видалена
            // Потрібно перерахувати форми, які не позначені на видалення
            let liveFormsCount = 0;
            container.querySelectorAll(formClass).forEach(form => {
                const cb = form.querySelector(`input[type="checkbox"][name$="-DELETE"]`);
                if (!cb || !cb.checked) {
                    liveFormsCount++;
                }
            });
            // Це може бути складним, якщо форми видаляються не по порядку.
            // Найпростіше - довірити Django індексацію, а TOTAL_FORMS має бути = початкові + додані - повністю_видалені_нові.
            // Оскільки ми щойно видалили нову, зменшуємо на 1.
            totalFormsInput.value = parseInt(totalFormsInput.value, 10) -1; 
            console.log(`FORMSET_MGR [${formsetPrefix}]: TOTAL_FORMS after new form DOM removal: ${totalFormsInput.value}`);
        }
        updateDeleteButtonsVisibility();
    }

    function updateDeleteButtonsVisibility() {
        const forms = container.querySelectorAll(formClass);
        let visibleFormsCount = 0;
        forms.forEach(form => {
            const delCheckbox = form.querySelector(`input[type="checkbox"][name$="-DELETE"]`);
            if (!delCheckbox || !delCheckbox.checked) {
                visibleFormsCount++;
            }
        });

        console.log(`FORMSET_MGR [${formsetPrefix}]: Updating delete buttons. Visible forms: ${visibleFormsCount}, Min forms: ${minFormsCount}`);
        forms.forEach((form, index) => {
            let deleteButton = form.querySelector(removeButtonClass);
            const delCheckbox = form.querySelector(`input[type="checkbox"][name$="-DELETE"]`);

            if (!deleteButton && (!delCheckbox || !delCheckbox.checked) && canDelete ) { // Додаємо кнопку, якщо її немає і можна видаляти
                 const controlsDiv = form.querySelector('.item-controls'); // Контейнер з HTML
                 if (controlsDiv) {
                    deleteButton = document.createElement('button');
                    deleteButton.type = 'button';
                    deleteButton.classList.add('btn', 'btn-danger', 'btn-sm', removeButtonClass.substring(1));
                    deleteButton.innerHTML = '<i class="fas fa-trash"></i>'; deleteButton.title = "Видалити";
                    controlsDiv.appendChild(deleteButton);
                 }
            }

            if (deleteButton) {
                if (delCheckbox && delCheckbox.checked) { // Якщо форма позначена на видалення
                    deleteButton.style.display = 'none'; 
                } else {
                    deleteButton.style.display = (visibleFormsCount > minFormsCount) ? 'inline-block' : 'none';
                }
            }
        });
    }
    
    function initManager() {
        console.log(`FORMSET_MGR [${formsetPrefix}]: Initializing event listeners and existing forms.`);
        addButton.addEventListener('click', addForm);
        container.addEventListener('click', function(event) {
            const targetButton = event.target.closest(removeButtonClass);
            if (targetButton) {
                removeForm(targetButton.closest(formClass));
            }
        });

        container.querySelectorAll(formClass).forEach((formElement, index) => {
            if (formElement.querySelector(`input[name$="-id"][value]`)) {
                formElement.dataset.isSaved = 'true';
            }
            if (typeof options.initializeNewFormCallback === 'function') {
                 options.initializeNewFormCallback(formElement, index); // Ініціалізація для існуючих теж
            }
        });
        updateDeleteButtonsVisibility();
        console.log(`FORMSET_MGR [${formsetPrefix}]: Initialization complete.`);
    }
    
    return { init: initManager }; 
}


// --- КОД СПЕЦИФІЧНИЙ ДЛЯ СТОРІНКИ AddDocumentProcessing ---
document.addEventListener('DOMContentLoaded', function() {
    console.log("AddDocProc JS: DOMContentLoaded.");

    // ... (визначення елементів MainForm, AJAX URL, getTomSelectConfig, як було) ...
    const unitSelectElement = document.getElementById('id_proc_form_unit');
    const oidSelectElement = document.getElementById('id_proc_form_oid');
    const wriSelectElement = document.getElementById('id_proc_form_work_request_item');
    const authorSelectElement = document.getElementById('id_proc_form_author');
    
    const oidsForUnitAjaxUrl = window.AJAX_LOAD_OIDS_FOR_UNIT_URL || "{% url 'oids:ajax_load_oids_for_unit' %}";
    const wriForOidAjaxUrl = window.AJAX_LOAD_WORK_REQUEST_ITEMS_FOR_OID_URL || "{% url 'oids:ajax_load_work_request_items_for_oid' %}";
    // const docTypesAjaxUrl = ...

    let initialOidIdFromDjango = "{{ main_form.initial.oid.id|default:''|escapejs }}";
    let initialWRIIdFromDjango = "{{ main_form.initial.work_request_item.id|default:''|escapejs }}";
    let initialOidTypeFromDjango = null; 
    // if (main_form.initial.oid && main_form.initial.oid.oid_type )
    //     initialOidTypeFromDjango = "{{ main_form.initial.oid.oid_type|escapejs }}";
   

    if (typeof TomSelect === 'undefined') { /* ... */ return; }

    // --- Керування Головною Формою ---
    const MainFormManager = (function() {
        // ... (весь код MainFormManager.init, handleUnitChange, handleOidChange, handleWriChange, 
        //      getOidInstance, getWriInstance, getCurrentOidId, getCurrentOidType, getCurrentWorkType, ЯК БУВ У ПОПЕРЕДНЬОМУ ПОВІДОМЛЕННІ) ...
        // Важливо: ця частина має бути тут. Я її скоротив для стислості відповіді.
        // Переконайтесь, що методи getCurrentOidId, getCurrentOidType, getCurrentWorkType реалізовані.
        // Наприклад:
        let tsUnit, tsOid, tsWri, tsAuthor;
        let currentOidId = null; let currentOidType = null; let currentSelectedWorkTypeFromWRI = null;
        function init() { /* ... як раніше ... */ 
             if (unitSelectElement) {
                let htmlUnitOpts = []; Array.from(unitSelectElement.options).forEach(opt => {if (opt.value) htmlUnitOpts.push({id:opt.value, text:opt.text, selected:opt.selected});});
                tsUnit = new TomSelect(unitSelectElement, getTomSelectConfig(unitSelectElement.id, 'Оберіть ВЧ', false, htmlUnitOpts, true, [], false));
                unitSelectElement.tomselectInstance = tsUnit; console.log("MainForm: Unit TomSelect INITIALIZED.");
                tsUnit.on('change', handleUnitChange);
                const initialUnitVal = tsUnit.getValue();
                if (initialUnitVal && initialUnitVal !== "") { handleUnitChange(initialUnitVal); } else { handleUnitChange(null); }
            }
            if (oidSelectElement) {
                tsOid = new TomSelect(oidSelectElement, getTomSelectConfig(oidSelectElement.id, 'Спочатку оберіть ВЧ', true, [], true, [], false));
                oidSelectElement.tomselectInstance = tsOid; console.log("MainForm: OID TomSelect INITIALIZED (disabled).");
                tsOid.on('change', handleOidChange);
            }
            if (wriSelectElement) {
                tsWri = new TomSelect(wriSelectElement, getTomSelectConfig(wriSelectElement.id, 'Спочатку оберіть ОІД', true, [], true, [], false));
                wriSelectElement.tomselectInstance = tsWri; console.log("MainForm: WRI TomSelect INITIALIZED (disabled).");
                tsWri.on('change', handleWriChange);
            }
            if (authorSelectElement) {
                let htmlAuthorOpts = []; Array.from(authorSelectElement.options).forEach(opt => {if (opt.value) htmlAuthorOpts.push({id:opt.value, text:opt.text});});
                tsAuthor = new TomSelect(authorSelectElement, getTomSelectConfig(authorSelectElement.id, 'Оберіть автора (необов\'язково)', false, htmlAuthorOpts, true, [], false));
                authorSelectElement.tomselectInstance = tsAuthor; console.log("MainForm: Author TomSelect INITIALIZED.");
            }
        }
        function handleUnitChange(unitId) { /* ... як раніше, викликає loadOidsForUnit ... */
            console.log("MainForm: Unit CHANGED to:", unitId);
            currentOidId = null; currentOidType = null; currentSelectedWorkTypeFromWRI = null;
            if (tsOid) {
                tsOid.clear(); tsOid.clearOptions(); tsOid.sync();
                if (unitId) {
                    tsOid.enable(); tsOid.placeholder = 'Завантаження ОІДів...';
                    fetch(`${oidsForUnitAjaxUrl}?unit_id=${unitId}`)
                        .then(r => r.ok ? r.json() : r.text().then(t => { throw new Error(t || `Error ${r.status}`); }))
                        .then(data => {
                            const options = data.map(oid => ({ id: oid.id.toString(), text: `${oid.cipher} (${oid.full_name || 'Без назви'})`, oid_type: oid.oid_type }));
                            tsOid.addOptions(options); tsOid.refreshOptions(false);
                            tsOid.placeholder = options.length ? 'Оберіть ОІД...' : 'Для ВЧ немає ОІДів';
                            if (initialOidIdFromDjango && unitId == unitSelectElement.value && tsOid.options[initialOidIdFromDjango]) { // Compare unitId with current unitSelectElement value
                                 tsOid.setValue(initialOidIdFromDjango, true); handleOidChange(initialOidIdFromDjango); initialOidIdFromDjango = null; 
                            } else { handleOidChange(null); }
                        }).catch(e => { if (tsOid) tsOid.placeholder = 'Помилка завантаження ОІДів';});
                } else { tsOid.disable(); tsOid.placeholder = 'Спочатку оберіть ВЧ'; handleOidChange(null); }
            }
        }
        function handleOidChange(oidId) { /* ... як раніше, викликає load WRIs та updateAllDocTypes ... */
            console.log("MainForm: OID CHANGED to:", oidId); currentOidId = oidId; currentOidType = null; currentSelectedWorkTypeFromWRI = null;
            if (tsWri) {
                tsWri.clear(); tsWri.clearOptions(); tsWri.sync();
                if (oidId && tsOid) { // tsOid має бути доступний
                    const oidOptionData = tsOid.options[oidId]; 
                    if (oidOptionData && oidOptionData.oid_type) currentOidType = oidOptionData.oid_type;
                    tsWri.enable(); tsWri.placeholder = 'Завантаження заявок...';
                    fetch(`${wriForOidAjaxUrl}?oid_id=${oidId}`)
                        .then(r => r.ok ? r.json() : r.text().then(t => { throw new Error(t || `Error ${r.status}`); }))
                        .then(data => {
                            const options = data.map(item => ({ id: item.id.toString(), text: item.text, work_type: item.work_type }));
                            tsWri.addOptions(options); tsWri.refreshOptions(false);
                            tsWri.placeholder = options.length ? 'Елемент заявки (необов\'язково)' : 'Для ОІД немає заявок';
                            if (initialWRIIdFromDjango && oidId === wriSelectElement.querySelector(`option[value="${initialWRIIdFromDjango}"]`)?.parentElement.value && tsWri.options[initialWRIIdFromDjango]) { // Compare oidId
                                 tsWri.setValue(initialWRIIdFromDjango, true); handleWriChange(initialWRIIdFromDjango); initialWRIIdFromDjango = null;
                            } else { handleWriChange(null); }
                        }).catch(e => {if(tsWri) tsWri.placeholder = 'Помилка завантаження заявок';});
                } else { tsWri.disable(); tsWri.placeholder = 'Спочатку оберіть ОІД'; handleWriChange(null); }
            }
        }
        function handleWriChange(wriId) { /* ... як раніше, викликає updateAllDocTypes ... */
            console.log("MainForm: WRI CHANGED to:", wriId); currentSelectedWorkTypeFromWRI = null;
            if (wriId && tsWri) {
                const wriOptionData = tsWri.options[wriId];
                if (wriOptionData && wriOptionData.work_type) currentSelectedWorkTypeFromWRI = wriOptionData.work_type;
            }
            DocumentItemFormsetManager.updateAllDocTypes(currentOidId, currentOidType, currentSelectedWorkTypeFromWRI);
        }
        return { init, getCurrentOidId: () => currentOidId, getCurrentOidType: () => currentOidType, getCurrentWorkType: () => currentSelectedWorkTypeFromWRI };
    })();

    // --- Керування Формсетом DocumentItemFormSet ---
    const DocumentItemFormsetManager = (function() {
        // Використовуємо DjangoFormsetManager, визначений у вашому main.js або спільному файлі
        if (typeof DjangoFormsetManager === 'function') {
            console.log("AddDocProc JS: DjangoFormsetManager found. Initializing for Document Items.");
            const docItemFormset = DjangoFormsetManager({
                containerSelector: '#document-items-formset-container',
                addButtonSelector: '#add-document-item-button',
                emptyFormTemplateId: 'document-item-empty-form-template',
                formsetPrefix: '{{ formset.prefix }}',
                formClass: '.document-item-form',
                removeButtonClass: '.remove-document-item-button',
                canDelete: "{{ formset.can_delete|yesno:'true,false' }}" === 'true',
                initializeNewFormCallback: function(newFormElement, formIndex) {
                    console.log(`DocItemFormset CALLBACK: Initializing fields for new document form ${formIndex}`);
                    const docTypeSelect = newFormElement.querySelector('select[name$="-document_type"]');
                    if (docTypeSelect && typeof TomSelect !== 'undefined') {
                        let htmlDocTypeOptions = []; // Опції з empty_form
                        Array.from(docTypeSelect.options).forEach(opt => {if (opt.value) htmlDocTypeOptions.push({id:opt.value, text:opt.text});});
                        
                        const config = getTomSelectConfig( // Використовуємо глобальну getTomSelectConfig
                            docTypeSelect.id || `${formsetPrefix}-${formIndex}-document_type`,
                            'Оберіть тип документа', false, htmlDocTypeOptions, true, [], false
                        );
                        const instance = new TomSelect(docTypeSelect, config);
                        docTypeSelect.tomselectInstance = instance;
                        console.log(`DocItemFormset CALLBACK: TomSelect for DocType initialized for ${docTypeSelect.id || 'new_doc_type_select'}`);
                        
                        // Оновлюємо на основі головної форми (заглушка для фільтрації)
                        this.updateSpecificDocType(docTypeSelect.tomselectInstance); // "this" тут - це DocumentItemFormsetManager
                    }
                },
                beforeRemoveFormCallback: function(formToRemove) {
                    const docTypeSelect = formToRemove.querySelector('select[name$="-document_type"]');
                    if (docTypeSelect && docTypeSelect.tomselectInstance) {
                        docTypeSelect.tomselectInstance.destroy();
                    }
                }
            });
            
            // Додаємо метод updateAllDocTypes/updateSpecificDocType до екземпляра, якщо DjangoFormsetManager його не має
            // Ця частина залежить від того, як реалізований ваш DjangoFormsetManager
            // Для нашого прикладу, припустимо, що ми додаємо цей метод до нашого локального менеджера тут
            // або робимо DocumentItemFormsetManager.updateAllDocTypes доступним глобально.
            // Простіший варіант для цього прикладу - зробити updateAllDocTypes частиною цього IIFE.
            
            // Цей метод тепер має бути доступний всередині DocumentItemFormsetManager
            // або ми викликаємо його звідси, передаючи необхідні дані.
            // Для простоти, я залишу updateAllDocTypes як частину цього IIFE.
            function updateSpecificDocTypeInFormset(tsInstance) { // tsInstance - це TomSelect для document_type
                 if (!tsInstance) return;
                 const oidVal = MainFormManager.getCurrentOidId();
                 const oidTypeVal = MainFormManager.getCurrentOidType();
                 const workTypeVal = MainFormManager.getCurrentWorkType();
                 console.log(`DocItemFormset updateSpecificDocType: OID ID: ${oidVal}, OID Type: ${oidTypeVal}, Work Type: ${workTypeVal}`);
                 tsInstance.clear(); tsInstance.clearOptions(); tsInstance.sync();
                 if (oidVal && oidTypeVal) {
                    tsInstance.enable();
                    tsInstance.placeholder = `Типи для ОІД ${oidTypeVal || 'N/A'}${workTypeVal ? ', робіт ' + workTypeVal : ''} (фільтр заглушка)`;
                    // Тут ви б завантажували/фільтрували опції для DocumentType, якщо б не було заглушки
                    // Зараз, якщо DocumentItemForm.document_type мав queryset=all(), то вони будуть втрачені
                    // Потрібно або передавати їх знову, або ваш DjangoFormsetManager.initializeNewFormCallback
                    // має правильно ініціалізувати TomSelect з початковими опціями з empty_form.
                    // У моєму прикладі DjangoFormsetManager.initializeNewFormCallback вже це робить.
                    console.warn(`DocItemFormset: Actual DocumentType filtering for [${tsInstance.input.id}] is STUBBED.`);
                 } else {
                    tsInstance.disable(); tsInstance.placeholder = 'Оберіть ОІД та/або Заявку в гол. формі';
                 }
            }
            
            // Ініціалізуємо сам менеджер формсету
            if (docItemFormset && typeof docItemFormset.init === 'function') {
                 docItemFormset.init();
                 // Зберігаємо функцію оновлення, щоб MainFormManager міг її викликати
                 DocumentItemFormsetManager.updateAllDocTypes = function(oidId, oidType, workType) {
                     console.log("AddDocProc JS: Global updateAllDocTypes called by MainFormManager.");
                     container.querySelectorAll('.document-item-form').forEach(formDiv => {
                         const docTypeSelect = formDiv.querySelector('select[name$="-document_type"]');
                         if (docTypeSelect && docTypeSelect.tomselectInstance) {
                            updateSpecificDocTypeInFormset(docTypeSelect.tomselectInstance); // Виклик внутрішньої функції
                         }
                     });
                 };

            } else {
                console.error("AddDocProc JS: Failed to initialize DjangoFormsetManager for Document Items.");
            }
        } else {
            console.warn("AddDocProc JS: DjangoFormsetManager is not defined. Formset 'add/remove' functionality will not work.");
        }
        return { // Повертаємо лише ті методи, які потрібні ззовні
            updateAllDocTypes: (typeof DjangoFormsetManager === 'function' && DocumentItemFormsetManager.updateAllDocTypes) 
                                ? DocumentItemFormsetManager.updateAllDocTypes 
                                : (oidId, oidType, workType) => { console.warn("updateAllDocTypes called, but formset manager not fully ready."); }
        };
    })(); // Кінець DocumentItemFormsetManager

    // --- Головна ініціалізація ---
    console.log("AddDocProc JS: Initializing managers.");
    MainFormManager.init(); 
    // DocumentItemFormsetManager.init() тепер викликається всередині обгортки
    // if (typeof DjangoFormsetManager === 'function') { /* ... */ }

});