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
    OID_CREATE_FORM: "#oid-create-form", // ID форми створення ОІД
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
            // Кнопка додавання ОІД тепер обробляється глобально, не тільки в формсеті
            // if (event.target.closest(SELECTORS.ADD_OID_BUTTON)) {
            //     openOidAside(event);
            // }
        });
        updateDeleteButtonsVisibility(); // Початкове налаштування видимості кнопок
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
    const unitSelectField = document.querySelector(SELECTORS.UNIT_SELECT); // Головний селект ВЧ на сторінці
    const unitId = unitSelectField ? unitSelectField.value : null;

    if (!unitId) {
        alert("Будь ласка, спочатку оберіть військову частину.");
        return;
    }

    const aside = document.querySelector(SELECTORS.OID_ASIDE);
    const overlay = document.querySelector(SELECTORS.OVERLAY);
    const unitSpan = document.querySelector(SELECTORS.INSERT_UNIT_SPAN); // Span для назви ВЧ в aside

    if (!aside || !overlay || !unitSpan) {
        console.error("Один або декілька необхідних елементів для OID Aside відсутні: OID_ASIDE, OVERLAY, INSERT_UNIT_SPAN.");
        return;
    }

    const clickedButton = event.target.closest(SELECTORS.ADD_OID_BUTTON);
    if (!clickedButton) return;

    // Визначаємо цільовий select для ОІД
    // Це може бути select поруч з кнопкою "Додати ОІД" або вказаний через data-атрибут
    const targetSelectId = clickedButton.dataset.targetSelect; // Наприклад, data-target-select="#id_form-0-oid"
    if (targetSelectId) {
        targetOidSelect = document.querySelector(targetSelectId);
    } else {
        // Якщо data-атрибут не вказано, шукаємо найближчий select з типовим іменем
        const formRow = clickedButton.closest(".form-row, .document-form, form"); // Шукаємо батьківський контейнер поля
        if (formRow) {
            targetOidSelect = formRow.querySelector(`select[name$="${SELECTORS.OID_SELECT_NAME_SUFFIX}"], select[name="${SELECTORS.OID_SELECT_MAIN_NAME}"]`);
        }
    }

    if (!targetOidSelect) {
        console.error("Не знайдено SELECT елемент для OID, асоційований з кнопкою.");
        // Можливо, варто пройтися по всіх select, що відповідають патерну, і якщо він один - використати його.
        // Або зробити зв'язок кнопки та select більш явним, наприклад, через data-attributes.
        return;
    }

    if (unitSelectField.selectedIndex > -1) {
        unitSpan.textContent = unitSelectField.options[unitSelectField.selectedIndex].text;
    } else {
        unitSpan.textContent = "ВЧ не обрано";
    }

    // Передаємо ID основної ВЧ у приховане поле форми створення ОІД
    const oidCreateForm = document.querySelector(SELECTORS.OID_CREATE_FORM);
    if (oidCreateForm) {
        let unitHiddenInput = oidCreateForm.querySelector('input[name="unit"]'); // Припускаємо, що поле називається 'unit'
        if (!unitHiddenInput) {
            unitHiddenInput = document.createElement("input");
            unitHiddenInput.type = "hidden";
            unitHiddenInput.name = "unit"; // Це поле має відповідати назві поля в OIDForm в Django
            oidCreateForm.appendChild(unitHiddenInput);
        }
        unitHiddenInput.value = unitId;
    }

    aside.style.display = "block";
    overlay.style.display = "block";
    document.body.classList.add("overflow-hidden"); // Заборонити прокрутку основної сторінки
}

/**
 * Закриває бічне вікно для створення ОІД.
 */
function closeOidAside() {
    const aside = document.querySelector(SELECTORS.OID_ASIDE);
    const overlay = document.querySelector(SELECTORS.OVERLAY);
    if (aside) aside.style.display = "none";
    if (overlay) overlay.style.display = "none";
    document.body.classList.remove("overflow-hidden");
    targetOidSelect = null; // Очищаємо посилання на select
}

/**
 * Обробляє відправку форми створення ОІД через AJAX.
 * @param {Event} event - Подію відправки форми.
 */
