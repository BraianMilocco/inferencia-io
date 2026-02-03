from graph.models import VideoAnalysis


def convert_errors_to_list(serializer_errors: dict) -> list[str]:
    """
    Converts serializer errors to a list of strings

    Args:
        serializer_errors (dict): Dictionary of serializer errors
    Returns:
        list[str]: List of errors as strings
    """
    error_messages = list()
    for field, errors in serializer_errors.items():
        for err in errors:
            error_messages.append(f"{field}: {err}")
    return error_messages


LANGUAGE_CODE_MAP = {
    "english": "en",
    "spanish": "es",
    "portuguese": "pt",
    "french": "fr",
    "german": "de",
    "italian": "it",
    "chinese": "zh",
    "japanese": "ja",
    "korean": "ko",
    "arabic": "ar",
    "russian": "ru",
    "hindi": "hi",
}


def get_iso_639_1_code(language_code: str) -> str:
    """
    Converts a language code to its ISO 639-1 code
    Args:
        language_code (str): The input language code
    Returns:
        str: The ISO 639-1 code
    """
    code = language_code.lower()
    return LANGUAGE_CODE_MAP.get(code, None)


def process_graph_result(
    video_analysis: VideoAnalysis, result: dict, title: bool = True
) -> tuple[bool, dict]:
    """
    Process graph result and update video_analysis.

    Args:
        video_analysis (VideoAnalysis): The VideoAnalysis instance to update
        result (dict): The result from the graph invocation

    Returns:
        tuple[bool, dict]: (success flag, error details if any)
    """
    update_fields = [
        "duration_seconds",
        "language_code",
        "transcript",
        "sentiment",
        "sentiment_score",
        "tone",
        "key_points",
    ]
    if result.get("errors"):
        video_analysis.errors = result["errors"]
        video_analysis.save(update_fields=["errors"])
        return False, {
            "error": "Error while analyzing video",
            "details": result["errors"],
        }
    if title:
        video_analysis.title = result.get("title", "")
        update_fields.append("title")
    video_analysis.duration_seconds = result.get("duration_seconds", 0)
    video_analysis.language_code = result.get("language_code", "unknown")
    video_analysis.transcript = result.get("transcript", "")
    video_analysis.sentiment = result.get("sentiment", "neutral")
    video_analysis.sentiment_score = result.get("sentiment_score", 0.5)
    video_analysis.tone = result.get("tone", "")
    video_analysis.key_points = result.get("key_points", [])

    video_analysis.save(update_fields=update_fields)

    return True, None
