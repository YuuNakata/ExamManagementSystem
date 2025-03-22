from django.db import models

from django.db import models
from users.models import User
from datetime import date


class ExamRequest(models.Model):
    EXAM_TYPES = (
        ("suficiencia", "Suficiencia"),
        ("premio", "Premio"),
    )

    student = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="exam_requests"
    )
    subject = models.CharField(max_length=100, verbose_name="Asignatura")
    exam_type = models.CharField(max_length=20, choices=EXAM_TYPES)
    request_date = models.DateField(verbose_name="Fecha de solicitud")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student} - {self.subject}"


class CalendarExam(models.Model):
    EXAM_TYPES = (
        ("suficiencia", "Suficiencia"),
        ("premio", "Premio"),
    )
    TURN_CHOICES = [
        ("1", "8:00-9:20"),
        ("2", "9:30-10:50"),
        ("3", "11:00-12:20"),
        ("4", "12:30-1:50"),
        ("5", "2:00-3:20"),
        ("6", "3:30-4:50"),
    ]
    date = models.DateField("Fecha del examen", default=date.today)
    turn = models.CharField("Turno", max_length=1, choices=TURN_CHOICES)
    exam_type = models.CharField(max_length=20, choices=EXAM_TYPES)
    subject = models.CharField(max_length=100, verbose_name="Asignatura")

    def __str__(self):
        return f"{self.get_day_of_week_display()} - {self.get_turn_display()}"
