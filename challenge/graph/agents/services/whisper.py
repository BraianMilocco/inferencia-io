import os
import logging
import tempfile
import uuid
import subprocess
import json
from pydantic import BaseModel
from typing import Dict, Optional
import yt_dlp

from openai import OpenAI

# Get from settings or environment
from challenge_inferencia.settings import LLM_API_KEY
from helpers import get_iso_639_1_code

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
    language_code: Optional[str] = None
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
                logger.info("Audio downloaded", extra={"audio_path": audio_path})

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
        logger.info(f"Extracting audio from local video {video_path} to {audio_path}", extra={"video_path": video_path})
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
            duration_seconds = self._get_video_duration_seconds(video_path)
            metadata = {
                "title": os.path.splitext(os.path.basename(video_path))[0],
                "duration_seconds": duration_seconds,
                "language_code": None,
            }
            logger.info(f'metadata extracted: {metadata}', extra={"video_path": video_path})
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
            with open(audio_path, "rb") as audio_file:
                result = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="verbose_json"
                )
            logger.info("Transcription completed", extra={"audio_path": audio_path})
            return TranscriptAudioResponse(
                transcript=result.text,
                language_code=getattr(result, "language", None),
                success=True,
                error=None
            )
        except Exception as e:
            logger.exception("Error transcribing audio", extra={"audio_path": audio_path})
            return TranscriptAudioResponse(transcript=None, success=False, error=str(e))
        finally:
            # Clean up temporary file
            self.delete_temp_file(audio_path)

    def _get_video_duration_seconds(self, file_path: str) -> Optional[int]:
        """
        Gets the duration of a video in seconds.

        Args:
            file_path (str): Path to the video file

        Returns:
            Optional[int]: Duration in seconds or None if failed
        """
        logger.info(f"Getting video duration from {file_path}", extra={"file_path": file_path})
        try:
            cmd = [
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration",
                "-of", "json",
                file_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            data = json.loads(result.stdout)
            duration = float(data["format"]["duration"])
            return int(duration)
        except Exception:
            logger.exception("Failed to read video duration", extra={"file_path": file_path})
            return None

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
        if download_response.audio_path:
            self.delete_temp_file(download_response.audio_path)

        metadata = WhisperMetadata(
            title=download_response.metadata['title'],
            duration_seconds=download_response.metadata['duration_seconds'],
            language_code=download_response.metadata['language_code'],
        )
        return WhisperResponse(
            transcript=transcript_response.transcript,
            metadata=metadata,
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
            self.delete_temp_file(video_path)
            if download_response.audio_path:
                self.delete_temp_file(download_response.audio_path)
            return WhisperResponse(transcript=None, metadata=None, error=download_response.error)

        transcript_response = self.transcribe_audio(download_response.audio_path)

        metadata = WhisperMetadata(
            title=download_response.metadata['title'],
            duration_seconds=self._get_video_duration_seconds(video_path),
            # As language code is not extracted from local files, we use the one from transcription
            # And whisper returns language codes in different formats, we normalize it            
            language_code=get_iso_639_1_code(transcript_response.language_code),
        )
        self.delete_temp_file(video_path)
        return WhisperResponse(
            transcript=transcript_response.transcript,
            metadata=metadata,
            error=transcript_response.error,
        )

