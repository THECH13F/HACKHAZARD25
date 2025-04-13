from django.db import models
from core.models import BaseModel, ThreatDetection
from django.contrib.auth.models import User

class VisualCapture(BaseModel):
    session = models.ForeignKey('core.AnalysisSession', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='visual_captures/%Y/%m/%d/')
    timestamp = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(default=dict)  # Store additional metadata like resolution, source, etc.

    class Meta:
        ordering = ['-timestamp']

class VisualThreatDetection(ThreatDetection):
    capture = models.ForeignKey(VisualCapture, on_delete=models.CASCADE)
    bounding_box = models.JSONField(null=True, blank=True)  # Store coordinates of detected threat
    detected_objects = models.JSONField(default=list)  # List of detected objects and their confidence scores
    screenshot = models.ImageField(upload_to='threat_screenshots/%Y/%m/%d/', null=True, blank=True)

    def save_screenshot(self, image_data):
        """Save a screenshot of the detected threat area"""
        # Implementation for saving the screenshot
        pass
