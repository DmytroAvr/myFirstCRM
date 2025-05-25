// oids/static/oids/js/filtering_dynamic.js

// Об'єкт з селекторами для зручного доступу
const FILTER_SELECTORS = {
    UNIT_FILTER_MAIN_DASHBOARD: '#id_unit_filter', // Select для ВЧ на головній панелі
    // Контейнери для списків ОІД на головній панелі
    OIDS_CREATING_LIST_CONTAINER: '#oidsCreatingList',
    OIDS_ACTIVE_LIST_CONTAINER: '#oidsActiveList',
    OIDS_CANCELLED_LIST_CONTAINER: '#oidsCancelledList',
    OIDS_LOADING_INDICATOR: '#loadingOidsIndicator',
    SELECTED_UNIT_DISPLAY_SPAN: '#selectedUnitForOidDisplay',

    // Селектори для форм (приклади, адаптуй за потребою)
    UNIT_SELECT_IN_FORM: '#id_unit', // Якщо є окремий select ВЧ у формах
    OID_SELECT_IN_FORM: '#id_oid',   // Якщо є окремий select ОІД у формах
    // ... інші селектори для форм, якщо потрібно
};

/**
 * Завантажує опції для одного цільового select2 поля через AJAX.
 * Використовується для стандартних каскадних select-ів у формах.
 * @param {jQuery} $targetSelect - jQuery об'єкт цільового select поля.
 * @param {Array|string} sourceValue - Значення (або масив значень) з вихідного select поля.
 * @param {Object} config - Об'єкт конфігурації фільтра.
 */
function loadSingleSelectOptions($targetSelect, sourceValue, config) {
    const { url, paramName, placeholder, transformItem = item => ({ value: item.id, label: item.name }) } = config;

    $targetSelect.prop('disabled', true)
                 .empty()
                 .append($('<option></option>').val('').text(placeholder.loading || 'Завантаження...'));

    const params = new URLSearchParams();
    if (Array.isArray(sourceValue)) {
        sourceValue.forEach(val => params.append(paramName, val));
    } else if (sourceValue) {
        params.append(paramName, sourceValue);
    } else { // Якщо sourceValue порожній, просто очищаємо і ставимо дефолтний плейсхолдер
        $targetSelect.prop('disabled', false).empty()
                     .append($('<option></option>').val('').prop('disabled', true).prop('selected', true).text(placeholder.default || 'Оберіть значення...'))
                     .trigger('change');
        return;
    }

    $.getJSON(url + '?' + params.toString(), function (data) {
        $targetSelect.prop('disabled', false).empty();
        $targetSelect.append($('<option></option>').val('').prop('disabled', true).prop('selected', true).text(placeholder.default || 'Оберіть значення...'));

        if (data && data.length > 0) {
            data.forEach(item => {
                const option = transformItem(item);
                $targetSelect.append($('<option></option>').val(option.value).text(option.label));
            });
        } else {
            // Можна додати опцію "Нічого не знайдено"
             $targetSelect.append($('<option></option>').val('').text(placeholder.empty || 'Нічого не знайдено'));
        }
        $targetSelect.trigger('change'); // Важливо для Select2 та інших слухачів
    }).fail(function() {
        console.error(`Помилка завантаження даних з ${url} для ${$targetSelect.attr('id')}`);
        $targetSelect.prop('disabled', false).empty()
                     .append($('<option></option>').val('').text(placeholder.error || 'Помилка завантаження.'))
                     .trigger('change');
    });
}


/**
 * Оновлює списки ОІД на головній панелі.
 * @param {Object} data - Дані з AJAX-відповіді (структура: { creating: [], active: [], cancelled: [] }).
 * @param {Object} selectors - Об'єкт з селекторами для контейнерів списків ОІД.
 */
