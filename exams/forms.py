from django import forms
from .models import ExamRequest, CalendarExam
from django.core.exceptions import ValidationError


class ExamRequestForm(forms.ModelForm):
    class Meta:
        model = ExamRequest
        fields = ["subject", "exam_type", "request_date"]
        widgets = {
            "request_date": forms.DateInput(attrs={"type": "date"}),
        }


class CalendarExamForm(forms.ModelForm):

    class Meta:
        model = CalendarExam
        fields = ["date", "turn", "exam_type", "subject"]

        widgets = {
            "turn": forms.Select(attrs={"class": "select-modal"}),
            "exam_type": forms.Select(
                attrs={
                    "class": "select-modal",
                }
            ),
            "subject": forms.TextInput(
                attrs={
                    "placeholder": "Nombre de la asignatura",
                },
            ),
            "date": forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["exam_type"].required = False
        self.fields["subject"].required = False

    def clean(self):
        cleaned_data = super().clean()
        exam_type = cleaned_data.get("exam_type")
        subject = cleaned_data.get("subject")
        if not exam_type:
            raise ValidationError("El campo 'Tipo de examen' no puede estar vacío.")
        if not subject:
            raise ValidationError("El campo 'Asignatura' no puede estar vacío.")
        if (
            CalendarExam.objects.exclude(pk=self.instance.pk)
            .filter(date=cleaned_data.get("date"), turn=cleaned_data.get("turn"))
            .exists()
        ):
            raise ValidationError(
                "Ya existe un examen en este turno para la fecha seleccionada"
            )

        return cleaned_data
