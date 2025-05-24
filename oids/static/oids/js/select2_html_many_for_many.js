// C:\myFirstCRM\oids\static\oids\js\select2_html_many_for_many.js
$(document).ready(function() {
  $('.select2').select2();

  // Коли змінюється вибір частин
  $('#id_units').on('change', function() {
    const selectedUnits = $(this).val(); // array of selected ids

    $('#id_oids').prop('disabled', true).empty().append('<option>Завантаження...</option>');
    $('#id_work_requests').prop('disabled', true).empty().append('<option>-- Спочатку оберіть ОІД --</option>');

    if (selectedUnits.length > 0) {
      const ids = selectedUnits.join(',');
      $.getJSON(`/oids/api/oids/?unit_ids=${ids}`, function(data) {
        $('#id_oids').prop('disabled', false).empty();
        data.forEach(oid => {
          $('#id_oids').append(`<option value="${oid.id}">${oid.name}</option>`);
        });
      });
    }
  });

  // Коли змінюється вибір ОІД
  $('#id_oids').on('change', function() {
    const selectedOids = $(this).val();

    $('#id_work_requests').prop('disabled', true).empty().append('<option>Завантаження...</option>');

    if (selectedOids.length > 0) {
      const ids = selectedOids.join(',');
      $.getJSON(`/oids/api/requests/?oid_ids=${ids}`, function(data) {
        $('#id_work_requests').prop('disabled', false).empty();
        data.forEach(req => {
          $('#id_work_requests').append(`<option value="${req.id}">${req.incoming_number} — ${req.incoming_date}</option>`);
        });
      });
    }
  });
});

