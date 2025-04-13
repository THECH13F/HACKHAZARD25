import os
import json
import time
from django.core.management.base import BaseCommand
from django.conf import settings
import requests


class Command(BaseCommand):
    help = 'Tests connection to the Groq API by making a simple chat completion request'

    def add_arguments(self, parser):
        parser.add_argument(
            '--verbose',
            action='store_true',
            dest='verbose',
            help='Display detailed response information',
        )

    def handle(self, *args, **options):
        api_key = settings.GROQ_API_KEY
        
        if not api_key:
            self.stderr.write(self.style.ERROR('GROQ_API_KEY not found in settings'))
            self.stderr.write(self.style.WARNING('Please set GROQ_API_KEY in your environment or settings.py'))
            return
        
        self.stdout.write(self.style.WARNING('Testing connection to Groq API...'))
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "llama3-8b-8192",
            "messages": [
                {"role": "system", "content": "You are a helpful assistant for cybersecurity."},
                {"role": "user", "content": "What are some common signs of a phishing attempt?"}
            ],
            "temperature": 0.7,
            "max_tokens": 100
        }
        
        start_time = time.time()
        
        try:
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json=payload
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            if response.status_code == 200:
                data = response.json()
                self.stdout.write(self.style.SUCCESS('✅ Connection successful!'))
                self.stdout.write(f'Response time: {duration:.2f} seconds')
                
                if options['verbose']:
                    self.stdout.write('\nResponse:')
                    self.stdout.write(json.dumps(data, indent=2))
                else:
                    # Just show the generated text
                    content = data['choices'][0]['message']['content']
                    model = data['model']
                    self.stdout.write(f'\nModel: {model}')
                    self.stdout.write(f'Response: {content}')
            else:
                self.stdout.write(self.style.ERROR(f'❌ API request failed with status code: {response.status_code}'))
                self.stdout.write(f'Error: {response.text}')
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Connection failed: {str(e)}')) 