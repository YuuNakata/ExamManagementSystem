// Validación genérica de formularios
document.querySelectorAll('form').forEach(form => {
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        try {
            const response = await fetch(form.action, {
                method: form.method,
                body: new FormData(form)
            });

            if (response.ok) {
                window.location.href = '/dashboard';
            } else {
                alert('Error al procesar la solicitud');
            }
        } catch (error) {
            console.error('Error:', error);
        }
    });
});