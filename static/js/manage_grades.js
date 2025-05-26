/* --- START OF FILE manage_grades.js --- */

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

// Ensure this file is loaded after modals.js if showModal/closeModal are defined there

function openGradeModal(examRequestId, studentName, examSubject, examType, examDate, currentGrade, currentComments) {
    const modal = document.getElementById('gradeExamModal');
    if (!modal) {
        console.error('Grade exam modal not found!');
        return;
    }

    // Populate student and exam information
    const studentInfoDiv = modal.querySelector('#modalStudentInfo');
    if (studentInfoDiv) {
        studentInfoDiv.innerHTML = `<strong>Estudiante:</strong> ${studentName}`;
    }
    const examInfoDiv = modal.querySelector('#modalExamInfo');
    if (examInfoDiv) {
        examInfoDiv.innerHTML = `<strong>Examen:</strong> ${examSubject} (${examType}) - ${examDate}`;
    }

    // Set the form action URL
    const form = modal.querySelector('#gradeFormInModal');
    if (form) {
        form.action = `/exams/grade-exam/${examRequestId}/`; // Construct the URL dynamically
    }

    // Pre-fill form fields
    // Assumes grade_form.grade and grade_form.comments are the IDs/names used in the template
    const gradeInput = modal.querySelector('[name="grade"]'); // Or use ID: #id_grade
    if (gradeInput) {
        gradeInput.value = currentGrade || '';
    }
    const commentsTextarea = modal.querySelector('[name="comments"]'); // Or use ID: #id_comments
    if (commentsTextarea) {
        commentsTextarea.value = currentComments || '';
    }

    // Show the modal (assuming showModal is globally available from modals.js)
    if (typeof showModal === 'function') {
        showModal('gradeExamModal');
    } else {
        console.error('showModal function is not defined. Make sure modals.js is loaded before manage_grades.js');
        // Fallback to basic display if showModal is missing, for basic testing
        // modal.style.display = 'flex'; 
    }
}

// Optional: Add event listener for the modal's close button if not handled by a generic one in modals.js
document.addEventListener('DOMContentLoaded', () => {
    const gradeModal = document.getElementById('gradeExamModal');
    if (gradeModal) {
        const closeBtn = gradeModal.querySelector('.close');
        if (closeBtn && typeof closeModal === 'function') {
            // This might be redundant if modals.js already handles all .close buttons
            // Check modals.js to avoid double event listeners
            // closeBtn.addEventListener('click', () => closeModal('gradeExamModal'));
        }
    }

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