// filtering_dynamic.js
// Універсальний модуль фільтрації за принципом select2 + AJAX

$(document).ready(function () {
  $('.select2').select2();

  function setupDynamicFilter(config) {
    const {
      sourceSelectId,
      targetSelectId,
      url,
      paramName,
      placeholder,
      dependsOn = [],
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

  // 🔽 Приклади використання:

  // 1. Один unit → багато oid
  setupDynamicFilter({
    sourceSelectId: '#id_unit',
    targetSelectId: '#id_oid',
    url: '/oids/ajax/load-oids-for-unit/',
    paramName: 'unit',
    placeholder: { default: 'Оберіть ОІД', loading: 'Завантаження ОІД...' }
  });

  // 2. Багато unit → багато oid
  setupDynamicFilter({
    sourceSelectId: '#id_units',
    targetSelectId: '#id_oids',
    url: '/oids/ajax/load-oids-for-units/',
    paramName: 'units[]',
    placeholder: { default: 'Оберіть ОІД', loading: 'Завантаження ОІД...' }
  });

  // 3. Багато oid → заявки
  setupDynamicFilter({
    sourceSelectId: '#id_oids',
    targetSelectId: '#id_work_requests',
    url: '/oids/ajax/get-requests-by-oids/',
    paramName: 'oid_ids',
    placeholder: { default: 'Оберіть заявку', loading: 'Завантаження заявок...' },
    transformItem: item => ({ value: item.id, label: `${item.incoming_number} — ${item.incoming_date}` })
  });

  // 4. Один oid → заявки
  setupDynamicFilter({
    sourceSelectId: '#id_oid',
    targetSelectId: '#id_work_requests',
    url: '/oids/ajax/get-requests-by-oid/',
    paramName: 'oid_id',
    placeholder: { default: 'Оберіть заявку', loading: 'Завантаження заявок...' },
    transformItem: item => ({ value: item.id, label: `${item.incoming_number} — ${item.incoming_date}` })
  });
});



/* <select id="id_units" class="select2" multiple></select>
<select id="id_oids" class="select2" multiple></select>
<select id="id_work_requests" class="select2" multiple></select>

або одиничний варіант:

<select id="id_unit" class="select2"></select>
<select id="id_oid" class="select2"></select>
<select id="id_work_requests" class="select2"></select> */