from django.contrib import admin
from .models import VisualCapture, VisualThreatDetection

@admin.register(VisualCapture)
class VisualCaptureAdmin(admin.ModelAdmin):
    list_display = ('id', 'session', 'timestamp')
    list_filter = ('timestamp',)
    date_hierarchy = 'timestamp'

@admin.register(VisualThreatDetection)
class VisualThreatDetectionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'capture', 'threat_level', 'confidence_score', 'created_at')
    list_filter = ('threat_level',)
    date_hierarchy = 'created_at'
