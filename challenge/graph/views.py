from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import (
    VideoAnalysisRequestSerializer,
    VideoAnalysisResponseSerializer
)
from .models import VideoAnalysis
from .agents.graph import create_video_analysis_graph


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
            error_messages = list()
            for field, errors in serializer.errors.items():
                for err in errors:
                    error_messages.append(f"{field}: {err}")
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
                        "error": "Error durante el análisis 2",
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