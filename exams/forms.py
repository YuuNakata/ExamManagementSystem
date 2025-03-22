from django import forms
from .models import ExamRequest, CalendarExam


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
            "exam_type": forms.Select(attrs={"class": "select-modal"}),
            "subject": forms.TextInput(
                attrs={"placeholder": "Nombre de la asignatura"}
            ),
            "date": forms.DateInput(attrs={"type": "date", "class": "date-input"}),
        }
