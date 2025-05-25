// oids/static/oids/js/select2-init.js
function initSelect2Fields(scope = document) {
    $(scope).find('.select2').each(function() {
        if ($(this).data('select2')) { // Вже ініціалізовано
            // console.log("Select2 вже ініціалізовано для:", $(this).attr('id') || $(this).attr('name'));
            return;
        }
        const $selectField = $(this);
        // Використовуємо інший data-атрибут для AJAX самого Select2, щоб не плутати з data-ajax-url для filtering_dynamic.js
        const select2OwnAjaxUrl = $selectField.data('select2-ajax-url'); 

        let select2Options = {
            width: '100%',
            placeholder: $selectField.data('placeholder') || 'Оберіть значення...', // Дозволяє HTML data-placeholder
            allowClear: true,
            language: 'uk'
        };

        if (select2OwnAjaxUrl) { // Тільки якщо є data-select2-ajax-url, налаштовуємо AJAX Select2
            console.log("Налаштування Select2 з AJAX для:", $selectField.attr('id') || $selectField.attr('name'), "URL:", select2OwnAjaxUrl);
            select2Options.ajax = {
                url: select2OwnAjaxUrl,
                dataType: 'json',
                delay: 250,
                data: function (params) {
                    let ajaxCallData = { q: params.term, page: params.page || 1 };
                    const dependsOnSelector = $selectField.data('depends-on');
                    if (dependsOnSelector) {
                        const dependsOnValue = $(dependsOnSelector).val();
                        if (dependsOnValue) {
                            const paramName = $selectField.data('depends-on-param-name') || 'dependent_id';
                            ajaxCallData[paramName] = dependsOnValue;
                        }
                    }
                    return ajaxCallData;
                },
                processResults: function (data, params) {
                    params.page = params.page || 1;
                    return {
                        results: (data.results || data).map(item => ({
                            id: item.id,
                            text: item.name || item.text 
                        })),
                        pagination: {
                            more: data.pagination ? data.pagination.more : false
                        }
                    };
                },
                cache: true
            };
            select2Options.minimumInputLength = $selectField.data('minimum-input-length') || 1;
        } else {
            // Це стандартний Select2, який бере опції з HTML
            console.log("Налаштування стандартного Select2 (без AJAX) для:", $selectField.attr('id') || $selectField.attr('name'));
        }

        $selectField.select2(select2Options);
    });
    // ... (код для темної теми, якщо є) ...
}