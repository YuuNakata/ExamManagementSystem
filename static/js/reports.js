/* --- START OF FILE reports.js --- */

// Ensure modal functions are available (assuming modals.js is loaded globally via base.html)
// If not, include showModal/closeModal functions here or ensure modals.js is loaded first.
// Example:
// function showModal(modalId) { ... }
// function closeModal(modalId) { ... }

/**
 * Prompts the user to confirm deletion of a report.
 * If confirmed, submits the corresponding hidden delete form.
 *
 * @param {string} reportId - The ID of the report to delete.
 * @param {string} reportTitle - The title/name of the report for the confirmation message.
 */
function confirmDelete(reportId, reportTitle) {
    const confirmation = confirm(`¿Está seguro que desea eliminar el reporte "${reportTitle}"?\n\nEsta acción no se puede deshacer.`);

    if (confirmation) {
        console.log(`Confirmed deletion for report ID: ${reportId}`);
        // Find the hidden form associated with this report ID
        const deleteForm = document.getElementById(`deleteForm${reportId}`);
        if (deleteForm) {
            // Submit the form to perform the deletion via POST request
            deleteForm.submit();

            // Optionally, you could use AJAX (fetch) here instead of form submission
            // to provide a smoother experience without page reload.
            // Example AJAX call (requires backend endpoint setup):
            /*
            fetch(`/reports/delete/${reportId}/`, { // Adjust URL as needed
                method: 'POST',
                headers: {
                    'X-CSRFToken': deleteForm.querySelector('[name=csrfmiddlewaretoken]').value, // Get CSRF token
                    'Content-Type': 'application/json' // Or appropriate content type
                },
                // body: JSON.stringify({ id: reportId }) // Optional body if needed
            })
            .then(response => {
                if (response.ok) {
                    console.log(`Report ${reportId} deleted successfully.`);
                    // Remove the report item from the list visually
                    const reportElement = document.getElementById(`report-item-${reportId}`);
                    if (reportElement) {
                        reportElement.style.transition = 'opacity 0.5s ease';
                        reportElement.style.opacity = '0';
                        setTimeout(() => reportElement.remove(), 500); // Remove after fade out
                    }
                    // Optionally show a success message (e.g., using a toast notification library)
                } else {
                    // Handle error - maybe show an alert
                    console.error(`Failed to delete report ${reportId}. Status: ${response.status}`);
                    alert('Error al eliminar el reporte. Por favor, inténtelo de nuevo.');
                }
            })
            .catch(error => {
                console.error('Error during report deletion request:', error);
                alert('Ocurrió un error de red al intentar eliminar el reporte.');
            });
            */

        } else {
            console.error(`Delete form not found for report ID: ${reportId}`);
            alert('Error interno: No se pudo encontrar el formulario de eliminación.');
        }
    } else {
        console.log(`Deletion cancelled for report ID: ${reportId}`);
    }
}

// Optional: Add any client-side validation for the generate report modal form
document.addEventListener('DOMContentLoaded', () => {
    const generateForm = document.querySelector('#generateReportModal form');
    if (generateForm) {
        generateForm.addEventListener('submit', (event) => {
            const reportType = document.getElementById('report_type').value;
            const startDateInput = document.getElementById('start_date');
            const endDateInput = document.getElementById('end_date');
            const startDate = startDateInput.value;
            const endDate = endDateInput.value;

            // Basic validation example: Check if report type is selected
            if (!reportType) {
                 alert('Por favor, seleccione un tipo de reporte.');
                 event.preventDefault(); // Stop form submission
                 return;
            }

             // Basic validation example: Check if end date is before start date
            if (startDate && endDate && startDate > endDate) {
                alert('La fecha de fin no puede ser anterior a la fecha de inicio.');
                endDateInput.focus();
                event.preventDefault(); // Stop form submission
                return;
            }

            console.log('Generating report...');
            // Allow form submission to proceed
        });
    }
});


/* --- END OF FILE reports.js --- */