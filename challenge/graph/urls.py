from django.urls import path
from .views import VideoAnalysisYoutubeView

urlpatterns = [
    path('analyze/youtube/', VideoAnalysisYoutubeView.as_view(), name='video-analysis-youtube'),
]   