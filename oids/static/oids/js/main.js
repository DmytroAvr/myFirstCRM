// oids/static/oids/js/main.js

// Об'єкт для зберігання всіх селекторів.
// Це покращує читабельність та легкість підтримки.
const SELECTORS = {
    // Загальні селектори
    ALL_FORMS: "form",
    THEME_TOGGLE_BUTTON: ".theme-toggle",
    MESSAGES_CONTAINER: "#messages",

    // Селектори для фільтра дати
    START_DATE_INPUT: "#id_start_date",
    END_DATE_INPUT: "#id_end_date",

    // Селектори для формсету документів
    FORMSET_CONTAINER: "#formset",
    ADD_FORM_BUTTON: "#add-form",
    TOTAL_FORMS_INPUT: "#id_form-TOTAL_FORMS",
    DOCUMENT_FORM_CLASS: ".document-form",
    REMOVE_FORM_BUTTON: ".remove-form",

    // Селектори для aside створення OID
    ADD_OID_BUTTON: ".add-oid-button", // Кнопка, що відкриває aside
    OID_ASIDE: "#oid-aside",
    OVERLAY: "#overlay",
    INSERT_UNIT_SPAN: "#insert_unit", // Span для відображення назви військової частини
    UNIT_SELECT: "#id_unit", // Основний select для військової частини (один на сторінці)
    OID_ASIDE_CLOSE_BUTTON: "#oid-aside-close",
    OID_CREATE_FORM: "#oid-create-form",
    OID_SELECT_NAME_SUFFIX: "-oid", // Для полів OID у формсеті (e.g., form-0-oid)
    OID_SELECT_MAIN_NAME: "oid", // Для основного поля OID, якщо воно не в формсеті (e.g., id_oid)
};

// =====================================================================================================
// Загальні утиліти та функції
// =====================================================================================================

/**
 * Встановлює атрибут `autocomplete="off"` для всіх форм.
 */
function disableFormsAutocomplete() {
    document.querySelectorAll(SELECTORS.ALL_FORMS).forEach((form) => {
        form.setAttribute("autocomplete", "off");
    });
}

/**
 * Перемикає тему (світла/темна).
 */
function setupThemeToggle() {
    const themeToggleButton = document.querySelector(SELECTORS.THEME_TOGGLE_BUTTON);
    if (themeToggleButton) {
        themeToggleButton.addEventListener("click", () => {
            document.body.classList.toggle("dark-theme");
            // Можливо, потрібно буде оновити тему Select2 після зміни теми
            if (typeof initSelect2Fields === "function") {
                // Перевіряємо, чи функція існує
                // Переініціалізувати Select2 з новою темою
                initSelect2Fields();
            }
        });
    }
}

/**
 * Приховує повідомлення через кілька секунд.
 */
function hideMessages() {
    const messagesContainer = document.querySelector(SELECTORS.MESSAGES_CONTAINER);
    if (messagesContainer) {
        setTimeout(() => {
            messagesContainer.style.display = "none";
        }, 5000); // Приховати через 5 секунд
    }
}

// =====================================================================================================
// Логіка для фільтрації дати (календаря)
// =====================================================================================================

/**
 * Встановлює обмеження для полів дати (початок не може бути пізніше кінця, кінець не раніше початку).
 */
function setupDateRangeFilter() {
    const startDateInput = document.querySelector(SELECTORS.START_DATE_INPUT);
    const endDateInput = document.querySelector(SELECTORS.END_DATE_INPUT);

    if (startDateInput && endDateInput) {
        startDateInput.addEventListener("change", function () {
            endDateInput.setAttribute("min", this.value);
        });

        endDateInput.addEventListener("change", function () {
            startDateInput.setAttribute("max", this.value);
        });
    }
}

// =====================================================================================================
// Логіка для формсету документів (додавання/видалення форм)
// =====================================================================================================

/**
 * Оновлює атрибути name, id та htmlFor для елементів у новій/перенумерованій формі.
 * @param {HTMLElement} form - DOM-елемент форми.
 * @param {number} index - Новий індекс форми.
 */
function updateFormElementAttributes(form, index) {
    form.dataset.formIndex = index; // Оновлюємо data-атрибут форми
    form.querySelectorAll("input, select, textarea, label").forEach((el) => {
        const nameAttr = el.getAttribute("name");
        const idAttr = el.getAttribute("id");
        const htmlForAttr = el.getAttribute("htmlFor");

        if (nameAttr) {
            el.setAttribute("name", nameAttr.replace(/form-\d+-/, `form-${index}-`));
        }
        if (idAttr) {
            el.setAttribute("id", idAttr.replace(/form-\d+-/, `form-${index}-`));
        }
        if (htmlForAttr) {
            el.setAttribute("htmlFor", htmlForAttr.replace(/form-\d+-/, `form-${index}-`));
        }
    });
}

