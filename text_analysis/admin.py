from django.contrib import admin
from .models import TextSource, TextThreatDetection

@admin.register(TextSource)
class TextSourceAdmin(admin.ModelAdmin):
    list_display = ('id', 'session', 'source_type', 'timestamp')
    list_filter = ('source_type', 'timestamp')
    search_fields = ('content',)
    date_hierarchy = 'timestamp'

@admin.register(TextThreatDetection)
class TextThreatDetectionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'source', 'threat_level', 'confidence_score', 'created_at')
    list_filter = ('threat_level',)
    search_fields = ('context',)
    date_hierarchy = 'created_at'