function updateOidListsOnDashboard(data, selectors) {
    const { OIDS_CREATING_LIST_CONTAINER, OIDS_ACTIVE_LIST_CONTAINER, OIDS_CANCELLED_LIST_CONTAINER } = selectors;
    const $creatingList = $(OIDS_CREATING_LIST_CONTAINER);
    const $activeList = $(OIDS_ACTIVE_LIST_CONTAINER);
    const $cancelledList = $(OIDS_CANCELLED_LIST_CONTAINER);

    const lists = {
        creating: $creatingList,
        active: $activeList,
        cancelled: $cancelledList
    };

    for (const key in lists) {
        lists[key].empty(); // Очищаємо попередні елементи
    }
    
    function formatDate(dateString) {
        if (!dateString) return '';
        // Проста перевірка формату YYYY-MM-DD
        if (!/^\d{4}-\d{2}-\d{2}$/.test(dateString)) return dateString; // Повертаємо як є, якщо формат не той
        const parts = dateString.split('-');
        return `${parts[2]}.${parts[1]}.${parts[0]}`; // dd.mm.yyyy
    }

    function populateList(listElement, oids, categoryName) {
        if (!oids || oids.length === 0) {
            listElement.append('<li>Немає ОІД у цій категорії.</li>');
            return;
        }
        oids.forEach(oid => {
            let expirationHtml = '';
            if (categoryName === 'active') {
                expirationHtml = '<div class="expirations" style="font-size: 0.8em; color: grey; margin-left: 10px;">';
                if (oid.ik_expiration_date) expirationHtml += `ІК до: ${formatDate(oid.ik_expiration_date)}<br>`;
                if (oid.attestation_expiration_date) expirationHtml += `Атестація до: ${formatDate(oid.attestation_expiration_date)}<br>`;
                if (oid.prescription_expiration_date) expirationHtml += `Припис до: ${formatDate(oid.prescription_expiration_date)}`;
                expirationHtml += '</div>';
            }
            // Переконайся, що oid.detail_url передається з AJAX view
            const listItemHtml = `
                <li class="oid-item" style="display: flex; justify-content: space-between; align-items: center; padding: 5px 0; border-bottom: 1px dashed #eee;">
                    <a href="${oid.detail_url}" style="flex-grow: 1;">${oid.cipher} - ${oid.full_name} (${oid.oid_type_display})</a>
                    <span style="margin-left: 10px;">(${oid.status_display})</span>
                    ${expirationHtml}
                </li>`;
            listElement.append(listItemHtml);
        });
    }

    populateList(lists.creating, data.creating, 'creating');
    populateList(lists.active, data.active, 'active');
    populateList(lists.cancelled, data.cancelled, 'cancelled');
}


/**
 * Універсальна функція для налаштування динамічної фільтрації.
 * @param {Object} config - Об'єкт конфігурації.
 * @param {string} config.sourceSelectSelector - Селектор вихідного select поля.
 * @param {string} [config.targetSelectSelector] - Селектор цільового select поля (для loadSingleSelectOptions).
 * @param {string} config.url - URL для AJAX-запиту.
 * @param {string} config.paramName - Ім'я параметра для URL.
 * @param {Object} [config.placeholder] - Тексти плейсхолдерів для targetSelectSelector.
 * @param {Function} [config.transformItem] - Функція перетворення для targetSelectSelector.
 * @param {Function} [config.customListUpdater] - Функція для оновлення кастомних списків (наприклад, ОІД на панелі).
 * @param {Object} [config.customListUpdaterSelectors] - Селектори для customListUpdater.
 * @param {string[]} [config.clearTargetsSelectors=[]] - Масив селекторів полів, які потрібно очистити.
 */
