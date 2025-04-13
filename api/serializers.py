from rest_framework import serializers
from core.models import ThreatDetection, AnalysisSession
from visual.models import VisualCapture, VisualThreatDetection
from audio.models import AudioCapture, AudioThreatDetection
from text_analysis.models import TextSource, TextThreatDetection
from django.contrib.auth.models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        read_only_fields = fields

class ThreatDetectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ThreatDetection
        fields = ['id', 'user', 'threat_level', 'description', 'source_type', 
                 'confidence_score', 'is_false_positive', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']

class AnalysisSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnalysisSession
        fields = ['id', 'user', 'session_type', 'start_time', 'end_time', 
                 'status', 'metadata', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

class VisualCaptureSerializer(serializers.ModelSerializer):
    class Meta:
        model = VisualCapture
        fields = ['id', 'session', 'image', 'timestamp', 'metadata', 'created_at']
        read_only_fields = ['id', 'created_at']

class VisualThreatDetectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = VisualThreatDetection
        fields = ['id', 'user', 'capture', 'threat_level', 'description', 
                 'source_type', 'confidence_score', 'bounding_box', 
                 'detected_objects', 'screenshot', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']

class AudioCaptureSerializer(serializers.ModelSerializer):
    class Meta:
        model = AudioCapture
        fields = ['id', 'session', 'audio_file', 'duration', 'sample_rate',
                 'channels', 'timestamp', 'metadata', 'created_at']
        read_only_fields = ['id', 'created_at']

class AudioThreatDetectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AudioThreatDetection
        fields = ['id', 'user', 'capture', 'threat_level', 'description', 
                 'source_type', 'confidence_score', 'start_time', 'end_time',
                 'frequency_range', 'transcription', 'audio_features', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']

class TextSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = TextSource
        fields = ['id', 'session', 'content', 'source_type', 'timestamp',
                 'metadata', 'created_at']
        read_only_fields = ['id', 'created_at']

class TextThreatDetectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TextThreatDetection
        fields = ['id', 'user', 'source', 'threat_level', 'description', 
                 'source_type', 'confidence_score', 'start_index', 'end_index',
                 'context', 'entities', 'sentiment_score', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']

# Serializers for API requests
class VisualAnalysisRequestSerializer(serializers.Serializer):
    image = serializers.CharField(help_text="Base64 encoded image data")
    session_id = serializers.IntegerField(required=False, help_text="Optional session ID for continuing an existing session")

class AudioAnalysisRequestSerializer(serializers.Serializer):
    audio = serializers.CharField(help_text="Base64 encoded audio data")
    transcription = serializers.CharField(required=False, help_text="Optional transcription of the audio")
    session_id = serializers.IntegerField(required=False, help_text="Optional session ID for continuing an existing session")

class TextAnalysisRequestSerializer(serializers.Serializer):
    text = serializers.CharField(help_text="Text content to analyze")
    session_id = serializers.IntegerField(required=False, help_text="Optional session ID for continuing an existing session")

class MultimodalAnalysisRequestSerializer(serializers.Serializer):
    text = serializers.CharField(required=False, help_text="Optional text content to analyze")
    image = serializers.CharField(required=False, help_text="Optional base64 encoded image data")
    audio = serializers.CharField(required=False, help_text="Optional base64 encoded audio data")
    transcription = serializers.CharField(required=False, help_text="Optional transcription of the audio") 