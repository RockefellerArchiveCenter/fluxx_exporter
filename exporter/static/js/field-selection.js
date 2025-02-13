let checkboxes = document.querySelectorAll(".table-field");

checkboxes.forEach(element => {
    
    element.addEventListener('click', function() {
        const attributes = this.id.split('-')
        let tableInput = document.getElementById(`id_${attributes[1]}-${attributes[2]}-include_in_export`)
        const siblingCheckboxes = this.parentElement.parentElement.querySelectorAll('.table-field')

        const anyChecked = Array.from(siblingCheckboxes).some(checkbox => checkbox.checked)
        if (anyChecked) {
            tableInput.value = "on"
        } else {
            tableInput.value = null
        }

    })
})