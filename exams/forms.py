from django import forms
from .models import ExamRequest


class ExamRequestForm(forms.ModelForm):
    class Meta:
        model = ExamRequest
        fields = ["subject", "exam_type", "request_date"]
        widgets = {
            "request_date": forms.DateInput(attrs={"type": "date"}),
        }
