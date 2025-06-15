// Mostrar modales
function showModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'flex';
        document.body.style.overflow = 'hidden';
    }
}

// Cerrar modales
function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (!modal) return;

    // Find all forms within the modal
    const forms = modal.querySelectorAll('form');
    forms.forEach(form => {
        // Reset form fields to their initial values
        form.reset();

        // Remove any dynamically added error messages
        const errorLists = form.querySelectorAll('.errorlist');
        errorLists.forEach(errorList => {
            errorList.remove();
        });

        // Remove .is-invalid class from fields
        const invalidFields = form.querySelectorAll('.is-invalid');
        invalidFields.forEach(field => {
            field.classList.remove('is-invalid');
        });
    });

    // Hide the modal
    modal.style.display = 'none';
    document.body.style.overflow = 'auto';
}

// Manejo de clicks
function handleDayClick(event, date) {
    event.stopPropagation();
    const examEntry = event.target.closest('.exam-entry');
    const addButton = event.target.closest('.add-exam-btn');
    
    if (!examEntry && !addButton) {
        const dateInput = document.querySelector('#newExamModal input[name="date"]');
        if (dateInput) {
            dateInput.value = date;
            showModal('newExamModal');
        }
    }
}

function handleAddExam(event, dateStr) {
    event.stopPropagation(); // Prevent triggering day click if nested differently
    const modal = document.getElementById('newExamModal');
    if (modal) {
        // Find the date input within the new exam form and set its value
        const dateInput = modal.querySelector('input[name="date"]'); // Adjust selector if needed
        if (dateInput) {
            dateInput.value = dateStr;
        } else {
            console.warn("Date input not found in newExamModal form.");
        }
        showModal('newExamModal');
    } else {
        console.error("newExamModal not found.");
    }
}

// Event listeners
document.addEventListener('DOMContentLoaded', () => {
    // Cerrar modal con botón X
    document.querySelectorAll('.modal .close').forEach(btn => {
        btn.addEventListener('click', () => closeModal(btn.closest('.modal').id));
    });

    // Cerrar al hacer click fuera
    document.querySelectorAll('.modal').forEach(modal => {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) closeModal(modal.id);
        });
    });

    // Click en exámenes existentes
    document.querySelectorAll('.exam-entry').forEach(exam => {
        exam.addEventListener('click', () => {
            showModal(`examModal${exam.dataset.examId}`);
        });
    });
});

function showMainModal({message, type="info", onConfirm=null, onCancel=null, confirmText="Aceptar", cancelText="Cancelar"}) {
    const modal = document.getElementById('mainModal');
    const text = document.getElementById('mainModalText');
    const actions = document.getElementById('mainModalActions');
    text.innerText = message;
    actions.innerHTML = "";

    // Color según tipo
    modal.querySelector('.modal-content').style.borderLeft = 
        type === "success" ? "5px solid #4caf50" :
        type === "error" ? "5px solid #f44336" :
        type === "warning" ? "5px solid #ff9800" : "none";

    if (onConfirm) {
        // Confirmación (ej: eliminar)
        const btnConfirm = document.createElement('button');
        btnConfirm.innerText = confirmText;
        btnConfirm.className = "btn btn-danger";
        btnConfirm.onclick = function() { closeMainModal(); onConfirm(); };
        actions.appendChild(btnConfirm);

        const btnCancel = document.createElement('button');
        btnCancel.innerText = cancelText;
        btnCancel.className = "btn btn-secondary";
        btnCancel.onclick = closeMainModal;
        actions.appendChild(btnCancel);
    } else {
        // Solo info/éxito/error
        const btnOk = document.createElement('button');
        btnOk.innerText = "Cerrar";
        btnOk.className = "btn btn-primary";
        btnOk.onclick = closeMainModal;
        actions.appendChild(btnOk);
    }

    modal.style.display = "flex";
}

function closeMainModal() {
    document.getElementById('mainModal').style.display = "none";
}