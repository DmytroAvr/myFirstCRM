// oids/static/oids/js/dynamic_filters.js

// Переконайтеся, що SELECTORS доступні. Якщо main.js завантажується раніше, вони будуть.
// В іншому випадку, їх можна перенести сюди або визначити глобально.
// Для простоти, припустимо, що main.js завантажується раніше і SELECTORS вже визначені,
// або ж продублюємо ключові селектори тут, якщо цей файл може завантажуватися незалежно.
const FILTER_SELECTORS = {
    UNIT_SELECT: '#id_unit',
    UNITS_MULTI_SELECT: '#id_units', // Для MultiSelectField Units
    OID_SELECT: '#id_oid',
    OIDS_MULTI_SELECT: '#id_oids', // Для MultiSelectField OIDs
    WORK_REQUEST_SELECT: '#id_work_requests', // Для WorkRequest
    WORK_REQUEST_ITEM_SELECT: '#id_work_request_item', // Приклад для WorkRequestItem
    DOCUMENT_FORM_CLASS: '.document-form', // Клас для формсетної форми
    FORMSET_CONTAINER: '#formset', // Контейнер формсету
    // Інші селектори, які можуть знадобитися для фільтрації OID-ів, документів тощо.
};

// =====================================================================================================
// Функції для динамічної фільтрації Select2 полів
// =====================================================================================================

/**
 * Завантажує опції для цільового select2 поля через AJAX.
 * @param {jQuery} $targetSelect - jQuery об'єкт цільового select поля.
 * @param {Array|string} sourceValue - Значення (або масив значень) з вихідного select поля.
 * @param {Object} config - Об'єкт конфігурації фільтра.
 */
function loadSelectOptions($targetSelect, sourceValue, config) {
    const { url, paramName, placeholder, transformItem } = config;

    // Очищаємо цільовий select і встановлюємо статус "завантаження"
    $targetSelect.prop('disabled', true)
                 .empty()
                 .append($('<option></option>').text(placeholder.loading || 'Завантаження...'));

    const params = new URLSearchParams();
    if (Array.isArray(sourceValue)) {
        // Якщо вихідне поле multi-select, додаємо кожне значення
        sourceValue.forEach(val => params.append(paramName, val));
    } else {
        params.append(paramName, sourceValue);
    }

    $.getJSON(url + '?' + params.toString(), function (data) {
        $targetSelect.prop('disabled', false).empty();

        // Додаємо опцію за замовчуванням (якщо потрібна)
        $targetSelect.append($('<option></option>').val('').text(placeholder.default || 'Оберіть значення...'));

        data.forEach(item => {
            const option = transformItem(item);
            $targetSelect.append($('<option></option>').val(option.value).text(option.label));
        });

        // Триггеримо зміну для Select2, щоб оновити відображення
        $targetSelect.trigger('change');
        // Якщо Select2 ініціалізовано, потрібно оновити його відображення
        if ($targetSelect.data('select2')) {
            $targetSelect.select2('open'); // Закриваємо/відкриваємо, щоб оновити
            $targetSelect.select2('close'); // Закриваємо, щоб не залишилося відкритим
        }

    }).fail(function() {
        console.error(`Помилка завантаження даних з ${url}`);
        $targetSelect.prop('disabled', false).empty().append($('<option></option>').val('').text(placeholder.error || 'Помилка завантаження.'));
        $targetSelect.trigger('change');
    });
}

