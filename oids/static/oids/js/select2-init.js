// oids/static/oids/js/select2-init.js

function initSelect2Fields(scope = document) {
    $(scope)
        .find(".select2")
        .each(function () {
            if ($(this).data("select2")) {
                // Перевірка, щоб не ініціалізувати двічі
                return;
            }
            const $selectField = $(this);
            const select2OwnAjaxUrl = $selectField.data("select2-ajax-url"); // Для AJAX самого Select2

            let select2Options = {
                width: "100%",
                placeholder: $selectField.data("placeholder") || "Оберіть значення...",
                allowClear: !!$selectField.find('option[value=""]').length, // allowClear, якщо є порожня опція
                language: "uk",
            };

            if (select2OwnAjaxUrl) {
                // Цей блок для Select2, які САМІ завантажують свої опції через AJAX (пошук)
                // Наприклад, якщо в тебе є select для вибору ОІД у формі з тисячами ОІДів.
                // Для #id_unit_filter цей блок не має спрацьовувати, бо в нього немає data-select2-ajax-url
                console.log("Налаштування Select2 з ВЛАСНИМ AJAX для:", $selectField.attr("id") || $selectField.attr("name"), "URL:", select2OwnAjaxUrl);
                select2Options.ajax = {
                    url: select2OwnAjaxUrl,
                    dataType: "json",
                    delay: 250,
                    data: function (params) {
                        let ajaxCallData = { q: params.term, page: params.page || 1 };
                        const dependsOnSelector = $selectField.data("depends-on");
                        if (dependsOnSelector) {
                            const dependsOnValue = $(dependsOnSelector).val();
                            if (dependsOnValue) {
                                const paramName = $selectField.data("depends-on-param-name") || "dependent_id";
                                ajaxCallData[paramName] = dependsOnValue;
                            }
                        }
                        return ajaxCallData;
                    },
                    processResults: function (data, params) {
                        params.page = params.page || 1;
                        return {
                            results: (data.results || data).map((item) => ({
                                id: item.id,
                                text: item.name || item.text, // Припустимо, сервер повертає 'name' або 'text'
                            })),
                            pagination: {
                                more: data.pagination ? data.pagination.more : false,
                            },
                        };
                    },
                    cache: true,
                };
                select2Options.minimumInputLength = $selectField.data("minimum-input-length") || 1;
            } else {
                // Це стандартний Select2, який бере опції з HTML (як наш #id_unit_filter)
                // console.log("Налаштування стандартного Select2 (без AJAX) для:", $selectField.attr('id') || $selectField.attr('name'));
            }

            $selectField.select2(select2Options);
        });
    console.log("select2 was inited");
    // ... (твій код для темної теми, якщо потрібен) ...
}

// Виклик initSelect2Fields має бути в base.html в $(document).ready()
