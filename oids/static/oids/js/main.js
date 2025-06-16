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
	OID_CREATE_FORM: "#ajaxOidCreateForm", // ID форми створення ОІД. раніше була #oid-create-form
	
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
            // TODO: Якщо Tom Select має теми, які залежать від класів body,
            // можливо, потрібно буде оновити/переініціалізувати екземпляри Tom Select тут.
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
 * @param {HTMLElement} formElement - DOM-елемент форми.
 * @param {number} index - Новий індекс форми.
 */
function updateFormElementAttributes(formElement, index) {
    formElement.dataset.formIndex = index; // Оновлюємо data-атрибут форми
    formElement.querySelectorAll("input, select, textarea, label").forEach((el) => {
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
    const formsetContainer = document.querySelector(SELECTORS.FORMSET_CONTAINER);
    const totalFormsInput = document.querySelector(SELECTORS.TOTAL_FORMS_INPUT);

    if (!formsetContainer || !totalFormsInput) {
        console.warn("Контейнер формсету або поле totalFormsInput не знайдено.");
        return;
    }

    const currentForms = formsetContainer.querySelectorAll(SELECTORS.DOCUMENT_FORM_CLASS);

    // Перевіряємо, чи є хоча б одна базова форма для клонування
    if (currentForms.length === 0) {
        const templateForm = document.getElementById("empty-form-template"); // Припускаємо, що у вас є шаблон
        if (!templateForm) {
            console.warn("Не знайдено базової форми для клонування ('" + SELECTORS.DOCUMENT_FORM_CLASS + "') та шаблону ('#empty-form-template').");
            return;
        }
        // Клонуємо з шаблону, якщо форм немає
        // Ця частина залежить від того, як ви реалізуєте 'empty-form-template'
        // Наприклад: const newForm = templateForm.content.cloneNode(true).firstElementChild;
        console.warn("Логіка клонування з шаблону ще не реалізована повністю.");
        return; // Тимчасово виходимо, якщо немає форм і шаблон не оброблений
    }

    const newForm = currentForms[0].cloneNode(true);
    const newIndex = currentForms.length;

    // Очищаємо значення інпутів у новій формі
    newForm.querySelectorAll("input, select, textarea").forEach((el) => {
        if (el.type !== "hidden" && el.tagName !== "SELECT") {
            // Для select очищення значення може бути іншим
            el.value = "";
        } else if (el.tagName === "SELECT") {
            el.selectedIndex = 0; // Скидаємо select на перший варіант (зазвичай порожній)
            // TODO: Якщо select був Tom Select, його потрібно буде очистити/скинути через API Tom Select
            if (el.tomselect) {
                el.tomselect.clear();
            }
        }

        // Очистити поля, які можуть бути ініціалізовані TomSelect
        // Це потрібно, щоб при клонуванні не копіювався стан TomSelect
        // TomSelect буде ініціалізований для нової форми окремо
        if (el.classList.contains("tomselect-hidden-input")) {
            // Приклад, якщо TomSelect додає такий клас
            el.remove(); // Видаляємо залишки від попереднього TomSelect
        }
    });

    // Видаляємо контейнер TomSelect, якщо він був скопійований
    const tomSelectWrapper = newForm.querySelector(".ts-wrapper");
    if (tomSelectWrapper) {
        tomSelectWrapper.remove();
    }

    updateFormElementAttributes(newForm, newIndex);
    formsetContainer.appendChild(newForm);
    totalFormsInput.value = newIndex + 1;

    // TODO: Ініціалізувати Tom Select для select елементів у `newForm`
    // Наприклад: initializeTomSelectForForm(newForm);

    updateDeleteButtonsVisibility();
}

/**
 * Видаляє форму з формосета.
 * @param {Event} event - Подію кліку по кнопці видалення.
 */
function removeDocumentForm(event) {
    const formDiv = event.target.closest(SELECTORS.DOCUMENT_FORM_CLASS);
    if (!formDiv) return;

    // TODO: Якщо на елементах форми був ініціалізований Tom Select, його потрібно знищити
    // formDiv.querySelectorAll('select').forEach(select => {
    //   if (select.tomselect) {
    //     select.tomselect.destroy();
    //   }
    // });

    formDiv.remove();

    const totalFormsInput = document.querySelector(SELECTORS.TOTAL_FORMS_INPUT);
    const formsAfterRemoval = document.querySelectorAll(SELECTORS.DOCUMENT_FORM_CLASS);
    if (totalFormsInput) {
        totalFormsInput.value = formsAfterRemoval.length;
    }

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
    // Оновлюємо для кожної форми окремо, оскільки кнопка видалення всередині форми
    forms.forEach((form) => {
        const deleteButton = form.querySelector(SELECTORS.REMOVE_FORM_BUTTON);
        if (deleteButton) {
            deleteButton.style.display = forms.length <= 1 ? "none" : "block";
        }
    });
}

/**
 * Ініціалізує логіку додавання/видалення форм.
 */
function setupDocumentFormsetLogic() {
    const addFormBtn = document.querySelector(SELECTORS.ADD_FORM_BUTTON);
    const formsetContainer = document.querySelector(SELECTORS.FORMSET_CONTAINER);

    if (addFormBtn) {
        // Ініціалізуємо, тільки якщо є кнопка додавання
        addFormBtn.addEventListener("click", addDocumentForm);
    }

    if (formsetContainer) {
        // Делегування подій, якщо є контейнер
        formsetContainer.addEventListener("click", function (event) {
            if (event.target.closest(SELECTORS.REMOVE_FORM_BUTTON)) {
                removeDocumentForm(event);
            }
  
        });
        updateDeleteButtonsVisibility(); // Початкове налаштування видимості кнопок
    }
}

// =====================================================================================================
// Головна функція ініціалізації всіх скриптів
// =====================================================================================================

document.addEventListener("DOMContentLoaded", function () {
    disableFormsAutocomplete();
    setupThemeToggle();
    hideMessages();
    setupDateRangeFilter();

    // Ініціалізація логіки формсету, якщо є відповідні елементи
    if (document.querySelector(SELECTORS.FORMSET_CONTAINER) || document.querySelector(SELECTORS.ADD_FORM_BUTTON)) {
        setupDocumentFormsetLogic();
	}
	
    // TODO: Тут буде місце для ініціалізації Tom Select для всіх потрібних полів <select>
    // Наприклад:
    // document.querySelectorAll('select.tomselect-field').forEach(selectEl => {
    //   new TomSelect(selectEl, { /* options */ });
    // });
    // Або виклик більш специфічної функції, яка знаходить і налаштовує Tom Select.
});
