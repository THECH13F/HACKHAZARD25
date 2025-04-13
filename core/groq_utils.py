import os
import logging
import groq
from django.conf import settings

logger = logging.getLogger('rt_cta')

class GroqClient:
    """Utility class for interacting with Groq's API for AI inference"""
    
    def __init__(self, api_key=None):
        self.api_key = api_key or settings.GROQ_API_KEY
        # Initialize with minimal parameters for compatibility
        self.client = groq.Client(api_key=self.api_key)
        logger.info("Initialized Groq client")
    
    def analyze_text(self, text, model="llama3-70b-8192"):
        """
        Analyze text content for potential threats
        
        Args:
            text (str): The text content to analyze
            model (str): The model to use for analysis
            
        Returns:
            dict: Analysis results including threat detection and confidence
        """
        try:
            logger.info(f"Analyzing text with Groq model: {model}")
            
            prompt = f"""
            You are a cybersecurity threat detection system. 
            Analyze the following text for potential security threats such as phishing attempts, 
            social engineering, malware indications, or suspicious instructions.
            
            Text: {text}
            
            Provide your analysis in the following JSON format:
            {{
                "threat_detected": true/false,
                "threat_level": "LOW"/"MEDIUM"/"HIGH"/"CRITICAL",
                "confidence_score": 0.0-1.0,
                "threat_type": "string",
                "description": "string",
                "indicators": ["string", "string"]
            }}
            
            Only provide the JSON output, nothing else.
            """
            
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a cybersecurity threat detection AI."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=1000,
            )
            
            # Extract and parse the JSON response
            result = response.choices[0].message.content
            logger.info(f"Groq text analysis completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing text with Groq: {str(e)}")
            raise
    
    def analyze_image(self, image_data, prompt, model="llama3-70b-8192"):
        """
        Analyze image content for potential threats
        
        Args:
            image_data (bytes): The image data to analyze
            prompt (str): Additional prompt to guide the analysis
            model (str): The model to use for analysis
            
        Returns:
            dict: Analysis results including threat detection and confidence
        """
        # Note: Image analysis will require a multimodal model
        # This is a placeholder for future implementation
        logger.warning("Image analysis with Groq not implemented yet")
        return {
            "threat_detected": False,
            "message": "Image analysis not implemented yet"
        }
    
    def analyze_audio(self, audio_text, model="llama3-70b-8192"):
        """
        Analyze transcribed audio content for potential threats
        
        Args:
            audio_text (str): The transcribed audio content to analyze
            model (str): The model to use for analysis
            
        Returns:
            dict: Analysis results including threat detection and confidence
        """
        # For now, we'll use text analysis for the transcribed audio
        return self.analyze_text(audio_text, model=model) 