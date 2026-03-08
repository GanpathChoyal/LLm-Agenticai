from django.contrib import admin
from .models import Patient, DiagnosticInput, DiagnosticReport

admin.site.register(Patient)
admin.site.register(DiagnosticInput)
admin.site.register(DiagnosticReport)
