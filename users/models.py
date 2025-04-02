from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLES = (
        ("estudiante", "Estudiante"),
        ("profesor", "Profesor"),
        ("admin", "Administrador"),
    )
    first_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100, blank=True, null=True)
    role = models.CharField(max_length=20, choices=ROLES, default="estudiante")
    curso_programa = models.CharField(max_length=100, blank=True, null=True)
    departamento_facultad = models.CharField(max_length=100, blank=True, null=True)

    @property
    def is_admin(self):
        return self.role == "admin"

    @property
    def is_teacher(self):
        return self.role == "profesor"

    @property
    def is_student(self):
        return self.role == "estudiante"

    @property
    def full_name(self):
        return self.first_name if self.first_name else "" + " " + self.last_name if self.last_name else ""

    groups = models.ManyToManyField(
        "auth.Group",
        related_name="customuser_set",
        blank=True,
        help_text="The groups this user belongs to.",
    )
    user_permissions = models.ManyToManyField(
        "auth.Permission",
        related_name="customuser_permissions_set",
        blank=True,
        help_text="Specific permissions for this user.",
    )

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
