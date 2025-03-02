from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User
from .models import RequestExam

class UserRegisterForm(UserCreationForm):
    username = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    email = forms.EmailField(
        max_length=254,
        required=True,
        widget=forms.EmailInput(attrs={"class": "form-control"}),
    )
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
        required=True,
    )
    password2 = forms.CharField(
        label="Confirm Password",
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
            "password1",
            "password2",
            "role",
            "curso_programa",
            "departamento_facultad",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].help_text = ""
        self.fields["password1"].help_text = ""
        self.fields["password2"].help_text = ""


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
            "role": forms.Select(attrs={"class": "form-control"}),
            "curso_programa": forms.TextInput(attrs={"class": "form-control"}),
            "departamento_facultad": forms.TextInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].help_text = ""

class AnnoRequest(forms.ModelForm):
    class Meta:
        model = RequestExam
        fields = ["anno"]
        widget = { "anno": forms.Select()}