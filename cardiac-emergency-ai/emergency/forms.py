from django import forms
from .models import Patient, DiagnosticInput

class UploadFilesForm(forms.ModelForm):
    class Meta:
        model = DiagnosticInput
        fields = ['report_file', 'ecg_file', 'xray_file']
        widgets = {
            'report_file': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,image/*'}),
            'ecg_file': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'xray_file': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }
