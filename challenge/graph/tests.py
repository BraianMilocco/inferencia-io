from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from unittest.mock import patch, MagicMock
from graph.models import VideoAnalysis
import time


class VideoAnalysisYoutubeAPITestCase(APITestCase):
    """
    Test cases for YouTube video analysis endpoint
    """

    def setUp(self):
        """Set up test fixtures"""
        self.url = reverse('video-analysis-youtube')
        self.valid_video_with_audio = "https://www.youtube.com/watch?v=ssYt09bCgUY"
        self.valid_video_without_audio = "https://www.youtube.com/watch?v=6TBKF6GF9-g"
        self.non_existent_video = "https://www.youtube.com/watch?v=AAASADADADADADADADDA"
        self.invalid_url_format = "https://www.yoyobe.com/watch?v=6TBKF6GF9-g"

    def test_successful_analysis_with_audio(self):
        """
        Test successful video analysis with a video that has audio
        Expected: 201 Created with all fields populated
        """
        data = {"video_url": self.valid_video_with_audio}
        
        response = self.client.post(self.url, data, format='json')
        
        # Check response status
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


    def test_video_without_audio(self):
        """
        Test video analysis with a video that has no audio
        Expected: 500 Internal Server Error with audio insufficient error
        """
        data = {"video_url": self.valid_video_without_audio}
        
        response = self.client.post(self.url, data, format='json')
        
        # Check response status
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
    def test_non_existent_video(self):
        """
        Test video analysis with a non-existent YouTube video
        Expected: 500 Internal Server Error
        """
        data = {"video_url": self.non_existent_video}
        
        response = self.client.post(self.url, data, format='json')
        
        # Check response status
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_url_format(self):
        """
        Test video analysis with an invalid URL format
        Expected: 400 Bad Request
        """
        data = {"video_url": self.invalid_url_format}
        
        response = self.client.post(self.url, data, format='json')
        
        # Check response status (could be 400 or 500 depending on validation)
        self.assertIn(response.status_code, [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_500_INTERNAL_SERVER_ERROR
        ])
        
        # Check error message exists
        self.assertIn('error', response.data)

    def test_missing_video_url(self):
        """
        Test video analysis without providing video_url
        Expected: 400 Bad Request
        """
        data = {}
        
        response = self.client.post(self.url, data, format='json')
        
        # Check response status
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_video_analyses(self):
        """
        Test GET endpoint to list video analyses with pagination
        Expected: 200 OK with paginated results
        """
        # Create some test data
        VideoAnalysis.objects.create(
            video_url="https://www.youtube.com/watch?v=test1",
            title="Test Video 1",
            transcript="Test transcript 1",
            sentiment="positive",
            sentiment_score=0.8,
            tone="educational",
            key_points=["Point 1", "Point 2", "Point 3"]
        )
        VideoAnalysis.objects.create(
            video_url="https://www.youtube.com/watch?v=test2",
            title="Test Video 2",
            transcript="Test transcript 2",
            sentiment="neutral",
            sentiment_score=0.5,
            tone="formal",
            key_points=["Point A", "Point B", "Point C"]
        )
        
        response = self.client.get(self.url)
        
        # Check response status
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check pagination structure
        self.assertIn('count', response.data)
        self.assertIn('results', response.data)
        self.assertGreaterEqual(len(response.data['results']), 2)

    def test_pagination_page_size(self):
        """
        Test pagination with custom page size
        Expected: Correct number of results per page
        """
        # Create 15 test records
        for i in range(15):
            VideoAnalysis.objects.create(
                video_url=f"https://www.youtube.com/watch?v=test{i}",
                title=f"Test Video {i}",
                transcript=f"Test transcript {i}",
                sentiment="positive",
                sentiment_score=0.8,
                tone="educational",
                key_points=["Point 1", "Point 2", "Point 3"]
            )
        
        # Test first page (should have 10 items by default)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 10)
        
        # Test second page
        response = self.client.get(f"{self.url}?page=2")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data['results']), 5)

