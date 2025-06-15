 /**
 * Shows a confirmation modal before submitting the delete form.
 * @param {string} formId The ID of the form to submit on confirmation.
 */
function confirmDelete(formId) {
    window.showModalMessage(
        '¿Está seguro que desea eliminar este usuario?',
        'warning',
        () => {
            document.getElementById(formId).submit();
        }
    );
}

/**
 * Redirects to the user management page with a search query.
 */
function performSearch() {
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        window.location.href = `/users/manage/?q=${encodeURIComponent(searchInput.value)}`;
    }
}

document.addEventListener('DOMContentLoaded', () => {
    // Use event delegation on a common ancestor for all forms
    document.body.addEventListener('submit', function(event) {
        // Target both edit and register forms
        const form = event.target.closest('#registerForm, form[id^="editForm"]');
        if (!form) return; // Exit if the submitted element is not a targeted form

        event.preventDefault(); // Prevent default browser submission

        const formData = new FormData(form);

        fetch(form.action, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': formData.get('csrfmiddlewaretoken')
            }
        })
        .then(response => response.json())
        .then(data => {
            clearFormErrors(form);

            if (data.status === 'success') {
                window.location.reload();
            } else if (data.status === 'error' && data.errors) {
                displayFormErrors(form, data.errors);

                // Scroll modal to top to show errors
                const modalContent = form.closest('.modal-content');
                if (modalContent) {
                    modalContent.scrollTop = 0;
                }
            }
        })
        .catch(error => {
            console.error('Error in AJAX request:', error);
            alert('An unexpected error occurred. Please check the console.');
        });
    });

    // Add event listener for Enter key on search input
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault(); // Prevent default form submission
                performSearch();
            }
        });
    }
});

/**
 * Displays validation errors on the form.
 * @param {HTMLFormElement} form The form element.
 * @param {Object} errors An object where keys are field names and values are arrays of error messages.
 */
function displayFormErrors(form, errors) {
    for (const fieldName in errors) {
        const field = form.querySelector(`[name="${fieldName}"]`);
        if (field) {
            const parent = field.closest('p') || field.parentElement;
            const errorList = document.createElement('ul');
            errorList.className = 'errorlist';
            
            errors[fieldName].forEach(errorText => {
                const listItem = document.createElement('li');
                listItem.textContent = errorText;
                errorList.appendChild(listItem);
            });
            
            parent.insertAdjacentElement('afterend', errorList);
            field.classList.add('is-invalid');
        }
    }
    if (errors.__all__) {
        const nonFieldErrorsDiv = document.createElement('div');
        nonFieldErrorsDiv.className = 'errorlist non-field-errors';
        
        errors.__all__.forEach(errorText => {
            const errorItem = document.createElement('p');
            errorItem.textContent = errorText;
            nonFieldErrorsDiv.appendChild(errorItem);
        });
        
        form.prepend(nonFieldErrorsDiv);
    }
}

/**
 * Removes all error messages and invalid-field styling from a form.
 * @param {HTMLFormElement} form The form element.
 */
function clearFormErrors(form) {
    const errorLists = form.querySelectorAll('.errorlist');
    errorLists.forEach(list => list.remove());

    const invalidFields = form.querySelectorAll('.is-invalid');
    invalidFields.forEach(field => field.classList.remove('is-invalid'));
}