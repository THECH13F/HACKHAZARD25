import os
import json
from django.core.management.base import BaseCommand
from django.conf import settings
from core.groq_utils import GroqClient

class Command(BaseCommand):
    help = 'Check Groq API threat detection for text, image, and audio inputs'

    def add_arguments(self, parser):
        parser.add_argument(
            '--model',
            default='llama3-70b-8192',
            help='Groq model to use for analysis'
        )
        parser.add_argument(
            '--text',
            default='This message contains a phishing attempt. Please click on this link: http://malicious-link.com and enter your password to verify your account.',
            help='Text content to analyze for threats'
        )
        parser.add_argument(
            '--audio-text',
            default='Hi, this is your bank calling. We need you to verify your account information immediately. Please provide your credit card number and security code.',
            help='Transcribed audio content to analyze for threats'
        )
        parser.add_argument(
            '--image',
            action='store_true',
            help='Test image analysis (not fully implemented yet)'
        )

    def handle(self, *args, **options):
        api_key = settings.GROQ_API_KEY
        if not api_key:
            self.stderr.write(self.style.ERROR('GROQ_API_KEY not set in environment variables'))
            return

        model = options['model']
        text = options['text']
        audio_text = options['audio_text']
        test_image = options['image']

        self.stdout.write(self.style.WARNING(f'Testing Groq threat detection with model: {model}'))
        
        try:
            client = GroqClient(api_key=api_key)
            
            # Test text analysis
            self.stdout.write(self.style.WARNING('\n1. Testing text threat detection:'))
            result = client.analyze_text(text, model=model)
            self._display_result(result, "Text Analysis")
            
            # Test audio analysis
            self.stdout.write(self.style.WARNING('\n2. Testing audio transcript threat detection:'))
            result = client.analyze_audio(audio_text, model=model)
            self._display_result(result, "Audio Analysis")
            
            # Test image analysis (if requested)
            if test_image:
                self.stdout.write(self.style.WARNING('\n3. Testing image threat detection:'))
                result = client.analyze_image(None, "Check this image for threats", model=model)
                self._display_result(result, "Image Analysis")
                
            self.stdout.write(self.style.SUCCESS('\nAll tests completed'))
                
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Error testing Groq threat detection: {str(e)}'))
    
    def _display_result(self, result, analysis_type):
        """Helper method to display analysis results"""
        self.stdout.write(f"\n{analysis_type} Result:")
        
        if isinstance(result, str):
            try:
                # Attempt to parse result as JSON
                result_dict = json.loads(result)
                self.stdout.write(json.dumps(result_dict, indent=2))
                
                # For text and audio, highlight important threat info
                if "threat_detected" in result_dict:
                    detected = result_dict.get("threat_detected")
                    level = result_dict.get("threat_level", "N/A")
                    confidence = result_dict.get("confidence_score", "N/A")
                    
                    style = self.style.ERROR if detected else self.style.SUCCESS
                    self.stdout.write(style(f"Threat Detected: {detected}"))
                    if detected:
                        self.stdout.write(style(f"Threat Level: {level}"))
                        self.stdout.write(style(f"Confidence: {confidence}"))
            except json.JSONDecodeError:
                # Not valid JSON, print as is
                self.stdout.write(result)
        else:
            # If it's already a dict or other object
            self.stdout.write(str(result)) 