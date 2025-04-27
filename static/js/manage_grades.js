/* --- START OF FILE manage_grades.js --- */

function applyFilters() {
    // In a real application, this would likely trigger a page reload
    // with query parameters or use AJAX to fetch filtered data.
    const subject = document.getElementById('subject_filter').value;
    const examType = document.getElementById('exam_type_filter').value;
    const date = document.getElementById('date_filter').value;
    console.log("Applying filters:", { subject, examType, date });
    alert("Filtrado activado (simulación). Recarga la página con parámetros o usa AJAX.");
    // Example URL construction (for page reload):
    // window.location.search = `?subject=${subject}&type=${examType}&date=${date}`;
}

function saveGrade(gradeId) {
    // In a real application, this would use AJAX to send the updated grade
    // associated with gradeId to the backend.
    const inputElement = document.querySelector(`.grade-input[data-grade-id='${gradeId}']`);
    const gradeValue = inputElement.value;
    console.log(`Saving grade for ID ${gradeId}: ${gradeValue}`);

    // Basic validation example
    if (gradeValue === '' || (parseFloat(gradeValue) >= 0 && parseFloat(gradeValue) <= 10)) {
        // Simulate saving - maybe disable input after saving or show success message
         alert(`Nota ${gradeValue} para ID ${gradeId} guardada (simulación).`);
         inputElement.disabled = true; // Example: disable after save
         // Find the corresponding "Modificar" button and show it, hide "Guardar"
         const saveButton = inputElement.closest('tr').querySelector('.btn-primary');
         const editButton = inputElement.closest('tr').querySelector('.btn-secondary');
         if(saveButton) saveButton.style.display = 'none';
         if(editButton) editButton.style.display = 'inline-block';


    } else {
        alert("Por favor, introduce una nota válida entre 0 y 10.");
        inputElement.focus();
    }

    // Add AJAX call here to POST data to the server
    // fetch(`/api/grades/${gradeId}/update`, { method: 'POST', body: JSON.stringify({ score: gradeValue }), headers: {'Content-Type': 'application/json', 'X-CSRFToken': '...'} })
    // .then(response => response.json())
    // .then(data => console.log('Success:', data))
    // .catch((error) => console.error('Error:', error));
}

function editGrade(gradeId) {
    // Function to re-enable the input field
     const inputElement = document.querySelector(`.grade-input[data-grade-id='${gradeId}']`);
     inputElement.disabled = false;
     inputElement.focus();

     // Hide the "Modificar" button and show the "Guardar" button
     const saveButton = inputElement.closest('tr').querySelector('.btn-primary');
     const editButton = inputElement.closest('tr').querySelector('.btn-secondary');
     if(saveButton) saveButton.style.display = 'inline-block';
     if(editButton) editButton.style.display = 'none';
}


// Initialize: Hide "Modificar" buttons initially if the input is not disabled
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.grades-table tbody tr').forEach(row => {
        const inputElement = row.querySelector('.grade-input');
        const saveButton = row.querySelector('.btn-primary'); // Assumes save is default
        const editButton = row.querySelector('.btn-secondary'); // Assumes edit is secondary

        if (inputElement && saveButton && editButton) {
            if (inputElement.disabled) {
                saveButton.style.display = 'none';
                editButton.style.display = 'inline-block';
            } else {
                 saveButton.style.display = 'inline-block';
                 editButton.style.display = 'none';
            }
        }
    });
});

/* --- END OF FILE manage_grades.js --- */