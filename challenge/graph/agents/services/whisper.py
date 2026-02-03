import os
import logging
import tempfile
import uuid
import subprocess
from pydantic import BaseModel
from typing import Dict, Optional
import yt_dlp

from openai import OpenAI

# Get from settings or environment
from challenge_inferencia.settings import LLM_API_KEY

logger = logging.getLogger(__name__)

class WhisperMetadata(BaseModel):
    title: Optional[str]
    duration_seconds: Optional[int]
    language_code: Optional[str]

class WhisperResponse(BaseModel):
    """
    Response object for Whisper transcription
    """
    transcript: Optional[str]
    metadata: Optional[WhisperMetadata]
    error: Optional[str] = None

class DownloadAudioResponse(BaseModel):
    audio_path: Optional[str]
    metadata: Optional[Dict]
    success: bool
    error: Optional[str] = None

class TranscriptAudioResponse(BaseModel):
    transcript: Optional[str]
    success: bool
    error: Optional[str] = None

class WhisperTranscriptionService:
    """ 
    Service to extract transcriptions using OpenAI's Whisper 
    
    Attributes:
        client (OpenAI): OpenAI client for API interactions
        temp_dir (str): Directory for temporary file storage

    Methods:
        download_audio(video_url: str) -> str: Downloads audio from a YouTube video
        transcribe_audio(audio_path: str) -> str: Transcribes audio using Whisper
        get_transcript(video_url: str) -> WhisperResponse: Gets the transcription of a video using Whisper.

    """
    
    def __init__(self):
        self.client = OpenAI(api_key=LLM_API_KEY)
        self.temp_dir = tempfile.gettempdir()
        logger.info("WhisperTranscriptionService initialized", extra={"temp_dir": self.temp_dir})

    def delete_temp_file(self, file_path: str):
        """
        Deletes a temporary file.
        
        Args:
            file_path (str): Path to the file
        """
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
            logger.info("Temporary file removed", extra={"file_path": file_path})

    def download_audio(self, video_url: str) -> DownloadAudioResponse:
        """
        Downloads audio from a YouTube video and saves it to a temporary file.
        
        Args:
            video_url (str): URL of the YouTube video

        Returns:
            DownloadAudioResponse: The response object containing the audio path, metadata, success status, and error message if any
        """
        audio_path = os.path.join(self.temp_dir, 'temp_audio.mp3')
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': audio_path.replace('.mp3', ''),
            'quiet': True,
            'no_warnings': True,
        }
        
        logger.info("Starting audio download", extra={"video_url": video_url})
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=True)
                logger.info(f"Audio downloaded - info {info.keys()}", extra={"audio_path": audio_path})
                # Extract metadata
                logger.info("EXTRACTING METADATA")
                keys = ['title', 'duration', 'language', 'language_preference', 'subtitles', 'ext', 'description', "duration_string", 'has_drm', 'preference']
                for key in keys:
                    logger.info(f"{key}: {info.get(key)}")
                
                language = info.get('language', None)
                if language is not None:
                    language = language.lower().split('-')[0].strip()
                metadata = {
                    'title': info.get('title', ''),
                    'duration_seconds': info.get('duration', 0),
                    'language_code': language,
                }
                
            return DownloadAudioResponse(
                audio_path=audio_path,
                metadata=metadata,
                success=True,
                error=None
            )
        except yt_dlp.utils.DownloadError as e:
            logger.exception("DownloadError while downloading audio", extra={"video_url": video_url})
            return DownloadAudioResponse(
                audio_path=None,
                metadata=None,
                success=False,
                error=f"DownloadError while downloading audio: {str(e)}"
            )
        except Exception as e:
            logger.exception("Error while downloading audio", extra={"video_url": video_url})
            return DownloadAudioResponse(
                audio_path=None,
                metadata=None,
                success=False,
                error=f"Error while downloading audio: {str(e)}"
            )

    def extract_audio_from_video(self, video_path: str) -> DownloadAudioResponse:
        """
        Extracts audio from a local video file using ffmpeg.
        """
        audio_path = os.path.join(self.temp_dir, f"temp_audio_{uuid.uuid4().hex}.mp3")
        logger.info("Extracting audio from local video", extra={"video_path": video_path})
        try:
            subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-i",
                    video_path,
                    "-vn",
                    "-acodec",
                    "libmp3lame",
                    "-q:a",
                    "2",
                    audio_path,
                ],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            metadata = {
                "title": os.path.splitext(os.path.basename(video_path))[0],
                "duration_seconds": 0,
                "language_code": None,
            }
            return DownloadAudioResponse(
                audio_path=audio_path,
                metadata=metadata,
                success=True,
                error=None,
            )
        except Exception as e:
            logger.exception("Error extracting audio from video", extra={"video_path": video_path})
            return DownloadAudioResponse(
                audio_path=None,
                metadata=None,
                success=False,
                error=f"Error extracting audio from video: {str(e)}",
            )

    def transcribe_audio(self, audio_path: str) -> TranscriptAudioResponse:
        """
        Transcribes audio using OpenAI's Whisper.
        
        Args:
            audio_path (str): Path to the audio file

        Returns:
            TranscriptAudioResponse: The response object containing the transcript, success status, and error message if any
        """

        logger.info("Starting transcription", extra={"audio_path": audio_path})
        try:
            with open(audio_path, 'rb') as audio_file:
                transcript = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="text"
                )
            
            logger.info("Transcription finished")
            return TranscriptAudioResponse(
                transcript=transcript,
                success=True,
                error=None
            )
            
        except Exception as e:
            logger.exception("Error while transcribing audio", extra={"audio_path": audio_path})
            return TranscriptAudioResponse(
                transcript=None,
                success=False,
                error=f"Error while transcribing audio: {str(e)}"
            )
        finally:
            # Clean up temporary file
            self.delete_temp_file(audio_path)
    
    def get_transcript(self, video_url: str) -> WhisperResponse:
        """
        Gets the transcription of a video using Whisper
        
        Args:
            video_url (str): URL of the YouTube video

        Returns:
            WhisperResponse: The response object containing the transcript and metadata
        """
        logger.info("Getting transcript", extra={"video_url": video_url})
        download_response = self.download_audio(video_url)
        if not download_response.success:
            if download_response.audio_path:
                self.delete_temp_file(download_response.audio_path)
            logger.error("Download failed", extra={"error": download_response.error})
            return WhisperResponse(
                transcript=None,
                metadata=None,
                error=download_response.error,
            )

        transcript_response = self.transcribe_audio(download_response.audio_path)
        return WhisperResponse(
            transcript=transcript_response.transcript,
            metadata=WhisperMetadata(
                title=download_response.metadata['title'],
                duration_seconds=download_response.metadata['duration_seconds'],
                language_code=download_response.metadata['language_code'],
            ),
            error=transcript_response.error,
        )

    def get_transcript_from_file(self, video_path: str) -> WhisperResponse:
        """
        Gets the transcription from a local video file.

        Args:
            video_path (str): Path to the local video file
        Returns:
            WhisperResponse: The response object containing the transcript and metadata
        """
        download_response = self.extract_audio_from_video(video_path)
        if not download_response.success:
            # Delete temp audio file if exists
            if download_response.audio_path:
                self.delete_temp_file(download_response.audio_path)
            self.delete_temp_file(video_path)
            return WhisperResponse(
                transcript=None,
                metadata=None,
                error=download_response.error,
            )

        transcript_response = self.transcribe_audio(download_response.audio_path)

        self.delete_temp_file(video_path)

        return WhisperResponse(
            transcript=transcript_response.transcript,
            metadata=WhisperMetadata(
                title=download_response.metadata['title'],
                duration_seconds=download_response.metadata['duration_seconds'],
                language_code=download_response.metadata['language_code'],
            ),
            error=transcript_response.error,
        )
