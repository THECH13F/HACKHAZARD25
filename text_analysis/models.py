from django.db import models
from core.models import BaseModel, ThreatDetection

class TextSource(BaseModel):
    session = models.ForeignKey('core.AnalysisSession', on_delete=models.CASCADE)
    content = models.TextField()
    source_type = models.CharField(max_length=50)  # e.g., chat, log, email
    timestamp = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(default=dict)

    class Meta:
        ordering = ['-timestamp']

class TextThreatDetection(ThreatDetection):
    source = models.ForeignKey(TextSource, on_delete=models.CASCADE)
    start_index = models.IntegerField()  # Start index of the threat in the text
    end_index = models.IntegerField()  # End index of the threat in the text
    context = models.TextField()  # Surrounding context of the threat
    entities = models.JSONField(default=list)  # Named entities found in the text
    sentiment_score = models.FloatField(null=True, blank=True)
    
    def get_threat_context(self, context_window=100):
        """Get the text context around the threat"""
        start = max(0, self.start_index - context_window)
        end = min(len(self.source.content), self.end_index + context_window)
        return self.source.content[start:end]
