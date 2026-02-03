import os
import tempfile
from pathlib import Path
from rest_framework.response import Response
from rest_framework import status, generics, mixins
from rest_framework.parsers import MultiPartParser, FormParser
from .serializers import (
    VideoAnalysisRequestSerializer,
    VideoAnalysisResponseSerializer,
    VideoAnalysisUploadSerializer
)
from .models import VideoAnalysis
from .agents.graph import create_video_analysis_graph
from helpers import convert_errors_to_list, process_graph_result


class VideoAnalysisYoutubeView(mixins.ListModelMixin, generics.GenericAPIView):
    """
    API endpoint to analyze YouTube videos.
    GET /api/analyze/youtube/ - List previous analyses (paginated)
    POST /api/analyze/youtube/ - Analyze a new YouTube video
    Body: {"video_url": "https://youtube.com/watch?v=xxxxx"}
    """
    queryset = VideoAnalysis.objects.exclude(
        video_url__istartswith="upload://"
    ).filter(
        video_url__icontains="youtube."
    ).order_by('-created_at')
    serializer_class = VideoAnalysisResponseSerializer
    
    def post(self, request):
        # Validar input
        data = request.data
        serializer = VideoAnalysisRequestSerializer(data=data)
        if not serializer.is_valid():
            error_messages = convert_errors_to_list(serializer.errors)
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
            
            process_graph_result(video_analysis, result, title=True)
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
    
    def get(self, request, *args, **kwargs):
        """List previous analyses with pagination"""
        return self.list(request, *args, **kwargs)


class VideoAnalysisUploadView(mixins.ListModelMixin, generics.GenericAPIView):
    """
    API endpoint to analyze uploaded MP4 videos.
    GET /api/analyze/upload/ - List previous analyses (paginated)
    POST /api/analyze/upload/ - Analyze an uploaded video
    Body: multipart/form-data with "video" file
    """
    queryset = VideoAnalysis.objects.filter(
        video_url__istartswith="upload://"
    ).order_by('-created_at')
    serializer_class = VideoAnalysisResponseSerializer
    parser_classes = (MultiPartParser, FormParser)

    def get(self, request, *args, **kwargs):
        """List previous analyses with pagination"""
        return self.list(request, *args, **kwargs)

    def post(self, request):
        serializer = VideoAnalysisUploadSerializer(data=request.data)
        if not serializer.is_valid():
            error_messages = convert_errors_to_list(serializer.errors)
            VideoAnalysis.objects.create(
                video_url=request.data.get('video', ''),
                errors=error_messages,
            )
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        video_file = serializer.validated_data["video"]
        clean_title = Path(video_file.name).stem.replace("_", " ").replace("-", " ").strip()
        temp_path = None
        video_analysis = VideoAnalysis.objects.create(
            video_url=f"upload://{video_file.name}",
            title=clean_title
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

            process_graph_result(video_analysis, result, title=False)
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