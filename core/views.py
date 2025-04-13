from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import ThreatDetection, AnalysisSession

# Create your views here.

@login_required
def dashboard(request):
    """Main dashboard view"""
    context = {
        'user': request.user,
        'active_tab': 'dashboard'
    }
    return render(request, 'index.html', context)

@login_required
def threat_data(request):
    """API view to get threat data for the dashboard"""
    user = request.user
    
    # Get recent threats
    recent_threats = ThreatDetection.objects.filter(user=user).order_by('-created_at')[:10]
    
    # Get threat counts by level
    threat_counts = {
        'LOW': ThreatDetection.objects.filter(user=user, threat_level='LOW').count(),
        'MEDIUM': ThreatDetection.objects.filter(user=user, threat_level='MEDIUM').count(),
        'HIGH': ThreatDetection.objects.filter(user=user, threat_level='HIGH').count(),
        'CRITICAL': ThreatDetection.objects.filter(user=user, threat_level='CRITICAL').count(),
    }
    
    # Get threat counts by source type
    source_counts = {
        'visual': ThreatDetection.objects.filter(user=user, source_type='visual').count(),
        'audio': ThreatDetection.objects.filter(user=user, source_type='audio').count(),
        'text': ThreatDetection.objects.filter(user=user, source_type='text').count(),
    }
    
    # Get most recent session status
    latest_sessions = {
        'visual': AnalysisSession.objects.filter(user=user, session_type='visual').order_by('-start_time').first(),
        'audio': AnalysisSession.objects.filter(user=user, session_type='audio').order_by('-start_time').first(),
        'text': AnalysisSession.objects.filter(user=user, session_type='text').order_by('-start_time').first(),
    }
    
    session_status = {
        'visual': latest_sessions['visual'].status if latest_sessions['visual'] else 'inactive',
        'audio': latest_sessions['audio'].status if latest_sessions['audio'] else 'inactive',
        'text': latest_sessions['text'].status if latest_sessions['text'] else 'inactive',
    }
    
    # Prepare data for response
    threats_data = []
    for threat in recent_threats:
        threats_data.append({
            'id': threat.id,
            'level': threat.threat_level,
            'description': threat.description,
            'source_type': threat.source_type,
            'confidence': threat.confidence_score,
            'created_at': threat.created_at.isoformat(),
            'is_false_positive': threat.is_false_positive,
        })
    
    return JsonResponse({
        'threats': threats_data,
        'threat_counts': threat_counts,
        'source_counts': source_counts,
        'session_status': session_status,
    })
