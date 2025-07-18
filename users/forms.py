from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User


class UserRegisterForm(UserCreationForm):
    username = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    first_name = forms.CharField(
        label="Nombres",
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    last_name = forms.CharField(
        label="Apellidos",
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    email = forms.EmailField(
        max_length=254,
        required=True,
        widget=forms.EmailInput(attrs={"class": "form-control"}),
    )
    password1 = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
        required=True,
    )
    password2 = forms.CharField(
        label="Confirmar contraseña",
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
        required=True,
    )
    role = forms.ChoiceField(
        choices=[
            ("estudiante", "Estudiante"),
            ("profesor", "Profesor"),
            ("admin", "Administrador"),
        ],
        required=True,
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    curso_programa = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    departamento_facultad = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "first_name",
            "last_name",
            "password1",
            "password2",
            "role",
            "curso_programa",
            "departamento_facultad",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Personalización de mensajes de error según la especificación
        self.error_messages['password_mismatch'] = 'Las contraseñas no coinciden.'
        self.error_messages['duplicate_username'] = 'Ya existe un usuario con este nombre.'

        for field in self.fields.values():
            field.error_messages['required'] = 'Este campo es obligatorio.'

        # Limpieza de textos de ayuda
        self.fields["username"].help_text = ""
        self.fields["password1"].help_text = ""

        # Traducción de labels
        self.fields["username"].label = "Nombre de usuario"
        self.fields["email"].label = "Correo electrónico"
        self.fields["first_name"].label = "Nombres"
        self.fields["last_name"].label = "Apellidos"
        self.fields["role"].label = "Rol"
        self.fields["curso_programa"].label = "Curso/Programa"
        self.fields["departamento_facultad"].label = "Departamento/Facultad"


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "first_name",
            "last_name",
            "role",
            "curso_programa",
            "departamento_facultad",
        ]
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "role": forms.Select(attrs={"class": "form-control"}),
            "curso_programa": forms.TextInput(attrs={"class": "form-control"}),
            "departamento_facultad": forms.TextInput(attrs={"class": "form-control"}),
        }
        error_messages = {
            'username': {
                'unique': "Ya existe un usuario con este nombre/correo.",
            },
            'email': {
                'unique': "Ya existe un usuario con este nombre/correo.",
            }
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Traducción de labels
        self.fields["username"].label = "Nombre de usuario"
        self.fields["email"].label = "Correo electrónico"
        self.fields["first_name"].label = "Nombres"
        self.fields["last_name"].label = "Apellidos"
        self.fields["role"].label = "Rol"
        self.fields["curso_programa"].label = "Curso/Programa"
        self.fields["departamento_facultad"].label = "Departamento/Facultad"

        # Hacemos que los campos de nombre y apellidos sean obligatorios
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True

        # Personalización de mensajes de error para campos requeridos
        for field in self.fields.values():
            if field.required:
                field.error_messages['required'] = 'Por favor rellene este campo'

        # Textos de ayuda
        self.fields["username"].help_text = ""
        self.fields["email"].help_text = "Ejemplo: usuario@dominio.com"
