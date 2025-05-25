// oids/static/oids/js/select2-init.js
// Це повинно бути глобальною функцією або об'єктом, щоб її можна було викликати з main.js

function initSelect2Fields(scope = document) {
    // Ініціалізуйте Select2 для всіх елементів з класом '.select2' у межах `scope`
    // або тільки для елементів, які ще не ініціалізовані.
    $(scope).find('.select2').each(function() {
        if (!$(this).data('select2')) { // Перевірка, щоб не ініціалізувати двічі
            $(this).select2({
                width: '100%',
                placeholder: 'Оберіть значення...',
                allowClear: true,
                language: 'uk', // або 'ru', 'en'
                // ... Ваші ajax налаштування тут для полів, які потребують їх
                // Приклад AJAX для OID Select2 (може бути специфічним для вашої форми):
                ajax: $(this).data('ajax-url') ? { // Якщо є атрибут data-ajax-url
                    url: $(this).data('ajax-url'),
                    dataType: 'json',
                    delay: 250,
                    data: function (params) {
                        // Отримуємо id обраної військової частини
                        const unitId = $('#id_unit').val(); // Припускаємо, що #id_unit завжди є
                        return {
                            q: params.term, // search term
                            unit: unitId, // ID військової частини
                        };
                    },
                    processResults: function (data) {
                        return {
                            results: data
                        };
                    },
                    cache: true
                } : undefined, // Якщо немає data-ajax-url, то AJAX не використовується
                minimumInputLength: $(this).data('minimum-input-length') || 0, // Налаштування мінімальної довжини пошуку
            });
        }
    });

    // Оновлюємо тему Select2, якщо body має dark-theme
    if (document.body.classList.contains('dark-theme')) {
        $(scope).find('.select2').each(function() {
            if ($(this).data('select2')) { // Перевіряємо, чи Select2 ініціалізовано
                // Це не змінить тему вже ініціалізованого Select2 напряму.
                // Краще: переініціалізувати Select2 або змінити його клас динамічно.
                // Для Select2 v4 можна використовувати: $(this).data('select2').$container.addClass('select2-container--dark');
                // Або переініціалізувати:
                // $(this).select2('destroy');
                // $(this).select2({ /* нові налаштування з темою */ theme: 'default dark' });
                // Простіше рішення - додати CSS, який застосовує темну тему на основі класу body
                // .dark-theme .select2-container--default .select2-selection--single { background-color: #333; color: #fff; }
                // І т.д.
            }
        });
    }

    // Логіка для динамічного оновлення OID Select2 при зміні військової частини
    // Це має бути після ініціалізації Select2 для #id_unit
    const unitSelect = $(SELECTORS.UNIT_SELECT);
    if (unitSelect.length) {
        unitSelect.off('change.oidUpdate').on('change.oidUpdate', function() { // Використовуємо простір імен для уникнення дублювання
            const currentUnitId = $(this).val();
            // Оновлюємо всі поля OID у формсеті та головній формі, які мають Select2
            $(`${SELECTORS.FORMSET_CONTAINER} select[name$="${SELECTORS.OID_SELECT_NAME_SUFFIX}"], select[name="${SELECTORS.OID_SELECT_MAIN_NAME}"]`).each(function() {
                const $select = $(this);
                if ($select.data('select2')) { // Перевірка, чи Select2 ініціалізовано
                    // Очищаємо поточний вибір
                    $select.val(null).trigger('change');
                    // Оскільки AJAX в Select2 вже налаштований з unitId,
                    // він автоматично завантажить правильні OID-и при наступному фокусі/пошуку.
                    // Якщо вам потрібно *негайно* оновити список доступних опцій без пошуку,
                    // це може бути складніше і вимагатиме додаткових AJAX-запитів до вашого `load_oids`.
                }
            });
        });
    }
}

// Запускаємо ініціалізацію Select2 при завантаженні DOM
// Ця функція буде викликана на кожній сторінці, де підключений цей файл.
document.addEventListener('DOMContentLoaded', function() {
    initSelect2Fields();
});