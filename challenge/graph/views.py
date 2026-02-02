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
        serializer = VideoAnalysisRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        video_url = serializer.validated_data['video_url']
        
        try:
            # Create and invoke the graph
            graph = create_video_analysis_graph()
            result = graph.invoke({"video_url": video_url})
            
            # Verify for errors
            if result.get("errors"):
                return Response(
                    {
                        "error": "Error durante el análisis",
                        "details": result["errors"]
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            # Save analysis to DB
            analysis = VideoAnalysis.objects.create(
                video_url=video_url,
                title=result.get("title", ""),
                duration_seconds=result.get("duration_seconds", 0),
                language_code=result.get("language_code", "unknown"),
                transcript=result.get("transcript", ""),
                sentiment=result.get("sentiment", "neutral"),
                sentiment_score=result.get("sentiment_score", 0.5),
                tone=result.get("tone", ""),
                key_points=result.get("key_points", [])
            )
            
            # Return response
            response_serializer = VideoAnalysisResponseSerializer(analysis)
            return Response(
                response_serializer.data,
                status=status.HTTP_201_CREATED
            )
            
        except Exception as e:
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