async function handleOidCreateFormSubmit(event) {
    event.preventDefault();

    const form = event.target; // Це #oid-create-form
    const formData = new FormData(form);

    // CSRF токен вже повинен бути в formData, якщо він є hidden input у формі
    // const csrfToken = formData.get("csrfmiddlewaretoken"); // Або отримати його інакше, якщо потрібно

    // unit_id вже додано до formData в openOidAside
    // const unitSelect = document.querySelector(SELECTORS.UNIT_SELECT);
    // const unitId = unitSelect ? unitSelect.value : null;
    // if (!unitId) {
    //     alert("Помилка: Не обрано військову частину для створення ОІД.");
    //     return;
    // }
    // formData.append("unit_for_new_oid", unitId); // Ім'я поля згідно views.py ajax_create_oid_view

    try {
        const response = await fetch(form.action, {
            // Використовуємо action з HTML форми
            method: "POST",
            body: formData,
            headers: {
                "X-CSRFToken": formData.get("csrfmiddlewaretoken"), // Переконайтеся, що CSRF токен присутній у формі
                "X-Requested-With": "XMLHttpRequest", // Часто потрібно для Django AJAX
            },
        });
        const data = await response.json();

        if (data.status === "success" && data.oid_id && data.oid_name) {
            alert("✅ ОІД успішно створено!");
            form.reset();
            closeOidAside();

            if (targetOidSelect) {
                const newOptionData = {
                    value: data.oid_id,
                    text: data.oid_name, // data.oid_name - це str(oid) з сервера
                };

                // Якщо Tom Select ініціалізований на targetOidSelect
                if (targetOidSelect.tomselect) {
                    targetOidSelect.tomselect.addOption(newOptionData);
                    targetOidSelect.tomselect.addItem(data.oid_id);
                    // targetOidSelect.tomselect.refreshOptions(false); // Може не знадобитися, якщо addOption оновлює кеш
                } else {
                    // Стандартний select
                    const optionElement = new Option(newOptionData.text, newOptionData.value, false, true); // selected = true
                    targetOidSelect.appendChild(optionElement);
                    targetOidSelect.value = newOptionData.value; // Встановлюємо значення
                }
            }

            // TODO: Оновлення інших select-ів OID на сторінці, якщо вони залежать від тієї ж ВЧ.
            // Це може вимагати більш складної логіки або сповіщення інших компонентів про новий ОІД.
            // Наприклад, можна пройтися по всіх select-ах для ОІД і, якщо вони не мають нового значення,
            // викликати для них метод TomSelect для оновлення джерела даних (якщо вони завантажуються через AJAX)
            // або просто додати нову опцію, якщо вони статичні.
        } else if (data.errors) {
            let errorMessages = "Помилка валідації:\n";
            for (const field in data.errors) {
                errorMessages += `${field}: ${data.errors[field].join(", ")}\n`;
            }
            alert("❌ " + errorMessages);
        } else {
            alert("❌ Відбулася невідома помилка при створенні ОІД.");
        }
    } catch (err) {
        console.error("❌ Помилка зв'язку з сервером при створенні ОІД:", err);
        alert("⚠️ Помилка зв’язку з сервером. Перевірте консоль для деталей.");
    }
}

/**
 * Ініціалізує логіку для бічного вікна створення ОІД.
 */
function setupOidAsideLogic() {
    const aside = document.querySelector(SELECTORS.OID_ASIDE);
    if (!aside) return;

    const closeButton = aside.querySelector(SELECTORS.OID_ASIDE_CLOSE_BUTTON);
    const overlay = document.querySelector(SELECTORS.OVERLAY);
    const oidCreateForm = aside.querySelector(SELECTORS.OID_CREATE_FORM);

    if (closeButton) {
        closeButton.addEventListener("click", closeOidAside);
    }
    if (overlay) {
        overlay.addEventListener("click", closeOidAside); // Закриття по кліку на оверлей
    }
    if (oidCreateForm) {
        oidCreateForm.addEventListener("submit", handleOidCreateFormSubmit);
    }

    // Глобальний слухач для кнопок "Додати ОІД" (делегування подій)
    // Це дозволяє кнопкам, доданим динамічно (наприклад, у формсетах), також працювати.
    document.body.addEventListener("click", function (event) {
        if (event.target.closest(SELECTORS.ADD_OID_BUTTON)) {
            openOidAside(event);
        }
    });
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

    // Ініціалізація логіки aside для створення ОІД
    setupOidAsideLogic(); // Ця функція тепер також налаштовує глобальний слухач для кнопок .add-oid-button

    // TODO: Тут буде місце для ініціалізації Tom Select для всіх потрібних полів <select>
    // Наприклад:
    // document.querySelectorAll('select.tomselect-field').forEach(selectEl => {
    //   new TomSelect(selectEl, { /* options */ });
    // });
    // Або виклик більш специфічної функції, яка знаходить і налаштовує Tom Select.
});
