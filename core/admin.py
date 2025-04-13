from django.contrib import admin
from .models import ThreatDetection, AnalysisSession

@admin.register(ThreatDetection)
class ThreatDetectionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'threat_level', 'source_type', 'confidence_score', 'is_false_positive', 'created_at')
    list_filter = ('threat_level', 'source_type', 'is_false_positive')
    search_fields = ('description',)
    date_hierarchy = 'created_at'

@admin.register(AnalysisSession)
class AnalysisSessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'session_type', 'start_time', 'end_time', 'status')
    list_filter = ('session_type', 'status')
    date_hierarchy = 'start_time'
