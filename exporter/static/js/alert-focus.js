// On page load, set focus to the first .alert <div> inside #alert-message if it exists
window.addEventListener('DOMContentLoaded', function () {
  var alertContainer = document.getElementById('alert-message');
  if (alertContainer) {
      var firstAlert = alertContainer.querySelector('.alert');
      if (firstAlert) {
          firstAlert.focus();
      }
  }
});
