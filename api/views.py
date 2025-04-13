from django.shortcuts import render
from rest_framework import views, status, viewsets
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.contrib.auth import authenticate
from django.conf import settings
import logging
import json
import base64
from core.tasks import process_visual_analysis, process_audio_analysis, process_text_analysis
from core.models import ThreatDetection, AnalysisSession
from drf_yasg.utils import swagger_auto_schema
from .serializers import (
    VisualAnalysisRequestSerializer, AudioAnalysisRequestSerializer,
    TextAnalysisRequestSerializer, MultimodalAnalysisRequestSerializer,
    ThreatDetectionSerializer, AnalysisSessionSerializer,
    UserSerializer
)

logger = logging.getLogger('rt_cta')

class LoginView(TokenObtainPairView):
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        operation_description="Authenticate user and obtain JWT token pair",
        responses={
            200: "Authentication successful",
            401: "Authentication failed"
        }
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

class RefreshTokenView(TokenRefreshView):
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        operation_description="Refresh JWT access token",
        responses={
            200: "Token refreshed successfully",
            401: "Invalid token"
        }
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

class UserProfileView(views.APIView):
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Get user profile information",
        responses={200: UserSerializer}
    )
    def get(self, request):
        """Get the user's profile information"""
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

class BaseAnalysisView(views.APIView):
    permission_classes = [IsAuthenticated]

    def handle_analysis(self, request, analysis_type):
        try:
            # Log the analysis request
            logger.info(f"Received {analysis_type} analysis request from user {request.user}")
            
            # Process the request (to be implemented in subclasses)
            result = self.process_request(request)
            
            return Response(result, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error in {analysis_type} analysis: {str(e)}")
            return Response(
                {"error": f"Error processing {analysis_type} analysis: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def process_request(self, request):
        raise NotImplementedError("Subclasses must implement process_request method")

class VisualAnalysisView(BaseAnalysisView):
    @swagger_auto_schema(
        request_body=VisualAnalysisRequestSerializer,
        operation_description="Submit an image for visual threat analysis",
        responses={200: "Analysis task submitted successfully"}
    )
    def post(self, request, *args, **kwargs):
        return self.handle_analysis(request, "visual")

    def process_request(self, request):
        # Validate input using serializer
        serializer = VisualAnalysisRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        image_data = serializer.validated_data['image']
        session_id = serializer.validated_data.get('session_id')
        
        # Submit task for asynchronous processing
        task = process_visual_analysis.delay(
            image_data, 
            request.user.id,
            session_id
        )
        
        return {
            "message": "Visual analysis task submitted successfully",
            "task_id": task.id,
            "status": "processing"
        }

class AudioAnalysisView(BaseAnalysisView):
    @swagger_auto_schema(
        request_body=AudioAnalysisRequestSerializer,
        operation_description="Submit audio data for threat analysis",
        responses={200: "Analysis task submitted successfully"}
    )
    def post(self, request, *args, **kwargs):
        return self.handle_analysis(request, "audio")

    def process_request(self, request):
        # Validate input using serializer
        serializer = AudioAnalysisRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        audio_data = serializer.validated_data['audio']
        transcription = serializer.validated_data.get('transcription', '')
        session_id = serializer.validated_data.get('session_id')
        
        # Submit task for asynchronous processing
        task = process_audio_analysis.delay(
            audio_data,
            transcription,
            request.user.id,
            session_id
        )
        
        return {
            "message": "Audio analysis task submitted successfully",
            "task_id": task.id,
            "status": "processing"
        }

class TextAnalysisView(BaseAnalysisView):
    @swagger_auto_schema(
        request_body=TextAnalysisRequestSerializer,
        operation_description="Submit text content for threat analysis",
        responses={200: "Analysis task submitted successfully"}
    )
    def post(self, request, *args, **kwargs):
        return self.handle_analysis(request, "text")

    def process_request(self, request):
        # Validate input using serializer
        serializer = TextAnalysisRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        text = serializer.validated_data['text']
        session_id = serializer.validated_data.get('session_id')
        
        # Submit task for asynchronous processing
        task = process_text_analysis.delay(
            text,
            request.user.id,
            session_id
        )
        
        return {
            "message": "Text analysis task submitted successfully",
            "task_id": task.id,
            "status": "processing"
        }

class MultimodalAnalysisView(BaseAnalysisView):
    @swagger_auto_schema(
        request_body=MultimodalAnalysisRequestSerializer,
        operation_description="Submit multiple data types (text, image, audio) for combined threat analysis",
        responses={200: "Analysis tasks submitted successfully"}
    )
    def post(self, request, *args, **kwargs):
        return self.handle_analysis(request, "multimodal")

    def process_request(self, request):
        # Validate input using serializer
        serializer = MultimodalAnalysisRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Create a multimodal analysis session
        session = AnalysisSession.objects.create(
            user=request.user,
            session_type='multimodal',
            status='processing'
        )
        
        tasks = []
        
        # Process each input type if available
        if 'text' in serializer.validated_data:
            task = process_text_analysis.delay(
                serializer.validated_data['text'],
                request.user.id,
                session.id
            )
            tasks.append({"type": "text", "task_id": task.id})
            
        if 'image' in serializer.validated_data:
            task = process_visual_analysis.delay(
                serializer.validated_data['image'],
                request.user.id,
                session.id
            )
            tasks.append({"type": "visual", "task_id": task.id})
            
        if 'audio' in serializer.validated_data:
            transcription = serializer.validated_data.get('transcription', '')
            task = process_audio_analysis.delay(
                serializer.validated_data['audio'],
                transcription,
                request.user.id,
                session.id
            )
            tasks.append({"type": "audio", "task_id": task.id})
        
        return {
            "message": "Multimodal analysis tasks submitted successfully",
            "session_id": session.id,
            "tasks": tasks,
            "status": "processing"
        }

class AnalysisResultView(views.APIView):
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Get analysis results for a specific session or the latest session",
        responses={
            200: "Analysis results retrieved successfully",
            404: "Analysis session not found"
        }
    )
    def get(self, request, session_id=None):
        """Get analysis results for a specific session or latest by type"""
        try:
            if session_id:
                # Get results for a specific session
                session = AnalysisSession.objects.get(id=session_id, user=request.user)
                
                # Get all threats detected in this session
                threats = ThreatDetection.objects.filter(
                    user=request.user,
                    created_at__gte=session.start_time,
                    created_at__lte=session.end_time or session.updated_at
                )
                
                return Response({
                    "session": AnalysisSessionSerializer(session).data,
                    "threats": ThreatDetectionSerializer(threats, many=True).data
                })
            
            else:
                # Get analysis type from query params
                analysis_type = request.query_params.get('type', 'all')
                
                # Get latest session by type
                if analysis_type != 'all':
                    session = AnalysisSession.objects.filter(
                        user=request.user,
                        session_type=analysis_type
                    ).order_by('-start_time').first()
                else:
                    session = AnalysisSession.objects.filter(
                        user=request.user
                    ).order_by('-start_time').first()
                
                if not session:
                    return Response({"message": "No analysis sessions found"}, status=status.HTTP_404_NOT_FOUND)
                
                # Get all threats detected in this session
                threats = ThreatDetection.objects.filter(
                    user=request.user,
                    created_at__gte=session.start_time,
                    created_at__lte=session.end_time or session.updated_at
                )
                
                return Response({
                    "session": AnalysisSessionSerializer(session).data,
                    "threats": ThreatDetectionSerializer(threats, many=True).data
                })
                
        except AnalysisSession.DoesNotExist:
            return Response({"error": "Analysis session not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error retrieving analysis results: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
