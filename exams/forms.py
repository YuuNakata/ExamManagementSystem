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


from django import forms
from django.core.exceptions import ValidationError
from .models import CalendarExam

from django import forms
from .models import CalendarExam

class CalendarExamForm(forms.ModelForm):
    # Campo subject personalizado
    subject = forms.CharField(
        label="Asignatura",
        widget=forms.TextInput(attrs={
            "placeholder": "Nombre de la asignatura",
            "class": "form-control"
        })

    )

    class Meta:
        model = CalendarExam
        fields = ["date", "turn", "exam_type", "subject"]
        
        widgets = {
            "turn": forms.Select(attrs={"class": "select-modal form-control"}),
            "exam_type": forms.Select(attrs={
                "class": "select-modal form-control",
            }),
            "date": forms.HiddenInput()
        }

    
        

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Configuración de campos requeridos
        self.fields['exam_type'].required = True
        self.fields['subject'].required = True
        
        # Estilos y clases para los campos y mensajes de error personalizados
        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': 'form-control'
            })
            if field.required:
                field.error_messages['required'] = 'Error Por favor, corrige los campos'

class GradeForm(forms.ModelForm):
    class Meta:
        model = ExamRequest
        fields = ['grade', 'comments']
        widgets = {
            
            'grade': forms.HiddenInput(
                attrs={
                    'id': 'id_grade',
                }
            ),
            'comments': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }

    def clean_grade(self):
        grade = self.cleaned_data.get('grade')
        if grade is not None and not (2 <= grade <= 5):
            raise ValidationError("La calificación debe estar entre 2 y 5.")
        return grade

class ReviewRequestForm(forms.ModelForm):
    class Meta:
        model = ReviewRequest
        fields = ['reason']
        widgets = {
            'reason': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Explica los motivos de tu revisión...'
            }),
        }
        error_messages = {
            'reason': {
                'required': "Por favor ingresa el motivo de la revisión",
            }
        }
       