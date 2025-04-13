import time
import json
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from core.models import ThreatDetection, AnalysisSession
from core.groq_utils import GroqClient
from text_analysis.models import TextSource, TextThreatDetection
from visual.models import VisualCapture, VisualThreatDetection
from audio.models import AudioCapture, AudioThreatDetection
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Start real-time threat detection without simulation'

    def add_arguments(self, parser):
        parser.add_argument(
            '--interval',
            type=float,
            default=5.0,
            help='Interval between threat checks in seconds'
        )
        parser.add_argument(
            '--user',
            default=None,
            help='Username of the user to use for detection (defaults to first superuser)'
        )
        parser.add_argument(
            '--duration',
            type=int,
            default=0,
            help='Duration to run in seconds (0 = indefinite until stopped)'
        )

    def handle(self, *args, **options):
        interval = options['interval']
        username = options['user']
        duration = options['duration']
        
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
            f'Starting real-time threat detection for user {user.username}\n'
            f'Interval: {interval} seconds, Duration: {"indefinite" if duration == 0 else f"{duration} seconds"}'
        ))
        
        # Initialize the Groq client
        groq_client = GroqClient()
        
        # Create a multimodal analysis session
        session = AnalysisSession.objects.create(
            user=user,
            session_type='multimodal',
            status='processing',
            metadata={'real_detection': True}
        )
        
        # Set up WebSocket channel for notifications
        channel_layer = get_channel_layer()
        
        # Run the detection loop
        start_time = time.time()
        end_time = start_time + duration if duration > 0 else float('inf')
        iteration = 0
        
        try:
            while time.time() < end_time:
                iteration += 1
                current_time = time.time() - start_time
                
                self.stdout.write(f'Iteration {iteration}: {current_time:.1f}s elapsed')
                
                # Collect system data for real threat detection
                # 1. System logs analysis
                system_logs = self._collect_system_logs()
                if system_logs:
                    self._analyze_text(groq_client, system_logs, user, session, channel_layer, "system_logs")
                
                # 2. Network traffic analysis
                network_data = self._collect_network_data()
                if network_data:
                    self._analyze_text(groq_client, network_data, user, session, channel_layer, "network_traffic")
                
                # 3. Process monitoring
                process_data = self._collect_process_data()
                if process_data:
                    self._analyze_text(groq_client, process_data, user, session, channel_layer, "process_data")
                
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
                f'\nDetection completed!\n'
                f'Duration: {time.time() - start_time:.1f} seconds\n'
                f'Iterations: {iteration}\n'
                f'Threats detected: {total_threats}'
            ))
            
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING('\nDetection interrupted by user'))
            # Update session
            session.status = 'interrupted'
            session.end_time = timezone.now()
            session.save()
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'\nError during detection: {str(e)}'))
            logger.exception("Error in real-time detection")
            # Update session
            session.status = 'failed'
            session.end_time = timezone.now()
            session.save()
    
    def _collect_system_logs(self):
        """Collect recent system logs for analysis"""
        # In a real implementation, this would tail system logs
        # For this example, we'll return a sample log entry
        return "Last login: Sat Apr 12 14:30:22 on ttys000"
    
    def _collect_network_data(self):
        """Collect network traffic data for analysis"""
        # In a real implementation, this would use a packet capture library
        # For this example, we'll return sample network data
        return "TCP connection established to 192.168.1.100:443"
    
    def _collect_process_data(self):
        """Collect running process information for analysis"""
        # In a real implementation, this would query OS for process list
        # For this example, we'll return sample process data
        return "chrome.exe, python.exe, explorer.exe"
    
    def _analyze_text(self, groq_client, text, user, session, channel_layer, source_type="system"):
        """Analyze text content using Groq API"""
        self.stdout.write(f"Analyzing {source_type}: {text[:50]}...")
        
        # Store text source
        text_source = TextSource.objects.create(
            session=session,
            content=text,
            source_type=source_type
        )
        
        # Analyze with Groq
        try:
            analysis_result = groq_client.analyze_text(text)
            if not analysis_result:
                return
            
            # Parse JSON response
            result = analysis_result
            
            # If threat detected, create a threat detection record
            if result.get('threat_detected', False):
                threat = ThreatDetection.objects.create(
                    user=user,
                    threat_level=result.get('threat_level', 'LOW'),
                    description=result.get('description', 'Unknown threat'),
                    source_type='text',
                    confidence_score=result.get('confidence_score', 0.5)
                )
                
                # Create text-specific threat detection directly
                text_threat = TextThreatDetection.objects.create(
                    user=user,
                    threat_level=result.get('threat_level', 'LOW'),
                    description=result.get('description', 'Unknown threat'),
                    source_type='text',
                    confidence_score=result.get('confidence_score', 0.5),
                    source=text_source,
                    start_index=0,
                    end_index=len(text),
                    context=text,
                    entities=json.dumps(result.get('indicators', [])),
                    sentiment_score=-0.7  # Default negative sentiment for threats
                )
                
                # Send notification via WebSocket
                notification_data = {
                    'id': text_threat.id,
                    'level': text_threat.threat_level,
                    'description': text_threat.description,
                    'source_type': 'text',
                    'timestamp': timezone.now().isoformat(),
                    'confidence': text_threat.confidence_score
                }
                
                async_to_sync(channel_layer.group_send)(
                    f"user_{user.id}_notifications",
                    {
                        'type': 'threat_notification',
                        'data': notification_data
                    }
                )
                
                self.stdout.write(self.style.WARNING(
                    f'Detected {threat.threat_level} threat in {source_type}!'
                ))
            else:
                self.stdout.write('No threats detected in this analysis')
                
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Error analyzing text: {str(e)}'))
            logger.exception("Error in text analysis") 