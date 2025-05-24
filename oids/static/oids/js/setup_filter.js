$(document).ready(function () {
    attachOidAside(); // якщо є

    setupDynamicFilter({
      sourceSelectId: '#id_units',
      targetSelectId: '#id_oids',
      url: '/oids/ajax/get-oids-by-units/',
      paramName: 'units[]',
      placeholder: { default: 'Оберіть ОІД', loading: 'Завантаження ОІД...' }
    });

    setupDynamicFilter({
      sourceSelectId: '#id_oids',
      targetSelectId: '#id_related_request',
      url: '/oids/ajax/get-requests-by-oids/',
      paramName: 'oid_ids',
      placeholder: { default: 'Оберіть заявку', loading: 'Завантаження заявок...' },
      transformItem: item => ({ value: item.id, label: `${item.incoming_number} — ${item.incoming_date}` })
    });

    setupDynamicFilter({
      sourceSelectId: '#id_oids',
      targetSelectId: '#id_documents',
      url: '/oids/ajax/load-documents-for-oids/',
      paramName: 'oids[]',
      placeholder: { default: 'Оберіть документи', loading: 'Завантаження документів...' },
      transformItem: item => ({ value: item.id, label: `${item.document_type__name} / ${item.document_number}` })
    });
  });