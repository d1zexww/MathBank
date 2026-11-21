from django import forms
from .models import StudentProfile


class StudentProfileForm(forms.ModelForm):

    class Meta:
        model = StudentProfile

        fields = [
            'full_name',
            'main_subject',
            'target_score'
        ]

        labels = {
            'full_name': 'Твоё имя',
            'main_subject': 'Основной предмет',
            'target_score': 'Желаемый результат ЕГЭ'
        }

        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Например, Александр'
            }),

            'main_subject': forms.Select(attrs={
                'class': 'form-input'
            }),

            'target_score': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': 'Например, 85',
                'min': 1,
                'max': 100
            })
        }