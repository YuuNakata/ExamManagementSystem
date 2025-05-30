from django import forms
from .models import ExamRequest, CalendarExam
from .models import ExamRequest, ReviewRequest
from django.core.exceptions import ValidationError


# class ExamRequestForm(forms.ModelForm):
#     class Meta:
#         model = ExamRequest
#         widgets = {
#             "request_date": forms.DateInput(attrs={"type": "date"}),
#         }


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
        

        return cleaned_data
class GradeForm(forms.ModelForm):
    class Meta:
        model = ExamRequest
        fields = ['grade', 'comments']
        widgets = {
            'grade': forms.NumberInput(attrs={'min': 0, 'max': 100, 'step': 0.1, 'class': 'form-control'}),
            'comments': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }

class ReviewRequestForm(forms.ModelForm):
    class Meta:
        model = ReviewRequest
        fields = ['reason']
        widgets = {
            'reason': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Explica los motivos de tu revisión...'}),
        }