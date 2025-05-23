
//  <label for="id_units">Військові частини:</label>
//     <select id="id_units" class="select2">
//       <option value="">-- Оберіть в/ч --</option>
//           {% for unit in units %}
//           <option value="{{ unit.id }}">{{ unit.name }}</option>
//           {% endfor %}
//     </select>

//   <label for="id_oids">ОІД:</label>
//     <select id="id_oids" class="select2" disabled>
//       <option value="">-- Спочатку оберіть в/ч --</option>
//     </select>

//   <label for="id_work_requests">Заявки:</label>
//     <select id="id_work_requests" class="select2" disabled>
//       <option value="">-- Спочатку оберіть ОІД --</option>
//     </select>



$(document).ready(function() {
  $('.select2').select2();

  // Обираємо військову частину — отримуємо список OID
  $('#id_units').on('change', function() {
    const unitId = $(this).val();

    $('#id_oids').prop('disabled', true).empty().append('<option>Завантаження...</option>');
    $('#id_work_requests').prop('disabled', true).empty().append('<option>-- Спочатку оберіть ОІД --</option>');

    if (unitId) {
      $.getJSON(`/oids/api/oids/?unit_id=${unitId}`, function(data) {
        $('#id_oids').prop('disabled', false).empty().append('<option value="">-- Оберіть ОІД --</option>');
        data.forEach(oid => {
          $('#id_oids').append(`<option value="${oid.id}">${oid.name}</option>`);
        });
      });
    }
  });

  // Обираємо OID — отримуємо список заявок
  $('#id_oids').on('change', function() {
    const oidId = $(this).val();

    $('#id_work_requests').prop('disabled', true).empty().append('<option>Завантаження...</option>');

    if (oidId) {
      $.getJSON(`/oids/api/requests/?oid_id=${oidId}`, function(data) {
        $('#id_work_requests').prop('disabled', false).empty().append('<option value="">-- Оберіть заявку --</option>');
        data.forEach(req => {
          $('#id_work_requests').append(`<option value="${req.id}">${req.incoming_number} — ${req.incoming_date}</option>`);
        });
      });
    }
  });
});
