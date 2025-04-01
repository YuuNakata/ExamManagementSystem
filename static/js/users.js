 // Manejo de modales
function showModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'flex';
    } else {
        console.error('Modal no encontrado:', modalId);
    }
}

function closeModal(modalId) {
    // Limpiar parámetros de URL
    const url = new URL(window.location);
    url.searchParams.delete('editing');
    url.searchParams.delete('show_register');
    window.history.replaceState({}, '', url);
    
    // Resto de lógica original
    const modal = document.getElementById(modalId);
    if (modal) modal.style.display = 'none';
}

// Búsqueda en tiempo real
function performSearch() {
    const query = document.getElementById('searchInput').value;
    window.location = `/users/manage/?q=${encodeURIComponent(query)}`;
}

// Confirmación de eliminación
function confirmDelete(formId) {
    if (confirm('¿Está seguro que desea eliminar este usuario?')) {
        document.getElementById(formId).submit();
    }
}
// Event listeners
document.getElementById('searchInput').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') performSearch();
});

window.onload = function() {
    const modals = document.querySelectorAll('.modal');
    modals.forEach(modal => {
        if (modal.style.display === 'block') {
            modal.style.display = 'none';
            console.log('Modal cerrado al cargar la página:', modal.id);
        }
    });
}