/**
 * Універсальна функція для налаштування динамічної фільтрації між select полями.
 * Підтримує як статичні, так і формсетні поля.
 * @param {Object} config - Об'єкт конфігурації.
 * @param {string} config.sourceSelectId - ID або клас вихідного select поля (e.g., '#id_unit', '.unit-select').
 * @param {string} config.targetSelectBaseName - Базове ім'я або ID для цільового select поля (e.g., 'oid', '#id_oid').
 * Якщо це формсет, то це буде 'oid'. Якщо статичне поле, '#id_oid'.
 * @param {string} config.url - URL для AJAX-запиту, який повертає дані для цільового поля.
 * @param {string} config.paramName - Ім'я параметра, що передається в URL для фільтрації (e.g., 'unit', 'units[]', 'oid_id').
 * @param {Object} config.placeholder - Об'єкт з текстами плейсхолдерів ({ default: '...', loading: '...', error: '...' }).
 * @param {Function} config.transformItem - Функція, яка перетворює кожен елемент відповіді AJAX у { value: ..., label: ... }.
 * За замовчуванням: item => ({ value: item.id, label: item.name }).
 * @param {string} [config.formPrefix='form'] - Префікс формсету, якщо цільове поле знаходиться у формсеті.
 * @param {string} [config.formClass='.document-form'] - Клас формсетної форми, якщо цільове поле знаходиться у формсеті.
 * @param {string[]} [config.clearTargets=[]] - Масив ID/базових імен полів, які потрібно очистити при зміні `sourceSelectId`.
 * Це дозволяє очищати ланцюжки фільтрації (A -> B -> C: при зміні A очистити B і C).
 * @param {boolean} [config.isReverse=false] - Якщо true, це поле є "зворотним" фільтром (наприклад, WorkRequest).
 * Його вибір повинен оновити батьківські поля.
 * @param {string} [config.parentUnitSelectId] - ID select поля Unit для WorkRequest.
 * @param {string} [config.parentOidSelectId] - ID select поля OID для WorkRequest.
 */
function setupDynamicFilter(config) {
    const {
        sourceSelectId,
        targetSelectBaseName, // Може бути ID або базовим ім'ям для формсету
        url,
        paramName,
        placeholder,
        transformItem = item => ({ value: item.id, label: item.name }),
        formPrefix = 'form',
        formClass = FILTER_SELECTORS.DOCUMENT_FORM_CLASS,
        clearTargets = [], // Поля, які потрібно очистити далі по ланцюжку
        isReverse = false, // Для WorkRequest -> OID -> Unit
        parentUnitSelectId,
        parentOidSelectId
    } = config;

    const $sourceSelect = $(sourceSelectId);

    // Функція для очищення залежних полів
    function clearDependentFields($currentSourceSelect) {
        clearTargets.forEach(targetName => {
            // Якщо це формсетне поле
            if ($currentSourceSelect.closest(formClass).length) {
                const formIndex = $currentSourceSelect.closest(formClass).data('form-index');
                const $target = $(`#id_${formPrefix}-${formIndex}-${targetName}`);
                if ($target.length && $target.data('select2')) {
                    $target.val(null).trigger('change').empty().append($('<option></option>').val('').text(placeholder.default || 'Оберіть значення...'));
                }
            } else { // Якщо це статичне поле
                const $target = $(`#id_${targetName}`);
                if ($target.length && $target.data('select2')) {
                    $target.val(null).trigger('change').empty().append($('<option></option>').val('').text(placeholder.default || 'Оберіть значення...'));
                }
            }
        });
    }

    // Обробник для зміни вихідного поля
    $sourceSelect.on('change', function () {
        const sourceValue = $(this).val();

        // Очищаємо залежні поля
        clearDependentFields($(this));

        if (!sourceValue || (Array.isArray(sourceValue) && sourceValue.length === 0)) {
            // Якщо значення немає, очищаємо цільове поле
            const $targetSelect = isFormsetField(targetSelectBaseName) ? $(`#id_${formPrefix}-0-${targetSelectBaseName}`) : $(targetSelectBaseName);
            if ($targetSelect.length) {
                $targetSelect.empty().append($('<option></option>').val('').text(placeholder.default || 'Оберіть значення...'));
                $targetSelect.trigger('change');
            }
            return;
        }

        if (isReverse) {
            // Логіка для зворотного фільтра (наприклад, WorkRequest -> OID -> Unit)
            // Коли WorkRequest обрано, потрібно отримати його OID та Unit і встановити їх.
            // Це вимагає AJAX-запиту, який поверне { oid_id: ..., unit_id: ... }
            $.getJSON(url + '?' + paramName + '=' + sourceValue, function (data) {
                if (data.oid_id && $(parentOidSelectId).length) {
                    $(parentOidSelectId).val(data.oid_id).trigger('change');
                    // Додатково: потрібно оновити Select2 відображення
                    if ($(parentOidSelectId).data('select2')) {
                        $(parentOidSelectId).select2('open'); // Закриваємо/відкриваємо, щоб оновити
                        $(parentOidSelectId).select2('close');
                    }
                }
                if (data.unit_id && $(parentUnitSelectId).length) {
                    $(parentUnitSelectId).val(data.unit_id).trigger('change');
                     if ($(parentUnitSelectId).data('select2')) {
                        $(parentUnitSelectId).select2('open'); // Закриваємо/відкриваємо, щоб оновити
                        $(parentUnitSelectId).select2('close');
                    }
                }
            }).fail(function() {
                console.error(`Помилка завантаження батьківських даних для ${sourceSelectId}`);
            });

        } else {
            // Логіка для звичайної фільтрації (зверху вниз)
            // Визначаємо, чи є цільове поле формсетним чи статичним
            if ($(this).closest(formClass).length) { // Якщо вихідне поле знаходиться у формсеті
                const formIndex = $(this).closest(formClass).data('form-index');
                const $targetSelect = $(`#id_${formPrefix}-${formIndex}-${targetSelectBaseName}`);
                if ($targetSelect.length) {
                    loadSelectOptions($targetSelect, sourceValue, config);
                }
            } else { // Якщо вихідне поле статичне
                // Якщо цільове поле - формсетний елемент, потрібно оновити всі такі елементи
                if (targetSelectBaseName.startsWith('form-')) { // heuristic for formset
                    $(formClass).each(function(index) {
                        const $targetSelect = $(this).find(`#id_${formPrefix}-${index}-${targetSelectBaseName.replace(`${formPrefix}-`, '').replace(`-${formPrefix}`, '')}`);
                        if ($targetSelect.length) {
                            loadSelectOptions($targetSelect, sourceValue, config);
                        }
                    });
                } else if (targetSelectBaseName === 'oid' && $(FILTER_SELECTORS.FORMSET_CONTAINER).length) {
                    // Це випадок, коли id_unit фільтрує id_oid у всіх формсетах
                    // Перевіряємо, чи є id_unit (один) і чи є формсет з OID.
                    $(FILTER_SELECTORS.FORMSET_CONTAINER).find(`select[name$="-oid"]`).each(function() {
                        const $targetSelect = $(this);
                        loadSelectOptions($targetSelect, sourceValue, config);
                    });
                } else { // Якщо цільове поле статичне (не в формсеті)
                    const $targetSelect = $(targetSelectBaseName); // Вже ID
                    if ($targetSelect.length) {
                        loadSelectOptions($targetSelect, sourceValue, config);
                    }
                }
            }
        }
    });
}

