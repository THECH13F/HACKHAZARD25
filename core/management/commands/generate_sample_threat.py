import random
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import ThreatDetection, ThreatLevel, AnalysisSession
from visual.models import VisualCapture, VisualThreatDetection
from audio.models import AudioCapture, AudioThreatDetection
from text_analysis.models import TextSource, TextThreatDetection
from django.utils import timezone

class Command(BaseCommand):
    help = 'Generate sample threat data for testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--type',
            default='all',
            choices=['all', 'visual', 'audio', 'text'],
            help='Type of threat to generate'
        )
        parser.add_argument(
            '--user',
            default=None,
            help='Username of the user to associate with the threats (defaults to first superuser)'
        )
        parser.add_argument(
            '--count',
            type=int,
            default=1,
            help='Number of threats to generate'
        )

    def handle(self, *args, **options):
        threat_type = options['type']
        username = options['user']
        count = options['count']
        
        # Get the user
        user = None
        if username:
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                self.stderr.write(self.style.ERROR(f'User {username} does not exist'))
                return
        else:
            # Get the first superuser
            user = User.objects.filter(is_superuser=True).first()
            if not user:
                self.stderr.write(self.style.ERROR('No superuser found. Please create a superuser first.'))
                return
                
        self.stdout.write(self.style.SUCCESS(f'Generating {count} sample threats of type "{threat_type}" for user {user.username}'))
        
        # Generate threats based on type
        if threat_type == 'all' or threat_type == 'visual':
            self._generate_visual_threats(user, count if threat_type == 'visual' else count // 3)
            
        if threat_type == 'all' or threat_type == 'audio':
            self._generate_audio_threats(user, count if threat_type == 'audio' else count // 3)
            
        if threat_type == 'all' or threat_type == 'text':
            self._generate_text_threats(user, count if threat_type == 'text' else count // 3)
        
        self.stdout.write(self.style.SUCCESS('Sample threats generated successfully!'))
    
    def _generate_visual_threats(self, user, count):
        """Generate sample visual threats"""
        self.stdout.write(f'Generating {count} visual threats...')
        
        for i in range(count):
            # Create session
            session = AnalysisSession.objects.create(
                user=user,
                session_type='visual',
                status='completed',
                metadata={'sample': True}
            )
            
            # Create visual capture
            capture = VisualCapture.objects.create(
                session=session,
                timestamp=timezone.now(),
                metadata={
                    'width': 1920,
                    'height': 1080,
                    'source': 'webcam',
                    'sample': True
                }
            )
            
            # Create threat
            threat_level = random.choice(list(ThreatLevel.choices))[0]
            
            threat = VisualThreatDetection.objects.create(
                user=user,
                capture=capture,
                threat_level=threat_level,
                description=f'Sample visual threat #{i+1}: Suspicious screen activity detected',
                source_type='visual',
                confidence_score=random.uniform(0.65, 0.95),
                bounding_box={'x': 100, 'y': 100, 'width': 200, 'height': 200},
                detected_objects=[{'label': 'suspicious_window', 'confidence': 0.87}]
            )
            
            self.stdout.write(f'  Created visual threat #{i+1} with level {threat_level}')
    
    def _generate_audio_threats(self, user, count):
        """Generate sample audio threats"""
        self.stdout.write(f'Generating {count} audio threats...')
        
        for i in range(count):
            # Create session
            session = AnalysisSession.objects.create(
                user=user,
                session_type='audio',
                status='completed',
                metadata={'sample': True}
            )
            
            # Create audio capture
            capture = AudioCapture.objects.create(
                session=session,
                duration=random.uniform(10.0, 60.0),
                sample_rate=44100,
                channels=2,
                timestamp=timezone.now(),
                metadata={
                    'source': 'microphone',
                    'sample': True
                }
            )
            
            # Create threat
            threat_level = random.choice(list(ThreatLevel.choices))[0]
            
            threat = AudioThreatDetection.objects.create(
                user=user,
                capture=capture,
                threat_level=threat_level,
                description=f'Sample audio threat #{i+1}: Suspicious voice pattern detected',
                source_type='audio',
                confidence_score=random.uniform(0.7, 0.98),
                start_time=random.uniform(0.0, 5.0),
                end_time=random.uniform(5.1, 10.0),
                transcription="Please provide your credit card number for verification purposes.",
                audio_features={'pitch': 120, 'intensity': 65}
            )
            
            self.stdout.write(f'  Created audio threat #{i+1} with level {threat_level}')
    
    def _generate_text_threats(self, user, count):
        """Generate sample text threats"""
        self.stdout.write(f'Generating {count} text threats...')
        
        phishing_samples = [
            "Urgent: Your account has been compromised. Please click this link to reset your password immediately: http://suspicious-site.com/reset?id=123",
            "This is your bank. We have detected unusual activity. Please verify your account by replying with your account number and PIN.",
            "Congratulations! You've won a free gift card. Click here to claim it before it expires: http://claim-prize.net/free",
            "Your package couldn't be delivered. Please verify your address by clicking: http://tracking-update.co/verify?p=456",
            "IT Department: Your password is about to expire. Please update it immediately using this secure link: http://password-reset.org/update",
        ]
        
        for i in range(count):
            # Create session
            session = AnalysisSession.objects.create(
                user=user,
                session_type='text',
                status='completed',
                metadata={'sample': True}
            )
            
            # Create text source
            content = random.choice(phishing_samples)
            source = TextSource.objects.create(
                session=session,
                content=content,
                source_type=random.choice(['email', 'chat', 'sms', 'log']),
                timestamp=timezone.now(),
                metadata={
                    'sender': 'unknown@example.com',
                    'sample': True
                }
            )
            
            # Create threat
            threat_level = random.choice(list(ThreatLevel.choices))[0]
            start_index = random.randint(0, 20)
            end_index = start_index + random.randint(50, 100)
            
            threat = TextThreatDetection.objects.create(
                user=user,
                source=source,
                threat_level=threat_level,
                description=f'Sample text threat #{i+1}: Potential phishing attempt detected',
                source_type='text',
                confidence_score=random.uniform(0.75, 0.99),
                start_index=start_index,
                end_index=min(end_index, len(content)),
                context=content,
                entities=['link', 'credentials'],
                sentiment_score=-0.8
            )
            
            self.stdout.write(f'  Created text threat #{i+1} with level {threat_level}') 