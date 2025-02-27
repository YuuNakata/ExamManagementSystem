from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLES = (
        ("estudiante", "Estudiante"),
        ("profesor", "Profesor"),
        ("admin", "Administrador"),
    )
    role = models.CharField(max_length=20, choices=ROLES, default="estudiante")
    curso_programa = models.CharField(max_length=100, blank=True, null=True)
    departamento_facultad = models.CharField(max_length=100, blank=True, null=True)

    @property
    def is_admin(self):
        return self.role == "admin"

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