/**
 * Додає нову форму до формосета.
 */
function addDocumentForm() {
    const formset = document.querySelector(SELECTORS.FORMSET_CONTAINER);
    const totalFormsInput = document.querySelector(SELECTORS.TOTAL_FORMS_INPUT);
    const currentForms = formset.querySelectorAll(SELECTORS.DOCUMENT_FORM_CLASS);

    // Перевіряємо, чи є хоча б одна базова форма для клонування
    if (currentForms.length === 0) {
        console.warn("Не знайдено базової форми для клонування. Переконайтеся, що є '.document-form' елементи.");
        return;
    }

    const newForm = currentForms[0].cloneNode(true);
    const newIndex = currentForms.length;

    // Очищаємо значення інпутів у новій формі
    newForm.querySelectorAll("input, select, textarea").forEach((el) => {
        if (el.type !== "hidden") {
            el.value = "";
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

    // Якщо використовуються Select2, перевикликаємо ініціалізацію для нової форми
    if (typeof initSelect2Fields === "function") {
        initSelect2Fields(newForm); // Ініціалізуємо Select2 тільки для нової форми
        console.log(`select2 init fo new form ${newForm}`);
    }
}

/**
 * Видаляє форму з формосета.
 * @param {Event} event - Подію кліку по кнопці видалення.
 */
function removeDocumentForm(event) {
    const formDiv = event.target.closest(SELECTORS.DOCUMENT_FORM_CLASS);
    if (!formDiv) return;

    formDiv.remove();

    // Оновлюємо TOTAL_FORMS
    const totalFormsInput = document.querySelector(SELECTORS.TOTAL_FORMS_INPUT);
    const formsAfterRemoval = document.querySelectorAll(SELECTORS.DOCUMENT_FORM_CLASS);
    totalFormsInput.value = formsAfterRemoval.length;

    // Перенумеровуємо залишені форми
    formsAfterRemoval.forEach((form, index) => {
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
        deleteButtons.forEach((btn) => (btn.style.display = "none"));
    } else {
        deleteButtons.forEach((btn) => (btn.style.display = "block"));
    }
}

/**
 * Ініціалізує логіку додавання/видалення форм.
 */
function setupDocumentFormsetLogic() {
    const addFormBtn = document.querySelector(SELECTORS.ADD_FORM_BUTTON);
    const formsetContainer = document.querySelector(SELECTORS.FORMSET_CONTAINER);

    if (addFormBtn && formsetContainer) {
        addFormBtn.addEventListener("click", addDocumentForm);

        // Делегування подій для кнопок видалення форми та кнопок додавання ОІД
        formsetContainer.addEventListener("click", function (event) {
            if (event.target.closest(SELECTORS.REMOVE_FORM_BUTTON)) {
                removeDocumentForm(event);
            }
            if (event.target.closest(SELECTORS.ADD_OID_BUTTON)) {
                openOidAside(event);
            }
        });

        // Ініціалізація видимості кнопок видалення при завантаженні сторінки
        updateDeleteButtonsVisibility();
    } else if (addFormBtn) {
        console.warn("Кнопка додавання форми знайдена, але контейнер формсету (id='formset') відсутній.");
    } else if (formsetContainer) {
        console.warn("Контейнер формсету знайдений, але кнопка додавання форми (id='add-form') відсутня.");
    }
}

// =====================================================================================================
// Логіка для бічного вікна (Aside) створення ОІД
// =====================================================================================================

let targetOidSelect = null; // Буде посилатися на select елемент, який потрібно оновити

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

    if (!aside || !overlay || !unitSpan) {
        console.error("Один або декілька необхідних елементів для OID Aside відсутні.");
        return;
    }

    // Знаходимо відповідний select для OID у поточній формі або основній формі
    const formDiv = event.target.closest(SELECTORS.DOCUMENT_FORM_CLASS);
    if (formDiv) {
        // Якщо кнопка всередині формсету
        targetOidSelect = formDiv.querySelector(`select[name$="${SELECTORS.OID_SELECT_NAME_SUFFIX}"]`);
    } else {
        // Якщо кнопка OID поза формсетом (у головній формі)
        targetOidSelect = document.querySelector(`select[name="${SELECTORS.OID_SELECT_MAIN_NAME}"]`);
    }

    if (!targetOidSelect) {
        console.error("Не знайдено SELECT елемент для OID у формі, з якої було відкрито aside.");
        return;
    }

    if (unitSelect.selectedIndex > -1) {
        unitSpan.textContent = unitSelect.options[unitSelect.selectedIndex].text;
    }

    aside.style.display = "block";
    overlay.style.display = "block";
}

/**
 * Закриває бічне вікно для створення ОІД.
 */
function closeOidAside() {
    const aside = document.querySelector(SELECTORS.OID_ASIDE);
    const overlay = document.querySelector(SELECTORS.OVERLAY);
    if (aside) aside.style.display = "none";
    if (overlay) overlay.style.display = "none";
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

    if (!unitId) {
        alert("Помилка: Не обрано військову частину для створення ОІД.");
        return;
    }
    formData.append("unit_id", unitId);

    try {
        const response = await fetch("/oids/ajax/create/", {
            // Переконайтеся, що це правильний URL
            method: "POST",
            body: formData,
            headers: {
                "X-CSRFToken": formData.get("csrfmiddlewaretoken"),
            },
        });
        const data = await response.json();

        if (data.success) {
            alert("✅ ОІД успішно створено!");
            form.reset();
            closeOidAside();

            // Оновлюємо Select2 поле у формі, з якої було відкрито aside
            if (targetOidSelect) {
                const newOption = new Option(data.oid.name, data.oid.id, true, true);
                if ($(targetOidSelect).data("select2")) {
                    $(targetOidSelect).append(newOption).trigger("change");
                } else {
                    targetOidSelect.appendChild(newOption);
                }
            }

            // Додатково: Можливо, вам потрібно оновити інші Select2 поля OID на сторінці
            // наприклад, якщо вони залежать від однієї і тієї ж військової частини
            // (цей функціонал може вимагає додаткової логіки на бекенді для AJAX оновлення Select2)
            document.querySelectorAll(`select[name$="${SELECTORS.OID_SELECT_NAME_SUFFIX}"], select[name="${SELECTORS.OID_SELECT_MAIN_NAME}"]`).forEach((selectElement) => {
                if ($(selectElement).data("select2") && selectElement !== targetOidSelect) {
                    // Якщо Select2 вже ініціалізовано, потрібно оновити його дані.
                    // Це може бути зроблено через AJAX знову, або якщо Select2
                    // вже підключений до AJAX-джерела, достатньо оновити його.
                    // Це дуже специфічно для вашої конфігурації Select2.
                    // Можливо, вам просто потрібно оновити всі select2, що пов'язані з OID,
                    // якщо їхні дані залежать від `unitId`.
                    // Якщо Select2 використовує AJAX, то він сам завантажить дані при пошуку,
                    // тому можливо, нічого тут не потрібно робити, крім додавання нової опції.
                }
            });
        } else {
            alert("❌ Помилка:\n" + JSON.stringify(data.errors, null, 2));
        }
    } catch (err) {
        console.error("❌ Помилка зв'язку з сервером:", err);
        alert("⚠️ Помилка зв’язку з сервером. Перевірте консоль для деталей.");
    }
}

// =====================================================================================================
// Головна функція ініціалізації всіх скриптів
// =====================================================================================================

document.addEventListener("DOMContentLoaded", function () {
    // Запускаємо загальні функції, які потрібні на всіх сторінках
    disableFormsAutocomplete();
    setupThemeToggle();
    hideMessages();

    // Запускаємо функції, які потребують наявності конкретних елементів
    setupDateRangeFilter(); // Запуститься, якщо знайдуться поля дати

    // Важливо: перевіряємо, чи є елементи формсету, перед тим як ініціалізувати логіку формсету.
    // Якщо є контейнер формсету або кнопка додавання, тоді ініціалізуємо.
    if (document.querySelector(SELECTORS.FORMSET_CONTAINER) || document.querySelector(SELECTORS.ADD_FORM_BUTTON)) {
        setupDocumentFormsetLogic();
    }

    // Запускаємо логіку aside, якщо є елементи aside
    if (document.querySelector(SELECTORS.OID_ASIDE)) {
        setupOidAsideLogic();
    }
    // initSelect2Fields();

    // Виклик для ініціалізації динамічних фільтрів
    // initializeDynamicFilters();
    // Примітки:
    // -  викликається в `select2-init.js`, який підключений раніше.
    // - Логіка Select2 для динамічного оновлення OID-ів при зміні UnitId повинна бути
    //   в `select2-init.js` або викликатися звідти.
    // - Якщо Select2 ініціалізується для динамічних полів, переконайтеся,
    //   що ви перевикликаєте `initSelect2Fields` для нових форм у `addDocumentForm`.
});
