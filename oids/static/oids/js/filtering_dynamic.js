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

  // 🔽 Статичні фільтри
  setupDynamicFilter({
    sourceSelectId: '#id_unit',
    targetSelectId: '#id_oid',
    url: '/oids/ajax/load-oids-for-unit/',
    paramName: 'unit',
    placeholder: { default: 'Оберіть ОІД', loading: 'Завантаження ОІД...' }
  });

  setupDynamicFilter({
    sourceSelectId: '#id_units',
    targetSelectId: '#id_oids',
    url: '/oids/ajax/load-oids-for-units/',
    paramName: 'units[]',
    placeholder: { default: 'Оберіть ОІД', loading: 'Завантаження ОІД...' }
  });

  setupDynamicFilter({
    sourceSelectId: '#id_oids',
    targetSelectId: '#id_work_requests',
    url: '/oids/ajax/get-requests-by-oids/',
    paramName: 'oid_ids',
    placeholder: { default: 'Оберіть заявку', loading: 'Завантаження заявок...' },
    transformItem: item => ({ value: item.id, label: `${item.incoming_number} — ${item.incoming_date}` })
  });

  setupDynamicFilter({
    sourceSelectId: '#id_oid',
    targetSelectId: '#id_work_requests',
    url: '/oids/ajax/get-requests-by-oid/',
    paramName: 'oid_id',
    placeholder: { default: 'Оберіть заявку', loading: 'Завантаження заявок...' },
    transformItem: item => ({ value: item.id, label: `${item.incoming_number} — ${item.incoming_date}` })
  });

  // 🔁 Для formset'ів (всі OID у заявці)
  setupDynamicFormsetFilter({
    sourceSelectId: '#id_unit',
    formSelector: '.document-form',
    fieldPrefix: 'form',
    fieldName: 'oid',
    url: '/oids/ajax/load-oids-for-unit/',
    paramName: 'unit',
    placeholder: { default: 'Оберіть ОІД', loading: 'Оновлення ОІД...' }
  });
});
