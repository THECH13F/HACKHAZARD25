from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
# Register your viewsets here
# router.register(r'threats', views.ThreatViewSet)

urlpatterns = [
    path('', include(router.urls)),
    
    # Authentication endpoints
    path('auth/login/', views.LoginView.as_view(), name='token-obtain-pair'),
    path('auth/refresh/', views.RefreshTokenView.as_view(), name='token-refresh'),
    path('auth/user/', views.UserProfileView.as_view(), name='user-profile'),
    
    # Analysis endpoints
    path('analyze/visual/', views.VisualAnalysisView.as_view(), name='visual-analysis'),
    path('analyze/audio/', views.AudioAnalysisView.as_view(), name='audio-analysis'),
    path('analyze/text/', views.TextAnalysisView.as_view(), name='text-analysis'),
    path('analyze/multimodal/', views.MultimodalAnalysisView.as_view(), name='multimodal-analysis'),
    
    # Results endpoints
    path('results/', views.AnalysisResultView.as_view(), name='analysis-results'),
    path('results/<int:session_id>/', views.AnalysisResultView.as_view(), name='session-results'),
] 