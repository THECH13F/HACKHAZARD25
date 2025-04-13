from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class ThreatLevel(models.TextChoices):
    LOW = 'LOW', 'Low'
    MEDIUM = 'MEDIUM', 'Medium'
    HIGH = 'HIGH', 'High'
    CRITICAL = 'CRITICAL', 'Critical'

class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class ThreatDetection(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    threat_level = models.CharField(max_length=10, choices=ThreatLevel.choices)
    description = models.TextField()
    source_type = models.CharField(max_length=50)  # visual, audio, text, or multimodal
    confidence_score = models.FloatField()
    is_false_positive = models.BooleanField(default=False)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='reviewed_threats'
    )

    def mark_as_reviewed(self, user, is_false_positive=False):
        self.reviewed_at = timezone.now()
        self.reviewed_by = user
        self.is_false_positive = is_false_positive
        self.save()

    class Meta:
        ordering = ['-created_at']

class AnalysisSession(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    session_type = models.CharField(max_length=50)  # visual, audio, text, or multimodal
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, default='active')
    metadata = models.JSONField(default=dict)

    def end_session(self):
        self.end_time = timezone.now()
        self.status = 'completed'
        self.save()

    class Meta:
        ordering = ['-start_time']
