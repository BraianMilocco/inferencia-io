from django.contrib import admin
from .models import VideoAnalysis


@admin.register(VideoAnalysis)
class VideoAnalysisAdmin(admin.ModelAdmin):
    list_display = ("id", "video_url", "tone", "sentiment", "created_at")
    search_fields = ("video_url", "title", "tone", "sentiment")
