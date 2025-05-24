// oids/static/oids/js/filter_config.js

window.dynamicFilterConfig = {
  filters: [
    {
      source: '#id_unit',
      target: '#id_oid',
      url: '/oids/ajax/load-oids-for-unit/',
      param: 'unit',
      placeholder: {
        default: 'Оберіть ОІД',
        loading: 'Завантаження ОІД...'
      }
    },
    {
      source: '#id_units',
      target: '#id_oids',
      url: '/oids/ajax/load-oids-for-units/',
      param: 'units[]',
      placeholder: {
        default: 'Оберіть ОІД',
        loading: 'Завантаження ОІД...'
      }
    },
    {
      source: '#id_oids',
      target: '#id_work_requests',
      url: '/oids/ajax/get-requests-by-oids/',
      param: 'oid_ids',
      placeholder: {
        default: 'Оберіть заявку',
        loading: 'Завантаження заявок...'
      },
      transform: item => ({ value: item.id, label: `${item.incoming_number} — ${item.incoming_date}` })
    },
    {
      source: '#id_oid',
      target: '#id_work_requests',
      url: '/oids/ajax/get-requests-by-oid/',
      param: 'oid_id',
      placeholder: {
        default: 'Оберіть заявку',
        loading: 'Завантаження заявок...'
      },
      transform: item => ({ value: item.id, label: `${item.incoming_number} — ${item.incoming_date}` })
    }
  ]
};
