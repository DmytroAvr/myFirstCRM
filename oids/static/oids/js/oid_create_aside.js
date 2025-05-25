// constants.js (або вгорі вашого основного файлу скриптів)
const SELECTORS = {
    FORMSET_CONTAINER: '#formset',
    ADD_FORM_BUTTON: '#add-form',
    TOTAL_FORMS_INPUT: '#id_form-TOTAL_FORMS',
    DOCUMENT_FORM_CLASS: '.document-form',
    ADD_OID_BUTTON: '.add-oid-button',
    REMOVE_FORM_BUTTON: '.remove-form',
    OID_ASIDE: '#oid-aside',
    OVERLAY: '#overlay',
    INSERT_UNIT_SPAN: '#insert_unit',
    UNIT_SELECT: '#id_unit',
    OID_ASIDE_CLOSE_BUTTON: '#oid-aside-close',
    OID_CREATE_FORM: '#oid-create-form',
    OID_SELECT_NAME_SUFFIX: '-oid', // для вибору OID поля у формах
};

// =====================================================================================================
// Управління формами формосета (додавання/видалення)
// =====================================================================================================

/**
 * Оновлює атрибути name, id та htmlFor для елементів у новій формі.
 * @param {HTMLElement} form - Клонована форма.
 * @param {number} index - Новий індекс форми.
 */
function updateFormElementAttributes(form, index) {
    form.querySelectorAll('input, select, textarea, label').forEach(el => {
        const nameAttr = el.getAttribute('name');
        const idAttr = el.getAttribute('id');
        const htmlForAttr = el.getAttribute('htmlFor');

        if (nameAttr) {
            el.setAttribute('name', nameAttr.replace(/form-\d+-/, `form-${index}-`));
        }
        if (idAttr) {
            el.setAttribute('id', idAttr.replace(/form-\d+-/, `form-${index}-`));
        }
        if (htmlForAttr) {
            el.setAttribute('htmlFor', htmlForAttr.replace(/form-\d+-/, `form-${index}-`));
        }
    });
}

/**
 * Додає нову форму до формосета.
 */
function addForm() {
    const formset = document.querySelector(SELECTORS.FORMSET_CONTAINER);
    const totalFormsInput = document.querySelector(SELECTORS.TOTAL_FORMS_INPUT);
    const currentForms = formset.querySelectorAll(SELECTORS.DOCUMENT_FORM_CLASS);

    // Клонуємо першу форму, щоб зберегти структуру
    const newForm = currentForms[0].cloneNode(true);
    const newIndex = currentForms.length;

    newForm.dataset.formIndex = newIndex; // Встановлюємо data-атрибут для зручності

    // Очищаємо значення інпутів у новій формі
    newForm.querySelectorAll('input, select, textarea').forEach(el => {
        if (el.type !== 'hidden') {
            el.value = '';
        }
    });

    // Оновлюємо атрибути name, id, htmlFor
    updateFormElementAttributes(newForm, newIndex);

    // Додаємо нову форму до DOM
    formset.appendChild(newForm);

    // Оновлюємо TOTAL_FORMS
    totalFormsInput.value = newIndex + 1;

    // Оновлюємо стан кнопок видалення
    updateDeleteButtonsVisibility();
}

/**
 * Видаляє форму з формосета.
 * @param {Event} event - Подію кліку по кнопці видалення.
 */
function removeForm(event) {
    const formDiv = event.target.closest(SELECTORS.DOCUMENT_FORM_CLASS);
    if (!formDiv) return;

    formDiv.remove();

    // Оновлюємо TOTAL_FORMS
    const totalFormsInput = document.querySelector(SELECTORS.TOTAL_FORMS_INPUT);
    const formsAfterRemoval = document.querySelectorAll(SELECTORS.DOCUMENT_FORM_CLASS);
    totalFormsInput.value = formsAfterRemoval.length;

    // Перенумеровуємо залишені форми
    formsAfterRemoval.forEach((form, index) => {
        form.dataset.formIndex = index;
        updateFormElementAttributes(form, index);
    });

    updateDeleteButtonsVisibility();
}

/**
 * Оновлює видимість кнопок видалення.
 * Якщо залишилась лише одна форма, кнопка видалення приховується.
 */
function updateDeleteButtonsVisibility() {
    const forms = document.querySelectorAll(SELECTORS.DOCUMENT_FORM_CLASS);
    const deleteButtons = document.querySelectorAll(SELECTORS.REMOVE_FORM_BUTTON);

    if (forms.length <= 1) {
        deleteButtons.forEach(btn => btn.style.display = 'none');
    } else {
        deleteButtons.forEach(btn => btn.style.display = 'block');
    }
}

// =====================================================================================================
// Управління бічним вікном (Aside) для створення ОІД
// =====================================================================================================

let targetOidSelect = null; // Зробимо цю змінну доступною для функцій aside, але не глобальною

/**
 * Відкриває бічне вікно для створення ОІД.
 * @param {Event} event - Подію кліку по кнопці додавання ОІД.
 */
