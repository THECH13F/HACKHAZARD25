import json
import logging
from celery import shared_task
from .groq_utils import GroqClient
from .models import ThreatDetection, AnalysisSession, ThreatLevel
from django.contrib.auth.models import User
import base64
import io
from PIL import Image
import cv2
import numpy as np

logger = logging.getLogger('rt_cta')
groq_client = GroqClient()

@shared_task
def process_visual_analysis(image_data, user_id, session_id=None):
    """
    Process visual data for threat analysis
    
    Args:
        image_data (str): Base64 encoded image data
        user_id (int): User ID who initiated the analysis
        session_id (int, optional): Analysis session ID
        
    Returns:
        dict: Analysis results
    """
    try:
        logger.info(f"Processing visual analysis for user {user_id}")
        
        # Get the user
        user = User.objects.get(id=user_id)
        
        # Create or get session
        session = None
        if session_id:
            session = AnalysisSession.objects.get(id=session_id)
        else:
            session = AnalysisSession.objects.create(
                user=user,
                session_type='visual',
                status='processing'
            )
        
        # Process image data
        image_bytes = base64.b64decode(image_data)
        image = Image.open(io.BytesIO(image_bytes))
        
        # Convert to OpenCV format
        cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        # Save the image to VisualCapture model
        # Code for saving image to model
        
        # Use Groq for analysis
        # Note: This is a placeholder as we don't have image analysis yet
        analysis_result = {
            "threat_detected": False,
            "threat_level": "LOW",
            "confidence_score": 0.1,
            "threat_type": "NONE",
            "description": "No threats detected in image",
            "indicators": []
        }
        
        # If a threat is detected, save it
        if analysis_result["threat_detected"]:
            threat = ThreatDetection.objects.create(
                user=user,
                threat_level=analysis_result["threat_level"],
                description=analysis_result["description"],
                source_type="visual",
                confidence_score=analysis_result["confidence_score"]
            )
        
        # Update session status
        session.status = 'completed'
        session.save()
        
        return analysis_result
    
    except Exception as e:
        logger.error(f"Error in visual analysis task: {str(e)}")
        if session:
            session.status = 'failed'
            session.save()
        return {"error": str(e)}

@shared_task
def process_audio_analysis(audio_data, transcription, user_id, session_id=None):
    """
    Process audio data for threat analysis
    
    Args:
        audio_data (str): Base64 encoded audio data
        transcription (str): Transcribed text from audio
        user_id (int): User ID who initiated the analysis
        session_id (int, optional): Analysis session ID
        
    Returns:
        dict: Analysis results
    """
    try:
        logger.info(f"Processing audio analysis for user {user_id}")
        
        # Get the user
        user = User.objects.get(id=user_id)
        
        # Create or get session
        session = None
        if session_id:
            session = AnalysisSession.objects.get(id=session_id)
        else:
            session = AnalysisSession.objects.create(
                user=user,
                session_type='audio',
                status='processing'
            )
        
        # Use Groq for analysis of the transcription
        analysis_result = groq_client.analyze_audio(transcription)
        
        # Parse the JSON result
        if isinstance(analysis_result, str):
            analysis_result = json.loads(analysis_result)
        
        # If a threat is detected, save it
        if analysis_result.get("threat_detected", False):
            threat = ThreatDetection.objects.create(
                user=user,
                threat_level=analysis_result["threat_level"],
                description=analysis_result["description"],
                source_type="audio",
                confidence_score=analysis_result["confidence_score"]
            )
        
        # Update session status
        session.status = 'completed'
        session.save()
        
        return analysis_result
    
    except Exception as e:
        logger.error(f"Error in audio analysis task: {str(e)}")
        if session:
            session.status = 'failed'
            session.save()
        return {"error": str(e)}

@shared_task
def process_text_analysis(text, user_id, session_id=None):
    """
    Process text data for threat analysis
    
    Args:
        text (str): Text to analyze
        user_id (int): User ID who initiated the analysis
        session_id (int, optional): Analysis session ID
        
    Returns:
        dict: Analysis results
    """
    try:
        logger.info(f"Processing text analysis for user {user_id}")
        
        # Get the user
        user = User.objects.get(id=user_id)
        
        # Create or get session
        session = None
        if session_id:
            session = AnalysisSession.objects.get(id=session_id)
        else:
            session = AnalysisSession.objects.create(
                user=user,
                session_type='text',
                status='processing'
            )
        
        # Use Groq for analysis
        analysis_result = groq_client.analyze_text(text)
        
        # Parse the JSON result
        if isinstance(analysis_result, str):
            analysis_result = json.loads(analysis_result)
        
        # If a threat is detected, save it
        if analysis_result.get("threat_detected", False):
            threat = ThreatDetection.objects.create(
                user=user,
                threat_level=analysis_result["threat_level"],
                description=analysis_result["description"],
                source_type="text",
                confidence_score=analysis_result["confidence_score"]
            )
        
        # Update session status
        session.status = 'completed'
        session.save()
        
        return analysis_result
    
    except Exception as e:
        logger.error(f"Error in text analysis task: {str(e)}")
        if session:
            session.status = 'failed'
            session.save()
        return {"error": str(e)} 