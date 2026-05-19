let multiSelectCheckboxes = document.querySelectorAll('.multi-select')
let lastChecked = null;
let lastCheckedCheckbox = null; 

multiSelectCheckboxes.forEach(element => {
    element.addEventListener('click', function(e) {
        if (!lastChecked) {
            lastChecked = this;
            lastCheckedCheckbox = [...this.parentElement.children].find(c => c.classList.contains('checkbox'))
            return;
        }

        if (e.shiftKey) {
            const siblingCheckboxes = [...this.parentElement.parentElement.children].filter(c => c.classList.contains('input-group'))

            const from = siblingCheckboxes.indexOf(this.parentElement)
            const to = siblingCheckboxes.indexOf(lastChecked.parentElement)

            const start = Math.min(from, to);
            const end = Math.max(from, to) + 1;

            const toControl = siblingCheckboxes.slice(start, end)

            toControl.forEach(el => {
                let checkbox = [...el.children].find(c => c.classList.contains('checkbox'))
                checkbox.checked = lastCheckedCheckbox.checked
            })
        }

        lastChecked = this;
        lastCheckedCheckbox = [...this.parentElement.children].find(c => c.classList.contains('checkbox'))

    })
})
