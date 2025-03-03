from django.db import models

from django.db import models
from users.models import User


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