/**
 * Перевіряє, чи є елемент частиною формсету.
 * @param {string} selector - Селектор для перевірки (наприклад, 'oid').
 * @returns {boolean}
 */
function isFormsetField(selector) {
    // Дуже проста евристика: якщо селектор є просто ім'ям поля (без #id_), припускаємо формсет.
    // Або ж, якщо це конкретний ID, перевіряємо його наявність.
    return !selector.startsWith('#');
}


/**
 * Ініціалізує всі динамічні фільтри на сторінці.
 */
function initializeDynamicFilters() {
    // Перевіряємо наявність jQuery та Select2
    if (typeof jQuery === 'undefined' || typeof $.fn.select2 === 'undefined') {
        console.warn("jQuery або Select2 не завантажено. Динамічні фільтри не будуть ініціалізовані.");
        return;
    }

    // --- Конфігурація фільтрів ---
    // Якщо ви хочете додати новий ланцюжок фільтрації, просто додайте новий об'єкт до цього масиву.
    const filterConfigurations = [
        // F1: Unit (одинарний) -> OID (одинарний)
        {
            sourceSelectId: FILTER_SELECTORS.UNIT_SELECT,
            targetSelectBaseName: FILTER_SELECTORS.OID_SELECT, // Це ID, бо OID не в формсеті тут
            url: '/oids/ajax/load-oids-for-unit/',
            paramName: 'unit',
            placeholder: { default: 'Оберіть ОІД', loading: 'Завантаження ОІД...' },
            clearTargets: ['oid', 'work_requests'] // При зміні Unit очистити OID та WorkRequests
        },
        // F2: Units (MultiSelect) -> OIDs (MultiSelect)
        {
            sourceSelectId: FILTER_SELECTORS.UNITS_MULTI_SELECT,
            targetSelectBaseName: FILTER_SELECTORS.OIDS_MULTI_SELECT,
            url: '/oids/ajax/load-oids-for-units/',
            paramName: 'units[]', // Масив значень для MultiSelectField
            placeholder: { default: 'Оберіть ОІД(и)', loading: 'Завантаження ОІД(ів)...' },
            clearTargets: ['oids', 'work_requests']
        },
        // F3: OID (одинарний) -> WorkRequests (одинарний/MultiSelect)
        {
            sourceSelectId: FILTER_SELECTORS.OID_SELECT,
            targetSelectBaseName: FILTER_SELECTORS.WORK_REQUEST_SELECT,
            url: '/oids/ajax/get-requests-by-oid/',
            paramName: 'oid_id',
            placeholder: { default: 'Оберіть заявку', loading: 'Завантаження заявок...' },
            transformItem: item => ({ value: item.id, label: `${item.incoming_number || item.id} — ${item.incoming_date || ''}` }),
            clearTargets: ['work_requests']
        },
        // F4: OIDs (MultiSelect) -> WorkRequests (одинарний/MultiSelect)
        {
            sourceSelectId: FILTER_SELECTORS.OIDS_MULTI_SELECT,
            targetSelectBaseName: FILTER_SELECTORS.WORK_REQUEST_SELECT,
            url: '/oids/ajax/get-requests-by-oids/',
            paramName: 'oid_ids', // Масив значень для MultiSelectField
            placeholder: { default: 'Оберіть заявку', loading: 'Завантаження заявок...' },
            transformItem: item => ({ value: item.id, label: `${item.incoming_number || item.id} — ${item.incoming_date || ''}` }),
            clearTargets: ['work_requests']
        },
        // F5: Unit (основний) -> OID у формсеті (.document-form)
        {
            sourceSelectId: FILTER_SELECTORS.UNIT_SELECT,
            targetSelectBaseName: 'oid', // Це базове ім'я для формсету: form-X-oid
            url: '/oids/ajax/load-oids-for-unit/',
            paramName: 'unit',
            placeholder: { default: 'Оберіть ОІД', loading: 'Оновлення ОІД...' },
            formPrefix: 'form',
            formClass: FILTER_SELECTORS.DOCUMENT_FORM_CLASS,
            clearTargets: ['oid'] // Це очистить OID в кожній формі
        },
        // F6: WorkRequest (зворотна фільтрація) -> OID -> Unit
        // Цей сценарій складніший, оскільки потрібно оновити батьківські поля.
        // Він вимагає, щоб AJAX-ендпоінт повертав ID батьківських об'єктів.
        // ПРИКЛАД: якщо WorkRequest може мати тільки один OID, а OID - один Unit.
        {
            sourceSelectId: FILTER_SELECTORS.WORK_REQUEST_SELECT, // ID для WorkRequest select
            targetSelectBaseName: null, // Немає прямого "цільового" поля для завантаження
            url: '/oids/ajax/get-work-request-details/', // URL, який поверне { oid_id, unit_id }
            paramName: 'request_id',
            placeholder: { default: 'Завантаження деталей...', loading: 'Завантаження деталей...' },
            transformItem: item => ({ value: item.id, label: item.id }), // Не використовується для зворотнього
            isReverse: true,
            parentOidSelectId: FILTER_SELECTORS.OID_SELECT, // ID поля OID, яке потрібно оновити
            parentUnitSelectId: FILTER_SELECTORS.UNIT_SELECT, // ID поля Unit, яке потрібно оновити
            clearTargets: ['oid', 'unit'] // Очистити ці поля перед завантаженням нових значень
        },
        // F7: OID -> TechnicalTask (якщо TechnicalTask залежить від OID)
        {
            sourceSelectId: FILTER_SELECTORS.OID_SELECT,
            targetSelectBaseName: '#id_technical_tasks', // Припускаємо ID для поля TechnicalTask
            url: '/oids/ajax/load-technical-tasks-for-oid/', // Новий AJAX-ендпоінт
            paramName: 'oid_id',
            placeholder: { default: 'Оберіть технічне завдання', loading: 'Завантаження ТЗ...' },
            transformItem: item => ({ value: item.id, label: `${item.input_number} — ${item.input_date}` }),
            clearTargets: ['technical_tasks']
        }
    ];

    filterConfigurations.forEach(config => {
        // Перевіряємо, чи існує вихідний елемент на сторінці перед налаштуванням фільтра
        if ($(config.sourceSelectId).length) {
            setupDynamicFilter(config);
        } else {
            console.log(`Вихідний елемент фільтра не знайдено: ${config.sourceSelectId}. Пропускаю налаштування.`);
        }
    });

    // Додатково, для формсетів: обробник для нових форм, що додаються динамічно
    const formsetContainer = $(FILTER_SELECTORS.FORMSET_CONTAINER);
    if (formsetContainer.length) {
        formsetContainer.on('DOMNodeInserted', function(e) {
            if ($(e.target).is(FILTER_SELECTORS.DOCUMENT_FORM_CLASS)) {
                // Нова форма додана, ініціалізуємо фільтри для неї.
                // Знаходимо всі конфігурації, які стосуються формсету
                filterConfigurations.filter(cfg => cfg.formClass === FILTER_SELECTORS.DOCUMENT_FORM_CLASS).forEach(cfg => {
                    // Для кожної конфігурації, що стосується формсету,
                    // потрібно знайти вихідне поле в новій формі (якщо воно є)
                    // і прив'язати до нього логіку.
                    // У нашому випадку, OID у формсеті залежить від Unit (статичного),
                    // тому зміна Unit вже оновлює всі OID-и.
                    // Але якщо б у вас був фільтр всередині формсету (напр., DocumentType -> DocumentSubtype у тій же формі),
                    // то потрібно було б ініціювати його тут.
                    // Наразі, логіка в `setupDynamicFilter` вже обробляє це:
                    // `if (targetSelectBaseName === 'oid' && $(FILTER_SELECTORS.FORMSET_CONTAINER).length)`
                    // буде перевиконана при зміні #id_unit і оновить всі OID-и формсету.
                });
            }
        });
    }


    // Ініціалізувати початковий стан Select2, якщо вони не були ініціалізовані раніше
    // (наприклад, Select2, які залежать від інших полів, і які повинні бути порожніми спочатку)
    // Це може бути зроблено тут або в `select2-init.js`.
    // Якщо #id_unit має значення при завантаженні, потрібно тригернути його зміну,
    // щоб завантажити залежні OID.
    const $unitSelect = $(FILTER_SELECTORS.UNIT_SELECT);
    if ($unitSelect.length && $unitSelect.val()) {
        $unitSelect.trigger('change');
    }

    const $unitsMultiSelect = $(FILTER_SELECTORS.UNITS_MULTI_SELECT);
    if ($unitsMultiSelect.length && $unitsMultiSelect.val() && $unitsMultiSelect.val().length > 0) {
        $unitsMultiSelect.trigger('change');
    }

    // Тригер для всіх початкових фільтрів, якщо є початкові значення
    filterConfigurations.forEach(config => {
        const $source = $(config.sourceSelectId);
        if ($source.length) {
            // Для Select2, яке може мати початкове значення з бекенду
            // Ми повинні тригернути 'change' вручну, щоб завантажити залежні поля
            // лише якщо воно має початкове обране значення.
            // Без перевірки на .val() ми б завантажували порожні списки.
            if ($source.val() && (!Array.isArray($source.val()) || $source.val().length > 0)) {
                $source.trigger('change');
            }
        }
    });

}

// Запускаємо ініціалізацію динамічних фільтрів, коли DOM готовий
// Ця функція буде викликана з main.js, тому тут не потрібен DOMContentLoaded.
// initializeDynamicFilters(); // Це буде викликано з main.js