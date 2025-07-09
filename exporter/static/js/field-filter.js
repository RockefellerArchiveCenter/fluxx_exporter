// Dynamically filter fieldset fields
function filterCheckboxes(input) {
    const filter = input.value.toLowerCase();
    const checkboxList = input.closest('fieldset').querySelector('.checkbox-list');
    const items = checkboxList.querySelectorAll('.input-group');
    items.forEach(function(item) {
        const label = item.querySelector('label').textContent.toLowerCase();
        item.style.display = label.includes(filter) ? '' : 'none';
    });
}