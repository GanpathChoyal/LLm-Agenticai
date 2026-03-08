from django.db import models
import uuid

class Patient(models.Model):
    patient_id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True
    )
    name = models.CharField(max_length=200, null=True, blank=True)
    age = models.IntegerField(null=True, blank=True)
    sex = models.CharField(
        max_length=10,
        choices=[("M","Male"),("F","Female")],
        null=True, blank=True
    )
    arrival_time = models.DateTimeField(
        auto_now_add=True
    )
    symptoms = models.TextField(null=True, blank=True)
    onset_time = models.CharField(max_length=100, null=True, blank=True)
    
    class Meta:
        ordering = ["-arrival_time"]
    
    def __str__(self):
        return f"Patient {self.patient_id} — {self.age}yr {self.sex}"

class DiagnosticInput(models.Model):
    patient = models.OneToOneField(
        Patient,
        on_delete=models.CASCADE,
        related_name="inputs"
    )
    
    # Uploaded files
    report_file = models.FileField(
        upload_to="report_uploads/",
        null=True, blank=True
    )
    ecg_file = models.FileField(
        upload_to="ecg_uploads/",
        null=True, blank=True
    )
    xray_file = models.ImageField(
        upload_to="xray_uploads/",
        null=True, blank=True
    )
    
    # Blood values and Vitals (extracted by Gemini)
    heart_rate = models.IntegerField(null=True, blank=True)
    systolic_bp = models.IntegerField(null=True, blank=True)
    troponin = models.FloatField(null=True, blank=True)
    bnp = models.FloatField(null=True, blank=True)
    ldl = models.FloatField(null=True, blank=True)
    hba1c = models.FloatField(null=True, blank=True)
    creatinine = models.FloatField(null=True, blank=True)
    ckmb = models.FloatField(null=True, blank=True)
    ckmb = models.FloatField(null=True, blank=True)
    
    uploaded_at = models.DateTimeField(
        auto_now_add=True
    )

class DiagnosticReport(models.Model):
    
    RISK_CHOICES = [
        ("LOW", "Low"),
        ("MODERATE", "Moderate"),
        ("HIGH", "High"),
        ("CRITICAL", "Critical"),
        ("INCONCLUSIVE", "Inconclusive")
    ]
    
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name="reports"
    )
    
    # Agent outputs
    ecg_findings = models.JSONField(null=True)
    biomarker_findings = models.JSONField(null=True)
    imaging_findings = models.JSONField(null=True)
    
    # Reasoning output
    risk_level = models.CharField(
        max_length=20,
        choices=RISK_CHOICES
    )
    final_report = models.TextField()
    confidence_score = models.FloatField()
    recommended_actions = models.JSONField(
        null=True
    )
    retrieved_guidelines = models.TextField(
        null=True
    )
    
    # Agentic control
    loop_count = models.IntegerField(default=0)
    agent_agreement = models.BooleanField(
        default=True
    )
    discordant_agents = models.JSONField(
        default=list
    )
    
    # Doctor response
    doctor_confirmed = models.BooleanField(
        default=False
    )
    doctor_override = models.BooleanField(
        default=False
    )
    doctor_notes = models.TextField(
        null=True, blank=True
    )
    
    # Meta
    created_at = models.DateTimeField(
        auto_now_add=True
    )
    processing_time_seconds = models.FloatField(
        null=True
    )
    
    class Meta:
        ordering = ["-created_at"]
    
    def __str__(self):
        return f"Report — {self.patient} — {self.risk_level}"


