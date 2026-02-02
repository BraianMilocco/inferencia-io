import os
import tempfile
from pydantic import BaseModel
from typing import Dict, Optional
import yt_dlp
from openai import OpenAI

# Get from settings or environment
from challenge_inferencia.settings import LLM_API_KEY

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

    def delete_temp_file(self, file_path: str):
        """
        Deletes a temporary file.
        
        Args:
            file_path (str): Path to the file
        """
        if os.path.exists(file_path):
            os.remove(file_path)

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
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=True)
                print(f"Audio downloaded to {audio_path}")
                print(f"Video info: {info}")
                # Extract metadata
                metadata = {
                    'title': info.get('title', ''),
                    'duration_seconds': info.get('duration', 0),
                    'language_code': info.get('language', None),
                }
                
            return DownloadAudioResponse(
                audio_path=audio_path,
                metadata=metadata,
                success=True,
                error=None
            )
            
        except Exception as e:
            return DownloadAudioResponse(
                audio_path=None,
                metadata=None,
                success=False,
                error=f"Error while downloading audio: {str(e)}"
            )
    
    def transcribe_audio(self, audio_path: str) -> TranscriptAudioResponse:
        """
        Transcribes audio using OpenAI's Whisper.
        
        Args:
            audio_path (str): Path to the audio file

        Returns:
            TranscriptAudioResponse: The response object containing the transcript, success status, and error message if any
        """

        try:
            with open(audio_path, 'rb') as audio_file:
                transcript = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="text"
                )
            
            return TranscriptAudioResponse(
                transcript=transcript,
                success=True,
                error=None
            )
            
        except Exception as e:
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
        # Download audio
        download_response = self.download_audio(video_url)
        if not download_response.success:
            # Delete temp file if exists
            self.delete_temp_file(download_response.audio_path)
            return WhisperResponse(
                transcript=None,
                metadata=None,
                error=download_response.error,
            )

        # Transcript audio
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