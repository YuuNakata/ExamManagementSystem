/* --- START OF FILE list_grades.js --- */

function applyFilters() {
    // Similar to manage_grades.js, this would filter the student's
    // grade list, likely via page reload or AJAX.
    const subject = document.getElementById('subject_filter').value;
    console.log("Applying filter for subject:", subject);
    alert("Filtrado activado (simulación). Recarga la página con parámetros o usa AJAX.");
    // Example URL construction:
    // window.location.search = `?subject=${subject}`;
}

// No specific JS needed for basic display, but could be added for
// interactive elements later (e.g., details pop-up on click).

/* --- END OF FILE list_grades.js --- */