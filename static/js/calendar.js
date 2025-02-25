document.addEventListener('DOMContentLoaded', function() {
    const calendarEl = document.getElementById('calendar');
    
    function renderCalendar(events) {
        const calendarHTML = events.map(event => `
            <div class="evento">
                <div class="fecha">${event.start}</div>
                <div class="titulo">${event.title}</div>
            </div>
        `).join('');
        calendarEl.innerHTML = calendarHTML;
    }

    // Cargar eventos desde API
    fetch('/api/eventos/')
        .then(response => response.json())
        .then(data => renderCalendar(data));
});