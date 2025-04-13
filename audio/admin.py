from django.contrib import admin
from .models import AudioCapture, AudioThreatDetection

@admin.register(AudioCapture)                                               
class AudioCaptureAdmin(admin.ModelAdmin):
    list_display = ('id', 'session', 'duration', 'sample_rate', 'channels', 'timestamp')
    list_filter = ('sample_rate', 'channels', 'timestamp')
    date_hierarchy = 'timestamp'

@admin.register(AudioThreatDetection)
class AudioThreatDetectionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'capture', 'threat_level', 'start_time', 'end_time', 'confidence_score')
    list_filter = ('threat_level',)
    date_hierarchy = 'created_at'
