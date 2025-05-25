    $(document).ready(function() {
            console.log("Document ready. Initializing Select2 and Filters...");
            // 1. Ініціалізація Select2
            if (typeof initSelect2Fields === 'function') {
                initSelect2Fields(document); // Передаємо scope, якщо потрібно для формсетів
                console.log("Select2 fields initialized.");
            } else {
                console.warn("Function initSelect2Fields not found.");
            }

            // У $(document).ready(), після виклику initSelect2Fields()
const $unitFilter = $('#id_unit_filter');
if ($unitFilter.data('select2')) { // Переконуємося, що Select2 ініціалізовано
    const currentValue = $unitFilter.val();
    console.log("Forcing trigger change on #id_unit_filter after init. Current value:", currentValue);
    $unitFilter.trigger('change'); // Це може допомогти Select2 "побачити" опції

    // Якщо є початкове значення з URL, спробувати встановити його ще раз
    const initialUnitId = "{{ request.GET.unit|default:'' }}"; // З Django шаблону
    if (initialUnitId && initialUnitId !== currentValue) {
        console.log("Setting initial unit ID from GET param:", initialUnitId);
        $unitFilter.val(initialUnitId).trigger('change');
    }
}

            // 2. Ініціалізація динамічних фільтрів ПІСЛЯ Select2
            if (typeof initializeDynamicFilters === 'function') {
                initializeDynamicFilters();
                console.log("Dynamic filters initialized.");
            } else {
                console.warn("Function initializeDynamicFilters not found.");
            }
        });