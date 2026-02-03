from django.urls import path
from .views import VideoAnalysisYoutubeView, VideoAnalysisUploadView

urlpatterns = [
    path('analyze/youtube/', VideoAnalysisYoutubeView.as_view(), name='video-analysis-youtube'),
    path('analyze/upload/', VideoAnalysisUploadView.as_view(), name='video-analysis-upload'),
]   