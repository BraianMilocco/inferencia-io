import logging
from typing import Dict

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from graph.agents.state import VideoAnalysisState
from graph.agents.llm_config import get_llm
from graph.agents.services.whisper import WhisperTranscriptionService, WhisperResponse
from graph.agents.prompts import (
    node_2_system_message, node_2_human_message,
    node_3_system_message, node_3_human_message
)

logger = logging.getLogger(__name__)



class SentimentAnalysis(BaseModel):
    """Schema for sentiment analysis"""
    sentiment: str = Field(
        description="General sentiment: 'positive', 'negative', or 'neutral'"
    )
    sentiment_score: float = Field(
        description="Sentiment score from 0.0 to 1.0, where 0.0 is very negative and 1.0 is very positive"
    )
    tone: str = Field(
        description="Speaker's tone (e.g., formal, informal, technical, sarcastic, motivational, educational)"
    )


class KeyPointsExtraction(BaseModel):
    """Schema for key points extraction"""
    key_points: list[str] = Field(
        description="List of exactly 3 key points from the video, each as a complete sentence"
    )



# ============================================================================
# NODE 1: EXTRACT
# ============================================================================
def extraction_node(state: VideoAnalysisState) -> Dict:
    """
    Node 1: Extracts the transcription of the video
    
    - whisper: Uses OpenAI's Whisper (more robust, requires API key, downloads audio)

    Args:
        state (VideoAnalysisState): Current state with video URL
    Returns:
        Dict: Result containing transcript, metadata, error, and status
    """
    video_url = state["video_url"]
    logger.info("Extraction node started", extra={"video_url": video_url})

    service = WhisperTranscriptionService()
    
    result: WhisperResponse = service.get_transcript(video_url)

    if result.error:
        return {
            "errors": [result.error],
            "status": "failed"
        }

    metadata = result.metadata
    return {
        "transcript": result.transcript,
        "metadata": metadata,
        "title": metadata.title if metadata else "",
        "duration_seconds": metadata.duration_seconds if metadata else 0,
        "language_code": metadata.language_code if metadata else "unknown",
        "status": "extracted"
    }

# ============================================================================
# NODE 2: SENTIMENT AND TONE ANALYSIS
# ============================================================================
def sentiment_analysis_node(state: VideoAnalysisState) -> Dict:
    """
    Node 2: Analyzes the sentiment and tone of the content

    Args:
        state (VideoAnalysisState): Current state with transcript
    Returns:
        Dict: Result containing sentiment, score, tone, error, and status
    """
    transcript = state.get("transcript")
    logger.info("Sentiment analysis node started")
    
    # Si no hay transcripción, saltar este nodo
    if not transcript:
        logger.warning("Sentiment analysis skipped: no transcript")
        return {
            "errors": ["No transcript available"],
            "status": "skipped"
        }
    
    try:
        llm = get_llm()
        parser = PydanticOutputParser(pydantic_object=SentimentAnalysis)
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", node_2_system_message),
            ("human", node_2_human_message)
        ])
        
        chain = prompt | llm | parser
        
        # Limit the transcript to avoid exceeding token limits
        truncated_transcript = transcript[:5000] if len(transcript) > 5000 else transcript
        
        logger.info("Invoking sentiment analysis LLM", extra={"transcript_length": len(truncated_transcript)})
        result = chain.invoke({
            "transcript": truncated_transcript,
            "format_instructions": parser.get_format_instructions()
        })
        logger.info("Sentiment analysis completed")
        
        return {
            "sentiment": result.sentiment,
            "sentiment_score": result.sentiment_score,
            "tone": result.tone,
            "status": "analyzed"
        }
        
    except Exception as e:
        logger.exception("Error analyzing sentiment")
        return {
            "errors": [f"Error analyzing sentiment: {str(e)}"],
            "status": "failed"
        }       


# ============================================================================
# NODE 3: STRUCTURING AND KEY POINTS EXTRACTION
# ============================================================================
def structuring_node(state: VideoAnalysisState) -> Dict:
    """
    Node 3: Extracts the 3 key points and structures the final result

    Args:
        state (VideoAnalysisState): Current state with transcript and sentiment analysis
    
    Returns:
        Dict: Result containing final structured data or error and status
    """
    transcript = state.get("transcript")
    logger.info("Structuring node started")
    
    if not transcript:
        logger.warning("Structuring skipped: no transcript")
        return {
            "errors": ["No transcript available"],
            "status": "skipped"
        }
    
    try:
        llm = get_llm()
        parser = PydanticOutputParser(pydantic_object=KeyPointsExtraction)
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", node_3_system_message),
            ("human", node_3_human_message)
        ])
        
        chain = prompt | llm | parser
        
        # Limit the transcript
        truncated_transcript = transcript[:5000] if len(transcript) > 5000 else transcript
        
        logger.info("Invoking structuring LLM", extra={"transcript_length": len(truncated_transcript)})
        result = chain.invoke({
            "transcript": truncated_transcript,
            "format_instructions": parser.get_format_instructions()
        })
        logger.info("Structuring completed")
        
        final_result = {
            "video_metadata": {
                "title": state.get("title", ""),
                "duration_seconds": state.get("duration_seconds", 0),
                "language_code": state.get("language_code", "unknown")
            },
            "analysis": {
                "sentiment": state.get("sentiment", ""),
                "sentiment_score": state.get("sentiment_score", 0.0),
                "tone": state.get("tone", ""),
                "key_points": result.key_points
            }
        }
        
        return {
            "key_points": result.key_points,
            "final_result": final_result,
            "status": "success"
        }
        
    except Exception as e:
        logger.exception("Error analyzing structuring")
        return {
            "errors": [f"Error analyzing structuring: {str(e)}"],
            "status": "failed"
        }