function setupDynamicFilter(config) {
    const {
        sourceSelectSelector,
        // targetSelectSelector, // Не використовується для dashboard config
        paramName,
        // placeholder, // Плейсхолдери для списків обробляються окремо
        customListUpdater,
        clearTargetsSelectors = []
    } = config;

    const $sourceSelect = $(sourceSelectSelector);

    // URL тепер передається напряму в config з initializeDynamicFilters
    const ajaxUrl = config.url; 

    if (!$sourceSelect.length) {
        // console.warn(`Вихідний елемент фільтра не знайдено: ${sourceSelectSelector}`);
        return;
    }
    if (!ajaxUrl) { // Ця перевірка тепер має бути в initializeDynamicFilters
        console.error(`КРИТИЧНО: URL не передано в setupDynamicFilter для ${sourceSelectSelector}`);
        return;
    }

    // ... (решта коду setupDynamicFilter як у попередній відповіді, 
    //      використовуючи 'ajaxUrl' замість '$sourceSelect.data('ajax-url')' або 'url' з config)
    //      Наприклад, $.ajax({ url: ajaxUrl, ... });
    //      Важливо: $sourceSelect.on('change', function () { ... });
    //      І початковий тригер: if ($sourceSelect.val() && $sourceSelect.val() !== '') { ... $sourceSelect.trigger('change'); ... }
}


function initializeDynamicFilters() {
    console.log("Ініціалізація jQuery динамічних фільтрів (DEBUG URL)...");

    const filterConfigurations = [
        {
            sourceSelectSelector: FILTER_SELECTORS.UNIT_FILTER_MAIN_DASHBOARD, // '#id_unit_filter'
            paramName: 'unit_id',
            customListUpdater: updateOidListsOnDashboard,
            // URL буде додано нижче з data-атрибута
            clearTargetsSelectors: [
                FILTER_SELECTORS.OIDS_CREATING_LIST_CONTAINER,
                FILTER_SELECTORS.OIDS_ACTIVE_LIST_CONTAINER,
                FILTER_SELECTORS.OIDS_CANCELLED_LIST_CONTAINER
            ]
        }
        // ... інші твої конфігурації для форм, якщо є ...
    ];

    filterConfigurations.forEach(config => {
        const $sourceElement = $(config.sourceSelectSelector);
        if ($sourceElement.length) {
            const ajaxUrlFromDataAttr = $sourceElement.data('ajax-url');
            console.log(`Для селектора "<span class="math-inline">\{config\.sourceSelectSelector\}", знайдено data\-ajax\-url\: "</span>{ajaxUrlFromDataAttr}"`);

            if (!ajaxUrlFromDataAttr) {
                console.warn(`!!! НЕ ЗНАЙДЕНО data-ajax-url для "${config.sourceSelectSelector}". Фільтр НЕ буде налаштовано для цього елемента.`);
                return; // Пропускаємо цю конфігурацію, якщо URL не знайдено
            }

            config.url = ajaxUrlFromDataAttr; // Встановлюємо URL в об'єкт конфігурації

            console.log(`Налаштовую фільтр для: "<span class="math-inline">\{config\.sourceSelectSelector\}" з URL\: "</span>{config.url}"`);
            setupDynamicFilter(config); // Передаємо оновлений config
        } else {
            // console.warn(`Вихідний елемент фільтра не знайдено: ${config.sourceSelectSelector}`);
        }
    });
}


/**
 * Ініціалізує всі динамічні фільтри на сторінці.
 */
