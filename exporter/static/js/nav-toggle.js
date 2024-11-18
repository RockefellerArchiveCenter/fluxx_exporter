// Mobile navigation toggle

document.getElementById('nav-toggle').addEventListener('click', function() {
  const expandedCurrent = this.getAttribute('aria-expanded');

  // Sets classes and attributes on the nav-toggle
  this.classList.toggle('active');
  this.classList.toggle('closed');
  this.setAttribute('aria-expanded', expandedCurrent === 'true' ? 'false' : 'true');

  // Sets classes and attributes on the nav-toggle-menu
  const menu = document.getElementById('nav-toggle-menu');
  menu.classList.toggle('active');
  menu.classList.toggle('closed');

  // Toggles tabindex values for each link
  const links = menu.querySelectorAll('.dropdown__btn--mobile');
  const isActive = menu.classList.contains('active');
  links.forEach(link => {
    link.tabIndex = isActive ? 0 : -1;
  });
});