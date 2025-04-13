import time
import random
import json
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from core.models import ThreatDetection, ThreatLevel, AnalysisSession
from core.tasks import process_text_analysis
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from core.consumers import ThreatNotificationConsumer

class Command(BaseCommand):
    help = 'Simulate real-time threat detection'

    def add_arguments(self, parser):
        parser.add_argument(
            '--duration',
            type=int,
            default=30,
            help='Duration of the simulation in seconds'
        )
        parser.add_argument(
            '--interval',
            type=float,
            default=5.0,
            help='Interval between threat checks in seconds'
        )
        parser.add_argument(
            '--user',
            default=None,
            help='Username of the user to use for the simulation (defaults to first superuser)'
        )
        parser.add_argument(
            '--detection-rate',
            type=float,
            default=0.3,
            help='Probability of detecting a threat at each interval (0.0-1.0)'
        )

    def handle(self, *args, **options):
        duration = options['duration']
        interval = options['interval']
        username = options['user']
        detection_rate = max(0.0, min(1.0, options['detection_rate']))
        
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
        
        self.stdout.write(self.style.SUCCESS(
            f'Starting real-time threat detection simulation for user {user.username}\n'
            f'Duration: {duration} seconds, Interval: {interval} seconds, Detection rate: {detection_rate:.1%}'
        ))
        
        # Create a multimodal analysis session
        session = AnalysisSession.objects.create(
            user=user,
            session_type='multimodal',
            status='processing',
            metadata={'simulation': True}
        )
        
        # Set up WebSocket channel for notifications
        channel_layer = get_channel_layer()
        
        # Sample input sources to simulate
        phishing_texts = [
            "Urgent: Your account has been compromised. Click here to reset: http://malicious-site.com/reset",
            "This is your IT department. We need your password for verification.",
            "You've won a free iPhone! Click to claim your prize: http://fake-prize.net",
            "Your package delivery failed. Confirm your address: http://tracking-phish.co/verify",
            "Security alert: Unusual activity detected. Please verify your account details immediately."
        ]
        
        # Run the simulation
        start_time = time.time()
        end_time = start_time + duration
        iteration = 0
        
        try:
            while time.time() < end_time:
                iteration += 1
                current_time = time.time() - start_time
                
                self.stdout.write(f'Iteration {iteration}: {current_time:.1f}s elapsed')
                
                # Simulate threat detection
                if random.random() < detection_rate:
                    threat_type = random.choice(['text', 'visual', 'audio'])
                    threat_level = random.choice([ThreatLevel.LOW, ThreatLevel.MEDIUM, ThreatLevel.HIGH, ThreatLevel.CRITICAL])
                    
                    self.stdout.write(self.style.WARNING(
                        f'Detected {threat_level} threat in {threat_type} input!'
                    ))
                    
                    # Create threat detection
                    threat = ThreatDetection.objects.create(
                        user=user,
                        threat_level=threat_level,
                        description=f'Simulation threat detected in {threat_type} input',
                        source_type=threat_type,
                        confidence_score=random.uniform(0.7, 0.98)
                    )
                    
                    # Send notification via WebSocket
                    notification_data = {
                        'id': threat.id,
                        'level': threat.threat_level,
                        'description': threat.description,
                        'source_type': threat.source_type,
                        'timestamp': timezone.now().isoformat(),
                        'confidence': threat.confidence_score
                    }
                    
                    async_to_sync(channel_layer.group_send)(
                        f"user_{user.id}_notifications",
                        {
                            'type': 'threat_notification',
                            'data': notification_data
                        }
                    )
                    
                    # For text threats, actually process the text using the task
                    if threat_type == 'text':
                        text = random.choice(phishing_texts)
                        self.stdout.write(f'Processing text: "{text[:50]}..."')
                        process_text_analysis.delay(text, user.id, session.id)
                else:
                    self.stdout.write('No threats detected in this iteration')
                
                # Check if we've reached the end
                if time.time() + interval >= end_time:
                    break
                    
                # Wait for the next interval
                time.sleep(interval)
                
            # Update session
            session.status = 'completed'
            session.end_time = timezone.now()
            session.save()
            
            # Final statistics
            total_threats = ThreatDetection.objects.filter(
                user=user,
                created_at__gte=session.start_time,
                created_at__lte=session.end_time
            ).count()
            
            self.stdout.write(self.style.SUCCESS(
                f'\nSimulation completed!\n'
                f'Duration: {time.time() - start_time:.1f} seconds\n'
                f'Iterations: {iteration}\n'
                f'Threats detected: {total_threats}'
            ))
            
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING('\nSimulation interrupted by user'))
            # Update session
            session.status = 'interrupted'
            session.end_time = timezone.now()
            session.save()
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'\nError during simulation: {str(e)}'))
            # Update session
            session.status = 'failed'
            session.end_time = timezone.now()
            session.save() 