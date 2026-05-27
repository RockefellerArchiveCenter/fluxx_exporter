let selectToggleCheckboxes = document.querySelectorAll(".select-toggle");

selectToggleCheckboxes.forEach(element => {
    
    element.addEventListener('click', function() {
        const prefix = this.id.replace('_select-toggle', '')
        const toControl = this.parentElement.parentElement.querySelectorAll(`[id*="${prefix}"]`)

        // Show or hide all visible checkboxes
        Array.from(toControl).map(c => c.offsetParent? c.checked = this.checked : null)
    })
})