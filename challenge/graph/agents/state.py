from typing import TypedDict, Optional, List


class VideoAnalysisState(TypedDict):
    """
    Shared state among all graph nodes.
    
    Attributes:
        video_url (str): The URL of the video to be analyzed.
        transcript (Optional[str]): The transcription of the video's audio.
        title (Optional[str]): The title of the video.
        duration_seconds (Optional[int]): The duration of the video in seconds.
        language_code (Optional[str]): The language code of the video's audio.
        sentiment (Optional[str]): The sentiment of the video content.
        sentiment_score (Optional[float]): The score representing the sentiment strength.
        tone (Optional[str]): The tone of the video content.
        key_points (Optional[List[str]]): The 3 key points of the video.
        final_result (Optional[dict]): The final result of the analysis.
        errors (Optional[List[str]]): Errors encountered during processing.
    """

    # Input
    video_url: Optional[str]
    video_path: Optional[str]
    
    # Extraction node outputs
    transcript: Optional[str]
    title: Optional[str]
    duration_seconds: Optional[int]
    language_code: Optional[str]
    
    # Sentiment analysis node outputs
    sentiment: Optional[str]
    sentiment_score: Optional[float]
    tone: Optional[str]
    
    # Structuring node outputs
    key_points: Optional[List[str]]
    
    # Final result
    final_result: Optional[dict]
    
    # Error handling
    errors: Optional[List[str]]
    status: Optional[str]  # "processing", "success", "failed"