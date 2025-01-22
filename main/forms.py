from django import forms
from .models import Batch, Graduate

class BatchForm(forms.ModelForm):
    class Meta:
        model = Batch
        fields = ['from_year', 'to_year', 'batch_type']
        widgets = {
            'from_year': forms.TextInput(attrs={'class': 'form-control year-input', 'placeholder': 'Enter start year'}),
            'to_year': forms.TextInput(attrs={'class': 'form-control year-input', 'placeholder': 'Enter end year'}),
            'batch_type': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter batch type'}),
        }

class GraduateForm(forms.ModelForm):
    class Meta:
        model = Graduate
        fields = [
            'first_name', 'middle_name', 'last_name', 'course',
            'email', 'contact', 'address', 'photo', 'batch', 'ambition'  # Include ambition
        ]

    def __init__(self, *args, **kwargs):
        exclude_batch = kwargs.pop('exclude_batch', False)  # Extract the custom argument
        super().__init__(*args, **kwargs)
        if exclude_batch:
            self.fields.pop('batch')  # Remove the 'batch' field dynamically

class GraduateAddForm(forms.ModelForm):
    class Meta:
        model = Graduate
        fields = [
            'first_name', 'middle_name', 'last_name', 'course',
            'email', 'contact', 'address', 'photo', 'batch', 'ambition'  # Include ambition
        ]

class GraduateEditForm(forms.ModelForm):
    class Meta:
        model = Graduate
        fields = [
            'first_name', 'middle_name', 'last_name', 'course',
            'email', 'contact', 'address', 'photo', 'ambition'  # Include ambition
        ]
