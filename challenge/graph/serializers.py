from rest_framework import serializers
from .models import VideoAnalysis


class VideoAnalysisRequestSerializer(serializers.Serializer):
    """Serializer for the request"""

    video_url = serializers.URLField(
        required=True, help_text="URL of the YouTube video to analyze"
    )

    def validate_video_url(self, value):
        """Validate that the URL is from YouTube"""
        if "youtube." not in value:
            raise serializers.ValidationError("URL must be from YouTube")
        return value


class VideoAnalysisUploadSerializer(serializers.Serializer):
    """Serializer for MP4 upload requests"""

    video = serializers.FileField(required=True, help_text="MP4 video file to analyze")

    def validate_video(self, value):
        content_type = getattr(value, "content_type", "")
        if content_type and content_type != "video/mp4":
            raise serializers.ValidationError("File must be an MP4 video")
        if not value.name.lower().endswith(".mp4"):
            raise serializers.ValidationError("File must have .mp4 extension")
        return value


class VideoAnalysisResponseSerializer(serializers.ModelSerializer):
    """Serializer for the response"""

    class Meta:
        model = VideoAnalysis
        fields = [
            "id",
            "title",
            "duration_seconds",
            "language_code",
            "sentiment",
            "sentiment_score",
            "tone",
            "key_points",
        ]
        read_only_fields = fields

    def to_representation(self, instance):
        """Returns the JSON format required by the challenge"""
        return {
            "video_metadata": {
                "title": instance.title,
                "duration_seconds": instance.duration_seconds,
                "language_code": instance.language_code,
            },
            "analysis": {
                "sentiment": instance.sentiment,
                "sentiment_score": instance.sentiment_score,
                "tone": instance.tone,
                "key_points": instance.key_points,
            },
        }
