from django import forms
from .models import Batch

class BatchForm(forms.ModelForm):
    class Meta:
        model = Batch
        fields = ['from_year', 'to_year', 'batch_type']
        widgets = {
            'from_year': forms.TextInput(attrs={'class': 'form-control year-input', 'placeholder': 'Enter start year'}),
            'to_year': forms.TextInput(attrs={'class': 'form-control year-input', 'placeholder': 'Enter end year'}),
            'batch_type': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter batch type'}),
        }
