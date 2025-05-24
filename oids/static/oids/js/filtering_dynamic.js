$(document).ready(function () {
  $('.select2').select2();

  function setupDynamicFilter(config) {
    const {
      sourceSelectId,
      targetSelectId,
      url,
      paramName,
      placeholder,
      transformItem = item => ({ value: item.id, label: item.name })
    } = config;

    function loadOptions(valueList) {
      const params = new URLSearchParams();
      if (Array.isArray(valueList)) {
        params.append(paramName, valueList.join(','));
      } else {
        params.append(paramName, valueList);
      }

      $(targetSelectId).prop('disabled', true).empty().append(`<option>${placeholder.loading}</option>`);

      $.getJSON(url + '?' + params.toString(), function (data) {
        $(targetSelectId).prop('disabled', false).empty().append(`<option>${placeholder.default}</option>`);

        data.forEach(item => {
          const option = transformItem(item);
          $(targetSelectId).append(`<option value="${option.value}">${option.label}</option>`);
        });
      });
    }

    $(sourceSelectId).on('change', function () {
      const value = $(this).val();
      if (!value || value.length === 0) {
        $(targetSelectId).empty().append(`<option>${placeholder.default}</option>`);
        return;
      }
      loadOptions(value);
    });
  }
  // Ініціалізація динамічних фільтрів з конфігурації
  if (window.dynamicFilterConfig && window.dynamicFilterConfig.filters) {
    window.dynamicFilterConfig.filters.forEach(config => {
      try {
        setupDynamicFilter({
          sourceSelectId: config.source,
          targetSelectId: config.target,
          url: config.url,
          paramName: config.param,
          placeholder: config.placeholder,
          transformItem: config.transform || (item => ({ value: item.id, label: item.name }))
        });
      } catch (e) {
        console.warn(`⚠️ Помилка під час ініціалізації фільтра між ${config.source} → ${config.target}`, e);
      }
    });
  }

  function setupDynamicFormsetFilter(config) {
    const {
      sourceSelectId,
      formSelector = '.document-form',
      fieldPrefix = 'form',
      fieldName = 'oid',
      url,
      paramName,
      placeholder,
      transformItem = item => ({ value: item.id, label: item.name })
    } = config;

    $(sourceSelectId).on('change', function () {
      const unitId = $(this).val();
      if (!unitId) return;

      $.getJSON(`${url}?${paramName}=${unitId}`, function (data) {
        $(formSelector).each(function (index) {
          const fieldId = `#id_${fieldPrefix}-${index}-${fieldName}`;
          const $select = $(this).find(fieldId);

          if (!$select.length) return;

          $select.prop('disabled', true).empty().append(`<option>${placeholder.loading}</option>`);

          $select.prop('disabled', false).empty().append(`<option value="">${placeholder.default}</option>`);
          data.forEach(item => {
            const option = transformItem(item);
            $select.append(`<option value="${option.value}">${option.label}</option>`);
          });
        });
      });
    });
  }

  if (window.dynamicFilterConfig?.filters) {
  window.dynamicFilterConfig.filters.forEach(cfg => {
    setupDynamicFilter({
      sourceSelectId: cfg.source,
      targetSelectId: cfg.target,
      url: cfg.url,
      paramName: cfg.param,
      placeholder: cfg.placeholder,
      transformItem: cfg.transform
    });
  });
}

});


/* <select id="id_units" class="select2" multiple></select>
<select id="id_oids" class="select2" multiple></select>
<select id="id_work_requests" class="select2" multiple></select>

або одиничний варіант:

<select id="id_unit" class="select2"></select>
<select id="id_oid" class="select2"></select>
<select id="id_work_requests" class="select2"></select> */