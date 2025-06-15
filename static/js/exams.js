// Helper function to display form errors from a JSON object
function displayFormErrors(form, errors) {
    // Remove any existing error messages
    form.querySelectorAll('.errorlist').forEach(el => el.remove());

    for (const fieldName in errors) {
        const errorMessages = errors[fieldName];
        const errorList = document.createElement('div');
        errorList.className = 'errorlist';
        
        errorMessages.forEach(msg => {
            const errorSpan = document.createElement('span');
            errorSpan.textContent = msg;
            errorList.appendChild(errorSpan);
        });

        if (fieldName === '__all__') {
            // For non-field errors, prepend them to the form
            form.prepend(errorList);
        } else {
            // For field-specific errors, find the field and insert the errors after it
            const field = form.querySelector(`[name="${fieldName}"]`);
            if (field) {
                field.classList.add('is-invalid'); // Add class to highlight the invalid field
                const parentContainer = field.parentElement;

                if (parentContainer && parentContainer.tagName === 'P') {
                    // Insert after the <p> tag that wraps the input
                    parentContainer.insertAdjacentElement('afterend', errorList);
                } else {
                    // Fallback if the field is not wrapped in a <p>
                    field.insertAdjacentElement('afterend', errorList);
                }
            }
        }
    }
}

document.addEventListener('DOMContentLoaded', function() {
    
    // Use event delegation on the document to handle all form submissions in modals
    document.addEventListener('submit', function(event) {
        
        const form = event.target;
        // Check if the submitted form is for creating or editing an exam
        if (form && (form.id === 'createExamForm' || form.id.startsWith('editForm'))) {
            event.preventDefault(); // Stop default form submission

            const formData = new FormData(form);
            const url = form.action;

            fetch(url, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                }
            })
            .then(response => {
                // Check if the response is ok, if not, throw an error to be caught later
                if (!response.ok) {
                    // Try to parse JSON error first, fallback to text
                    return response.json().catch(() => response.text()).then(errorBody => {
                        // Pass both status and body to the catch block
                        throw { status: response.status, body: errorBody };
                    });
                }
                return response.json();
            })
            .then(data => {
                if (data.status === 'success') {
                    // On success, simply reload the page to show the changes
                    // This works for both create (redirect_url) and update (message)
                    window.location.reload();
                } else if (data.status === 'error' && data.errors) {
                    // If the server returns a JSON with errors, display them
                    displayFormErrors(form, data.errors);
                }
            })
            .catch(error => {
                console.error('Error en la petición AJAX:', error);
                // Handle different error types
                let errorMessage = 'Ocurrió un error inesperado.';
                if (error.status) {
                    errorMessage = `Error del servidor (${error.status}).`;
                    if (typeof error.body === 'string') {
                        errorMessage += ` Respuesta: ${error.body}`;
                    } else if (error.body && error.body.errors) {
                        // If the server sent a JSON error response despite the !ok status
                        displayFormErrors(form, error.body.errors);
                        return; // Errors displayed, no need for alert
                    }
                }
                alert(errorMessage);
            });
        }
    });
});
