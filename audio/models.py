from django.db import models
from core.models import BaseModel, ThreatDetection

class AudioCapture(BaseModel):
    session = models.ForeignKey('core.AnalysisSession', on_delete=models.CASCADE)
    audio_file = models.FileField(upload_to='audio_captures/%Y/%m/%d/')
    duration = models.FloatField()  # Duration in seconds
    sample_rate = models.IntegerField()
    channels = models.IntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(default=dict)

    class Meta:
        ordering = ['-timestamp']

class AudioThreatDetection(ThreatDetection):
    capture = models.ForeignKey(AudioCapture, on_delete=models.CASCADE)
    start_time = models.FloatField()  # Start time of the detected threat in seconds
    end_time = models.FloatField()  # End time of the detected threat in seconds
    frequency_range = models.JSONField(null=True, blank=True)  # Store frequency range of the threat
    transcription = models.TextField(null=True, blank=True)  # For speech-to-text results
    audio_features = models.JSONField(default=dict)  # Store extracted audio features

    def extract_threat_segment(self):
        """Extract the audio segment containing the threat"""
        # Implementation for extracting the specific audio segment
        pass
