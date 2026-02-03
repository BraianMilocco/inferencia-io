import os
import tempfile
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from .serializers import (
    VideoAnalysisRequestSerializer,
    VideoAnalysisResponseSerializer,
    VideoAnalysisUploadSerializer
)
from .models import VideoAnalysis
from .agents.graph import create_video_analysis_graph
from helpers import convert_errors_to_list

class VideoAnalysisYoutubeView(APIView):
    """
    API endpoint to analyze YouTube videos.
    POST /api/analyze/youtube/
    Body: {"video_url": "https://youtube.com/watch?v=xxxxx"}
    """
    
    def post(self, request):
        # Validar input
        data = request.data
        serializer = VideoAnalysisRequestSerializer(data=data)
        if not serializer.is_valid():
            error_messages = convert_errors_to_list(serializer.errors.items())
            VideoAnalysis.objects.create(
                video_url=data.get('video_url', ''),
                errors=error_messages,
            )
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        video_url = serializer.validated_data['video_url']
        # Creates a VideoAnalysis entry
        video_analysis = VideoAnalysis.objects.create(
            video_url=video_url,
        )
        try:
            # Create and invoke the graph
            graph = create_video_analysis_graph()
            result = graph.invoke({"video_url": video_url})
            
            if result.get("errors"):
                video_analysis.errors = result["errors"]
                video_analysis.save()
                return Response(
                    {
                        "error": "Error while analyzing video",
                        "details": result["errors"]
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Save analysis to DB
            video_analysis.title = result.get("title", "")
            video_analysis.duration_seconds = result.get("duration_seconds", 0)
            video_analysis.language_code = result.get("language_code", "unknown")
            video_analysis.transcript = result.get("transcript", "")
            video_analysis.sentiment = result.get("sentiment", "neutral")
            video_analysis.sentiment_score = result.get("sentiment_score", 0.5)
            video_analysis.tone = result.get("tone", "")
            video_analysis.key_points = result.get("key_points", [])
            video_analysis.save(
                update_fields=[
                    "title",
                    "duration_seconds",
                    "language_code",
                    "transcript",
                    "sentiment",
                    "sentiment_score",
                    "tone",
                    "key_points"
                ]
            )
            video_analysis.refresh_from_db()           
            # Return response
            response_serializer = VideoAnalysisResponseSerializer(video_analysis)
            return Response(
                response_serializer.data,
                status=status.HTTP_201_CREATED
            )
            
        except Exception as e:
            video_analysis.errors = [str(e)]
            video_analysis.save(
                update_fields=["errors"]
            )
            return Response(
                {
                    "error": "Unexpected error during analysis",
                    "details": str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def get(self, request):
        """List previous analyses"""
        analyses = VideoAnalysis.objects.all()[:10]  # Last 10
        serializer = VideoAnalysisResponseSerializer(analyses, many=True)
        return Response(serializer.data)


class VideoAnalysisUploadView(APIView):
    """
    API endpoint to analyze uploaded MP4 videos.
    POST /api/analyze/upload/
    Body: multipart/form-data with "video" file
    """

    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):
        serializer = VideoAnalysisUploadSerializer(data=request.data)
        if not serializer.is_valid():
            error_messages = convert_errors_to_list(serializer.errors.items())
            VideoAnalysis.objects.create(
                video_url=request.data.get('video', ''),
                errors=error_messages,
            )
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        video_file = serializer.validated_data["video"]
        temp_path = None
        video_analysis = VideoAnalysis.objects.create(
            video_url=f"upload://{video_file.name}",
        )

        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
                for chunk in video_file.chunks():
                    tmp.write(chunk)
                temp_path = tmp.name

            graph = create_video_analysis_graph()
            result = graph.invoke({
                "video_url": video_analysis.video_url,
                "video_path": temp_path,
            })

            if result.get("errors"):
                video_analysis.errors = result["errors"]
                video_analysis.save(update_fields=["errors"])
                return Response(
                    {
                        "error": "Error durante el análisis",
                        "details": result["errors"]
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            video_analysis.title = result.get("title", "")
            video_analysis.duration_seconds = result.get("duration_seconds", 0)
            video_analysis.language_code = result.get("language_code", "unknown")
            video_analysis.transcript = result.get("transcript", "")
            video_analysis.sentiment = result.get("sentiment", "neutral")
            video_analysis.sentiment_score = result.get("sentiment_score", 0.5)
            video_analysis.tone = result.get("tone", "")
            video_analysis.key_points = result.get("key_points", [])
            video_analysis.save(
                update_fields=[
                    "title",
                    "duration_seconds",
                    "language_code",
                    "transcript",
                    "sentiment",
                    "sentiment_score",
                    "tone",
                    "key_points"
                ]
            )
            video_analysis.refresh_from_db()
            response_serializer = VideoAnalysisResponseSerializer(video_analysis)
            return Response(
                response_serializer.data,
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            video_analysis.errors = [str(e)]
            video_analysis.save(update_fields=["errors"])
            return Response(
                {
                    "error": "Unexpected error during analysis",
                    "details": str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        finally:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)