# --- START OF FILE models.py ---

from django.db import models
from users.models import User # Make sure this import is correct for your project
from datetime import date
from django.core.exceptions import ValidationError # Add this import

class CalendarExam(models.Model): # Keep CalendarExam as is
    class Meta:
        ordering = ['date', 'turn'] # Good practice to add ordering

    EXAM_TYPES = (
        ("suficiencia", "Suficiencia"),
        ("premio", "Premio"),
    )
    TURN_CHOICES = [
        ("1", "8:00-12:00"),
        ("2", "12:00-4:00"),
    ]
    date = models.DateField(
        "Fecha del examen", default=date.today, null=False, blank=False
    )
    turn = models.CharField(
        "Turno", max_length=1, choices=TURN_CHOICES, null=False, blank=False
    )
    exam_type = models.CharField(
        "Tipo", max_length=20, choices=EXAM_TYPES, null=False, blank=False # Changed verbose_name slightly
    )
    subject = models.CharField(
        max_length=100, verbose_name="Asignatura", null=False, blank=False
    )

    def __str__(self):
        # Using f-string and accessing display values directly
        return f"{self.date.strftime('%Y-%m-%d')} - {self.get_turn_display()} - {self.subject}"

    def is_past(self):
        return self.date < date.today()


class ExamRequest(models.Model):
    REQUEST_STATUS = (
        ('Pending', 'Pendiente'),
        ('Approved', 'Aprobada'),
        ('Rejected', 'Rechazada'),
    )

    student = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="exam_requests"
    )

    calendar_exam = models.ForeignKey(
        CalendarExam, on_delete=models.CASCADE, related_name="requests",
        null=True, 
    )
    request_timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Solicitud",null=True)
    status = models.CharField(max_length=10, choices=REQUEST_STATUS, default='Pending', verbose_name="Estado")

    class Meta:
        # Prevent a student from requesting the same exact exam slot multiple times
        unique_together = ['student', 'calendar_exam']
        ordering = ['-request_timestamp']

    def __str__(self):
        return f"Solicitud de {self.student.get_full_name()} para {self.calendar_exam}"

