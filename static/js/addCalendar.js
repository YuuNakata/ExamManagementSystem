function addExam() {
    const date = document.getElementById('date').value;
    const subject = document.getElementById('subject').value;
    const examType = document.getElementById('exam-type').value;

    if (date && subject && examType) {
        const tableBody = document.querySelector('.exam-calendar tbody');
        const newRow = document.createElement('tr');

        newRow.innerHTML = `
            <td>${new Date(date).toLocaleDateString()}</td>
            <td>${subject}</td>
            <td>${examType}</td>
        `;

        tableBody.appendChild(newRow);
        alert('Examen agregado exitosamente.');
    } else {
        alert('Por favor, completa todos los campos.');
    }
}