function initializeDynamicFilters() {
    console.log("Ініціалізація jQuery динамічних фільтрів...");

    const filterConfigurations = [
        // Фільтр для головної панелі: ВЧ -> Списки ОІД
        {
            sourceSelectSelector: FILTER_SELECTORS.UNIT_FILTER_MAIN_DASHBOARD, // Наприклад, '#id_unit_filter'
            // targetSelectSelector тут не потрібен, бо оновлюємо кастомні списки
            url: $(FILTER_SELECTORS.UNIT_FILTER_MAIN_DASHBOARD).data('ajax-url-categorized'), // URL беремо з data-атрибута
            paramName: 'unit_id',
            customListUpdater: updateOidListsOnDashboard, // Функція для оновлення DOM
            // customListUpdaterSelectors передавати не потрібно, бо вони використовуються всередині updateOidListsOnDashboard
            // але якщо б вони були потрібні ззовні, то:
            // customListUpdaterSelectors: { 
            //     OIDS_CREATING_LIST_CONTAINER: FILTER_SELECTORS.OIDS_CREATING_LIST_CONTAINER,
            //     OIDS_ACTIVE_LIST_CONTAINER: FILTER_SELECTORS.OIDS_ACTIVE_LIST_CONTAINER,
            //     OIDS_CANCELLED_LIST_CONTAINER: FILTER_SELECTORS.OIDS_CANCELLED_LIST_CONTAINER
            // },
            clearTargetsSelectors: [ // Що очищати при зміні ВЧ
                FILTER_SELECTORS.OIDS_CREATING_LIST_CONTAINER,
                FILTER_SELECTORS.OIDS_ACTIVE_LIST_CONTAINER,
                FILTER_SELECTORS.OIDS_CANCELLED_LIST_CONTAINER
            ]
        },
        
        // Приклад фільтра для форми: Unit (звичайний select) -> OID (звичайний select)
        // Цей фільтр буде працювати, якщо у вас є форма з полями #id_unit та #id_oid
        {
            sourceSelectSelector: FILTER_SELECTORS.UNIT_SELECT_IN_FORM, // Наприклад, '#id_unit' у формі
            targetSelectSelector: FILTER_SELECTORS.OID_SELECT_IN_FORM,   // Наприклад, '#id_oid' у формі
            url: $(FILTER_SELECTORS.UNIT_SELECT_IN_FORM).data('ajax-url-oids'), // data-ajax-url-oids="{% url 'oids:ajax_load_oids_for_unit' %}"
            paramName: 'unit_id', // Або 'unit' залежно від вашого AJAX view
            placeholder: { default: 'Спочатку оберіть ВЧ', loading: 'Завантаження ОІД...', error: 'Помилка', empty: 'Немає ОІД для цієї ВЧ'},
            transformItem: item => ({ value: item.id, label: item.name }), // name - це те, що повертає ajax_load_oids_for_unit
            clearTargetsSelectors: [FILTER_SELECTORS.OID_SELECT_IN_FORM] // Очищати ОІД при зміні ВЧ
        }
        // Додайте сюди інші конфігурації для форм, якщо потрібно
    ];

    filterConfigurations.forEach(config => {
        const $sourceElement = $(config.sourceSelectSelector);
        if ($sourceElement.length) {
            // Якщо URL не був встановлений з data-атрибуту і містить Django тег,
            // це буде виявлено в setupDynamicFilter і виведено попередження.
            // Якщо URL береться з data-атрибута, він вже буде коректним.
            if (!config.url) { // Якщо URL не був визначений з data-атрибута в конфігу
                 if (config.customListUpdater) { // Для головної панелі
                    config.url = $sourceElement.data('ajax-url-categorized');
                 } else if (config.targetSelectSelector) { // Для звичайних select
                    config.url = $sourceElement.data('ajax-url-oids'); // Або інший відповідний data-атрибут
                 }
            }
            console.log(`Налаштовую фільтр для: ${config.sourceSelectSelector} з URL: ${config.url}`);
            setupDynamicFilter(config);
        } else {
            // console.warn(`Вихідний елемент фільтра не знайдено для конфігурації: ${config.sourceSelectSelector}`);
        }
    });
}

// Виклик initializeDynamicFilters() має відбуватися після того, як DOM завантажено
// і після того, як Select2 ініціалізував свої поля.
// Це зазвичай робиться в $(document).ready() у вашому головному JS файлі (main.js)
// або в кінці base.html, після підключення всіх скриптів.

// Якщо цей файл підключається останнім і jQuery вже доступний:
// $(document).ready(function() {
//     if (typeof initializeDynamicFilters === 'function') {
//         initializeDynamicFilters();
//     }
// });
// Але краще керувати порядком виклику з main.js або base.html