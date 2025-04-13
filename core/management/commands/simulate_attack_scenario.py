import time
import random
import json
import os
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from django.conf import settings
from django.core.files.base import ContentFile
from core.models import ThreatDetection, ThreatLevel, AnalysisSession
from visual.models import VisualCapture, VisualThreatDetection
from audio.models import AudioCapture, AudioThreatDetection
from text_analysis.models import TextSource, TextThreatDetection
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.conf import settings
from PIL import Image, ImageDraw
import base64
import io
import numpy as np

class Command(BaseCommand):
    help = 'Simulate a realistic cyber attack scenario with visual, audio, and text threats'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user',
            default=None,
            help='Username of the user to use for the simulation (defaults to first superuser)'
        )
        parser.add_argument(
            '--duration',
            type=int,
            default=300,  # 5 minutes
            help='Duration of the scenario in seconds'
        )
        parser.add_argument(
            '--speed',
            type=float,
            default=1.0,
            help='Speed multiplier for the scenario (2.0 = twice as fast)'
        )

    def handle(self, *args, **options):
        username = options['user']
        duration = options['duration']
        speed = options['speed']
        
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
            f'Starting attack scenario simulation for user {user.username}\n'
            f'Duration: {duration} seconds, Speed: {speed}x'
        ))
        
        # Create a multimodal analysis session
        session = AnalysisSession.objects.create(
            user=user,
            session_type='multimodal',
            status='processing',
            metadata={'simulation': True, 'scenario': 'attack'}
        )
        
        # Set up WebSocket channel for notifications
        channel_layer = get_channel_layer()
        
        # Define the attack scenario stages
        scenario = [
            # Initial recon stage
            {
                'time': 0,
                'event': 'text',
                'content': 'Receiving email from unknown sender...',
                'threat_level': ThreatLevel.LOW,
                'threat_desc': 'Email from unknown sender detected'
            },
            {
                'time': 5,
                'event': 'text',
                'content': 'Subject: Urgent Security Update Required\nDear User, Our security system has detected unusual activity on your account. Please verify your identity by clicking the link below: http://security-verify-portal.com/verify?id=123456',
                'threat_level': ThreatLevel.MEDIUM,
                'threat_desc': 'Potential phishing attempt detected with suspicious URL'
            },
            {
                'time': 15,
                'event': 'visual',
                'content': 'phishing_site.jpg',
                'bounding_box': {'x': 20, 'y': 30, 'width': 60, 'height': 40},
                'threat_level': ThreatLevel.HIGH,
                'threat_desc': 'Fake login page detected with suspicious URL'
            },
            {
                'time': 25,
                'event': 'audio',
                'content': 'Please enter your username and password to verify your account security.',
                'threat_level': ThreatLevel.HIGH,
                'threat_desc': 'Audio requesting sensitive credentials detected'
            },
            {
                'time': 40,
                'event': 'text',
                'content': 'Downloading file: security_update.exe...',
                'threat_level': ThreatLevel.CRITICAL,
                'threat_desc': 'Potentially malicious executable download detected'
            },
            {
                'time': 50,
                'event': 'visual',
                'content': 'malware_alert.jpg',
                'bounding_box': {'x': 10, 'y': 10, 'width': 80, 'height': 60},
                'threat_level': ThreatLevel.CRITICAL,
                'threat_desc': 'Malware installation attempt detected'
            },
            {
                'time': 65,
                'event': 'text',
                'content': 'System scanning files... Unusual activity detected.',
                'threat_level': ThreatLevel.MEDIUM,
                'threat_desc': 'Suspicious system file access detected'
            },
            {
                'time': 80,
                'event': 'visual',
                'content': 'data_exfiltration.jpg',
                'bounding_box': {'x': 30, 'y': 20, 'width': 40, 'height': 30},
                'threat_level': ThreatLevel.CRITICAL,
                'threat_desc': 'Data exfiltration attempt detected'
            },
            {
                'time': 95,
                'event': 'audio',
                'content': 'Your computer has been infected with a virus. Call this number immediately: 1-800-123-4567',
                'threat_level': ThreatLevel.HIGH,
                'threat_desc': 'Tech support scam detected in audio'
            },
            {
                'time': 110,
                'event': 'text',
                'content': 'Connecting to remote server... transferring data...',
                'threat_level': ThreatLevel.CRITICAL,
                'threat_desc': 'Unauthorized data transfer to unknown server'
            },
            {
                'time': 130,
                'event': 'visual',
                'content': 'ransomware.jpg',
                'bounding_box': {'x': 5, 'y': 5, 'width': 90, 'height': 80},
                'threat_level': ThreatLevel.CRITICAL,
                'threat_desc': 'Ransomware encryption process detected'
            }
        ]
        
        # Run the scenario
        start_time = time.time()
        end_time = start_time + duration
        
        # Adjust event times for simulation speed
        scenario_events = [
            {**event, 'time': event['time'] / speed}
            for event in scenario
        ]
        
        try:
            last_event_time = 0
            for event in scenario_events:
                # Wait until it's time for this event
                event_time = event['time']
                wait_time = event_time - (time.time() - start_time)
                
                if wait_time > 0:
                    time.sleep(wait_time)
                
                # Process the event
                self.stdout.write(self.style.WARNING(
                    f'[{time.time() - start_time:.1f}s] {event["event"].upper()} EVENT: {event["threat_desc"]}'
                ))
                
                # Create a threat detection
                if event['event'] == 'visual':
                    self._create_visual_threat(user, session, event, channel_layer)
                elif event['event'] == 'audio':
                    self._create_audio_threat(user, session, event, channel_layer)
                elif event['event'] == 'text':
                    self._create_text_threat(user, session, event, channel_layer)
                
                # Check if we've reached the end of the scenario
                if time.time() >= end_time:
                    break
                
                # Update last event time
                last_event_time = event_time
            
            # If we still have time, fill with random events
            remaining_time = end_time - time.time()
            if remaining_time > 10:
                self.stdout.write(self.style.WARNING(
                    f'\nScenario completed with {remaining_time:.1f}s remaining. Filling with random events...'
                ))
                
                # Fill remaining time with random events
                while time.time() < end_time:
                    wait_time = random.uniform(5, 15) / speed
                    if time.time() + wait_time >= end_time:
                        break
                    
                    time.sleep(wait_time)
                    
                    # Random event type
                    event_type = random.choice(['visual', 'audio', 'text'])
                    threat_level = random.choice(list(ThreatLevel.choices))[0]
                    
                    # Generate random event
                    event = {
                        'event': event_type,
                        'content': f'Random {event_type} input',
                        'threat_level': threat_level,
                        'threat_desc': f'Random {threat_level.lower()} threat in {event_type}'
                    }
                    
                    if event_type == 'visual':
                        event['bounding_box'] = {
                            'x': random.randint(10, 70),
                            'y': random.randint(10, 70), 
                            'width': random.randint(20, 50),
                            'height': random.randint(20, 50)
                        }
                        self._create_visual_threat(user, session, event, channel_layer)
                    elif event_type == 'audio':
                        self._create_audio_threat(user, session, event, channel_layer)
                    elif event_type == 'text':
                        self._create_text_threat(user, session, event, channel_layer)
            
            # Mark session as completed
            session.status = 'completed'
            session.end_time = timezone.now()
            session.save()
            
            self.stdout.write(self.style.SUCCESS(
                f'\nAttack scenario simulation completed successfully!\n'
                f'Duration: {time.time() - start_time:.1f} seconds'
            ))
            
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING('\nSimulation interrupted by user'))
            session.status = 'interrupted'
            session.end_time = timezone.now()
            session.save()
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'\nError during simulation: {str(e)}'))
            session.status = 'failed'
            session.end_time = timezone.now()
            session.save()
    
    def _create_visual_threat(self, user, session, event, channel_layer):
        """Create a visual threat and send notification"""
        # Create visual capture
        capture = VisualCapture.objects.create(
            session=session,
            timestamp=timezone.now(),
            metadata={
                'simulation': True,
                'scenario': 'attack'
            }
        )
        
        # Generate a simple image if needed (since we can't use actual files)
        image_data = self._generate_threat_image(event['content'], event['bounding_box'])
        capture.image.save(f"sim_{event['content']}", ContentFile(image_data))
        
        # Create threat detection
        threat = VisualThreatDetection.objects.create(
            user=user,
            capture=capture,
            threat_level=event['threat_level'],
            description=event['threat_desc'],
            source_type='visual',
            confidence_score=random.uniform(0.8, 0.98),
            bounding_box=event['bounding_box'],
            detected_objects=[{'label': 'suspicious_element', 'confidence': 0.95}]
        )
        
        # Send WebSocket notification
        self._send_notification(channel_layer, user, threat, event)
        
        # Also send visual feed update
        self._send_visual_update(channel_layer, user, capture, event)
    
    def _create_audio_threat(self, user, session, event, channel_layer):
        """Create an audio threat and send notification"""
        # Create audio capture
        capture = AudioCapture.objects.create(
            session=session,
            duration=random.uniform(5.0, 15.0),
            sample_rate=44100,
            channels=2,
            timestamp=timezone.now(),
            metadata={
                'simulation': True,
                'scenario': 'attack',
                'transcription': event['content']
            }
        )
        
        # Create threat detection
        threat = AudioThreatDetection.objects.create(
            user=user,
            capture=capture,
            threat_level=event['threat_level'],
            description=event['threat_desc'],
            source_type='audio',
            confidence_score=random.uniform(0.8, 0.98),
            start_time=1.0,
            end_time=5.0,
            transcription=event['content'],
            audio_features={'pitch': 120, 'intensity': 65}
        )
        
        # Send WebSocket notification
        self._send_notification(channel_layer, user, threat, event)
        
        # Also send audio feed update
        self._send_audio_update(channel_layer, user, event)
    
    def _create_text_threat(self, user, session, event, channel_layer):
        """Create a text threat and send notification"""
        # Create text source
        source = TextSource.objects.create(
            session=session,
            content=event['content'],
            source_type=random.choice(['email', 'chat', 'log']),
            timestamp=timezone.now(),
            metadata={
                'simulation': True,
                'scenario': 'attack'
            }
        )
        
        # Create threat detection
        start_index = 0
        end_index = min(100, len(event['content']))
        
        threat = TextThreatDetection.objects.create(
            user=user,
            source=source,
            threat_level=event['threat_level'],
            description=event['threat_desc'],
            source_type='text',
            confidence_score=random.uniform(0.8, 0.98),
            start_index=start_index,
            end_index=end_index,
            context=event['content'],
            entities=['suspicious_activity', 'threat'],
            sentiment_score=-0.7
        )
        
        # Send WebSocket notification
        self._send_notification(channel_layer, user, threat, event)
        
        # Also send text feed update
        self._send_text_update(channel_layer, user, event)
    
    def _send_notification(self, channel_layer, user, threat, event):
        """Send a threat notification via WebSocket"""
        notification_data = {
            'id': threat.id,
            'level': threat.threat_level,
            'description': threat.description,
            'source_type': threat.source_type,
            'timestamp': timezone.now().isoformat(),
            'confidence': threat.confidence_score
        }
        
        # Add source-specific data
        if event['event'] == 'visual' and 'bounding_box' in event:
            notification_data['bounding_box'] = event['bounding_box']
        
        async_to_sync(channel_layer.group_send)(
            f"user_{user.id}_notifications",
            {
                'type': 'threat_notification',
                'data': notification_data
            }
        )
    
    def _send_visual_update(self, channel_layer, user, capture, event):
        """Send visual feed update via WebSocket"""
        # In a real implementation, you would use the actual URL
        # Here we'll use a placeholder
        update_data = {
            'image_url': capture.image.url if capture.image else '/static/img/placeholder.jpg',
            'timestamp': timezone.now().isoformat()
        }
        
        async_to_sync(channel_layer.group_send)(
            f"user_{user.id}_notifications",
            {
                'type': 'visual_update',
                'data': update_data
            }
        )
    
    def _send_audio_update(self, channel_layer, user, event):
        """Send audio visualization update via WebSocket"""
        # Generate random waveform data
        amplitude_data = []
        for i in range(50):
            if 'CRITICAL' in event['threat_level'] or 'HIGH' in event['threat_level']:
                # More erratic for higher threats
                amplitude_data.append(random.uniform(0.3, 0.9))
            else:
                amplitude_data.append(random.uniform(0.1, 0.6))
        
        update_data = {
            'amplitude_data': amplitude_data,
            'timestamp': timezone.now().isoformat()
        }
        
        async_to_sync(channel_layer.group_send)(
            f"user_{user.id}_notifications",
            {
                'type': 'audio_update',
                'data': update_data
            }
        )
    
    def _send_text_update(self, channel_layer, user, event):
        """Send text feed update via WebSocket"""
        update_data = {
            'text': event['content'],
            'timestamp': timezone.now().isoformat()
        }
        
        async_to_sync(channel_layer.group_send)(
            f"user_{user.id}_notifications",
            {
                'type': 'text_update',
                'data': update_data
            }
        )
    
    def _generate_threat_image(self, image_name, bounding_box):
        """Generate a simple image for the scenario"""
        # Create a colored image with a suspicious element
        width, height = 640, 480
        image = Image.new('RGB', (width, height), color=(245, 245, 245))
        draw = ImageDraw.Draw(image)
        
        # Draw some UI elements
        draw.rectangle([10, 10, width-10, 50], fill=(200, 200, 200))
        draw.rectangle([20, 20, 100, 40], fill=(220, 220, 220))
        draw.rectangle([120, 20, 200, 40], fill=(220, 220, 220))
        draw.rectangle([220, 20, 300, 40], fill=(220, 220, 220))
        
        # Draw a suspicious element based on the bounding box
        x = int((bounding_box['x'] / 100) * width)
        y = int((bounding_box['y'] / 100) * height)
        w = int((bounding_box['width'] / 100) * width)
        h = int((bounding_box['height'] / 100) * height)
        
        if 'phishing' in image_name:
            # Draw a fake login form
            draw.rectangle([x, y, x+w, y+h], fill=(255, 255, 255), outline=(200, 200, 200))
            draw.rectangle([x+20, y+40, x+w-20, y+70], fill=(240, 240, 240))
            draw.rectangle([x+20, y+90, x+w-20, y+120], fill=(240, 240, 240))
            draw.rectangle([x+20, y+140, x+w-80, y+170], fill=(66, 133, 244))
            draw.text((x+30, y+150), "Login", fill=(255, 255, 255))
            draw.text((x+30, y+20), "Enter your credentials", fill=(0, 0, 0))
        elif 'malware' in image_name:
            # Draw a fake malware alert
            draw.rectangle([x, y, x+w, y+h], fill=(255, 50, 50), outline=(200, 0, 0))
            draw.text((x+20, y+20), "WARNING: VIRUS DETECTED", fill=(255, 255, 255))
            draw.text((x+20, y+50), "Your computer is at risk!", fill=(255, 255, 255))
        elif 'ransomware' in image_name:
            # Draw a ransomware screen
            draw.rectangle([x, y, x+w, y+h], fill=(30, 30, 30), outline=(255, 0, 0))
            draw.text((x+20, y+20), "YOUR FILES HAVE BEEN ENCRYPTED", fill=(255, 0, 0))
            draw.text((x+20, y+50), "Pay 1 Bitcoin to decrypt", fill=(255, 255, 0))
        elif 'data' in image_name:
            # Draw a data transfer screen
            draw.rectangle([x, y, x+w, y+h], fill=(30, 30, 100), outline=(50, 50, 200))
            draw.text((x+20, y+20), "Transferring files...", fill=(255, 255, 255))
            draw.rectangle([x+20, y+50, x+w-40, y+70], fill=(50, 50, 150))
            draw.rectangle([x+20, y+50, x+int((w-40)*0.7), y+70], fill=(100, 100, 255))
        else:
            # Generic suspicious element
            draw.rectangle([x, y, x+w, y+h], fill=(255, 200, 200), outline=(255, 0, 0))
            draw.text((x+10, y+h//2), "SUSPICIOUS ACTIVITY", fill=(255, 0, 0))
        
        # Save to a bytes buffer
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG")
        return buffer.getvalue() 