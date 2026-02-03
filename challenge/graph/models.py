from django.db import models
from django.contrib.postgres.fields import ArrayField


class SentimentChoices(models.TextChoices):
    POSITIVE = "positive", "Positive"
    NEGATIVE = "negative", "Negative"
    NEUTRAL = "neutral", "Neutral"


class VideoAnalysis(models.Model):
    """
    Model to store the analysis of a video including its metadata,
    transcription, sentiment analysis, tone, and key points.

    Attributes:
        video_url (URLField): The URL of the video.
        created_at (DateTimeField): Timestamp when the analysis was created.
        updated_at (DateTimeField): Timestamp when the analysis was last updated.
        title (CharField): Title of the video.
        duration_seconds (IntegerField): Duration of the video in seconds.
        language_code (CharField): Language code of the video's audio.
        transcript (TextField): Transcription of the video's audio.
        sentiment (CharField): Sentiment of the video content.
        sentiment_score (FloatField): Score representing the sentiment strength.
        tone (CharField): Tone of the video content.
        key_points (ArrayField): List of 3 key points from the video.
        errors (ArrayField): List of errors encountered during processing (if any).

    Methods:
        __str__(): Returns a string representation of the analysis.
    """

    video_url = models.URLField(
        max_length=500, help_text="URL of the video to be analyzed"
    )
    created_at = models.DateTimeField(
        auto_now_add=True, help_text="Timestamp when the analysis was created"
    )
    updated_at = models.DateTimeField(
        auto_now=True, help_text="Timestamp when the analysis was last updated"
    )

    # Metadata
    title = models.CharField(
        max_length=500, blank=True, null=True, help_text="Title of the video"
    )
    duration_seconds = models.IntegerField(
        blank=True, null=True, help_text="Duration of the video in seconds"
    )
    language_code = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        help_text="Language code of the video's audio",
    )

    # Transcription
    transcript = models.TextField(
        blank=True, null=True, help_text="Transcription of the video's audio"
    )

    # Analysis
    sentiment = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        choices=SentimentChoices.choices,
        help_text="Sentiment of the video content",
    )
    sentiment_score = models.FloatField(
        blank=True, null=True, help_text="Score representing the sentiment strength"
    )
    tone = models.CharField(
        max_length=100, blank=True, null=True, help_text="Tone of the video content"
    )
    key_points = ArrayField(
        models.TextField(),
        size=3,
        help_text="The 3 key points of the video",
        blank=True,
        null=True,
    )

    # Errors (if any)
    errors = ArrayField(
        models.TextField(),
        blank=True,
        null=True,
        help_text="Errors encountered during processing",
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Video Analysis"
        verbose_name_plural = "Video Analyses"

    def __str__(self) -> str:
        return f"Analysis of {self.video_url[:50]} - {self.sentiment}"
