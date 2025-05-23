document.addEventListener('DOMContentLoaded', function () {
  // Усі селекти з класом .select2 активуються
  $('.select2').select2({
    width: '100%',
    placeholder: 'Оберіть значення...',
    allowClear: true,
    language: 'uk' // або 'ru', 'en'
  });

  // Темна тема підтримка: автоматично перемикати тему
  if (document.body.classList.contains('dark-theme')) {
    $('.select2').select2({
      theme: 'default dark'
    });
  }
});
