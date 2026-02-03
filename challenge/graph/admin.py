from django.contrib import admin
from .models import VideoAnalysis

@admin.register(VideoAnalysis)
class VideoAnalysisAdmin(admin.ModelAdmin):
        #video_url (URLField): The URL of the video.
        #created_at (DateTimeField): Timestamp when the analysis was created.
        #updated_at (DateTimeField): Timestamp when the analysis was last updated.
        #title (CharField): Title of the video.
        #duration_seconds (IntegerField): Duration of the video in seconds.
        #language_code (CharField): Language code of the video's audio.
        #transcript (TextField): Transcription of the video's audio.
        #sentiment (CharField): Sentiment of the video content.
        #sentiment_score (FloatField): Score representing the sentiment strength.
        #tone (CharField): Tone of the video content.
    list_display = ('id', 'video_url', 'tone', 'sentiment', 'created_at')
    search_fields = ('video_url', 'title', 'tone', 'sentiment')