function openOidAside(event) {
    const unitSelect = document.querySelector(SELECTORS.UNIT_SELECT);
    const unitId = unitSelect ? unitSelect.value : null;

    if (!unitId) {
        alert("Будь ласка, спочатку оберіть військову частину.");
        return;
    }

    const aside = document.querySelector(SELECTORS.OID_ASIDE);
    const overlay = document.querySelector(SELECTORS.OVERLAY);
    const unitSpan = document.querySelector(SELECTORS.INSERT_UNIT_SPAN);

    // Знаходимо відповідний select для OID у поточній формі
    const formDiv = event.target.closest(SELECTORS.DOCUMENT_FORM_CLASS) || event.target.closest('form');
    // Перевіряємо, чи це select, який закінчується на '-oid' (для формсету)
    // або просто 'oid' (якщо це основна форма)
    targetOidSelect = formDiv.querySelector(`select[name$="${SELECTORS.OID_SELECT_NAME_SUFFIX}"], select[name="oid"]`);


    if (unitSelect.selectedIndex > -1) {
        unitSpan.textContent = unitSelect.options[unitSelect.selectedIndex].text;
    }

    aside.style.display = 'block';
    overlay.style.display = 'block';
    aside.dataset.targetForm = formDiv.dataset.formIndex; // Зберігаємо індекс форми, з якої відкрили aside
}

/**
 * Закриває бічне вікно для створення ОІД.
 */
function closeOidAside() {
    document.querySelector(SELECTORS.OID_ASIDE).style.display = "none";
    document.querySelector(SELECTORS.OVERLAY).style.display = "none";
    targetOidSelect = null; // Очищаємо посилання на select
}

/**
 * Обробляє відправку форми створення ОІД через AJAX.
 * @param {Event} event - Подію відправки форми.
 */
async function handleOidCreateFormSubmit(event) {
    event.preventDefault();

    const form = event.target;
    const formData = new FormData(form);
    const unitSelect = document.querySelector(SELECTORS.UNIT_SELECT);
    const unitId = unitSelect ? unitSelect.value : null;

    if (unitId) {
        formData.append('unit_id', unitId);
    } else {
        alert("Помилка: Не обрано військову частину для створення ОІД.");
        return;
    }

    try {
        const response = await fetch('/oids/ajax/create/', {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': formData.get('csrfmiddlewaretoken')
            }
        });
        const data = await response.json();

        if (data.success) {
            alert("✅ ОІД створено");
            form.reset();
            closeOidAside();

            // Оновлюємо Select2 поле у формі
            if (targetOidSelect) {
                const newOption = new Option(data.oid.name, data.oid.id, true, true); // text, value, defaultSelected, selected
                // Перевіряємо, чи це Select2 поле, і додаємо опцію відповідно
                if (targetOidSelect.classList.contains('select2-hidden-accessible')) {
                    // Якщо це Select2, потрібно програмно додати опцію і тригернути подію
                    $(targetOidSelect).append(newOption).trigger('change');
                } else {
                    targetOidSelect.appendChild(newOption);
                }
            }

            // Якщо потрібно оновити існуючі Select2 поля OID після створення нового OID
            // Це може бути складно, якщо Select2 вже ініціалізовано.
            // Можливо, краще перезавантажити дані для всіх Select2 OID-полів
            // або надати окремий AJAX endpoint для оновлення Select2 даних.
            // Приклад для всіх Select2-полів OID:
            document.querySelectorAll(`select[name$="${SELECTORS.OID_SELECT_NAME_SUFFIX}"], select[name="oid"]`).forEach(selectElement => {
                if ($(selectElement).data('select2')) { // Перевірка, чи Select2 ініціалізовано
                    const currentUnitId = document.querySelector(SELECTORS.UNIT_SELECT).value;
                    // Оновлюємо дані для Select2, якщо він прив'язаний до поточної військової частини
                    if (selectElement.dataset.unitId === currentUnitId) { // Додайте data-unit-id до ваших select OID
                         // Можливо, вам знадобиться перевикликати функцію завантаження даних для Select2
                         // або просто додати нову опцію, якщо вона ще не існує
                    }
                }
            });


        } else {
            alert("❌ Помилка:\n" + JSON.stringify(data.errors, null, 2)); // Красивіший вивід помилок
        }
    } catch (err) {
        console.error("❌ Помилка зв'язку з сервером:", err);
        alert("⚠️ Помилка зв’язку з сервером. Перевірте консоль для деталей.");
    }
}

// =====================================================================================================
// Ініціалізація та обробники подій
// =====================================================================================================

document.addEventListener('DOMContentLoaded', function () {
    const addFormBtn = document.querySelector(SELECTORS.ADD_FORM_BUTTON);
    const oidAsideCloseBtn = document.querySelector(SELECTORS.OID_ASIDE_CLOSE_BUTTON);
    const oidCreateForm = document.querySelector(SELECTORS.OID_CREATE_FORM);
    const formsetContainer = document.querySelector(SELECTORS.FORMSET_CONTAINER);

    // Обробник для кнопки додавання нової форми
    if (addFormBtn) {
        addFormBtn.addEventListener('click', addForm);
    }

    // Делегування подій для кнопок видалення форми
    // Це дозволяє обробляти кліки на кнопках, які додаються динамічно
    formsetContainer.addEventListener('click', function(event) {
        if (event.target.closest(SELECTORS.REMOVE_FORM_BUTTON)) {
            removeForm(event);
        }
        if (event.target.closest(SELECTORS.ADD_OID_BUTTON)) {
            openOidAside(event);
        }
    });

    // Обробники для бічного вікна ОІД
    if (oidAsideCloseBtn) {
        oidAsideCloseBtn.addEventListener('click', closeOidAside);
    }
    if (oidCreateForm) {
        oidCreateForm.addEventListener('submit', handleOidCreateFormSubmit);
    }

    // Ініціалізація видимості кнопок видалення при завантаженні сторінки
    updateDeleteButtonsVisibility();

    // Якщо ви використовуєте Select2, переконайтеся, що він ініціалізований.
    // Зазвичай це робиться в іншому місці, або тут, якщо необхідно.
    // Приклад:
    // $('.select2').select2(); // Якщо у вас є загальний селектор для всіх Select2
});