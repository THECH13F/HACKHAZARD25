import os
import json
from django.core.management.base import BaseCommand
from django.conf import settings
from core.groq_utils import GroqClient

class Command(BaseCommand):
    help = 'Test the connection to Groq API'

    def add_arguments(self, parser):
        parser.add_argument(
            '--model',
            default='llama3-70b-8192',
            help='Groq model to test with'
        )
        parser.add_argument(
            '--text',
            default='This is a test message to check if the Groq API connection is working.',
            help='Text to use for the test query'
        )

    def handle(self, *args, **options):
        api_key = settings.GROQ_API_KEY
        if not api_key:
            self.stderr.write(self.style.ERROR('GROQ_API_KEY not set in environment variables'))
            return

        model = options['model']
        text = options['text']

        self.stdout.write(self.style.WARNING(f'Testing Groq API connection with model: {model}'))
        
        try:
            client = GroqClient(api_key=api_key)
            result = client.analyze_text(text, model=model)
            
            # Pretty print the result
            if isinstance(result, str):
                try:
                    result_dict = json.loads(result)
                    self.stdout.write(self.style.SUCCESS('Connection successful!'))
                    self.stdout.write(json.dumps(result_dict, indent=2))
                except json.JSONDecodeError:
                    self.stdout.write(self.style.SUCCESS('Connection successful!'))
                    self.stdout.write(result)
            else:
                self.stdout.write(self.style.SUCCESS('Connection successful!'))
                self.stdout.write(json.dumps(result, indent=2))
                
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Error connecting to Groq API: {str(e)}')) 