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
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = 'auto';
    }
}

// Manejo de clicks
function handleDayClick(event, date) {
    event.stopPropagation();
    const examEntry = event.target.closest('.exam-entry');
    
    if (!examEntry) {
        const dateInput = document.querySelector('#newExamModal input[name="date"]');
        if (dateInput) {
            dateInput.value = date;
            showModal('newExamModal');
        }
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