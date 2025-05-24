// 1
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