from django.core.exceptions import ValidationError
from django.test import TestCase
from rest_framework.test import APIClient

from core.models import LandingVideo


class LandingVideoApiTests(TestCase):
    """The landing reel lists active clips in order with one playable URL each."""

    def setUp(self):
        self.client = APIClient()
        LandingVideo.objects.create(
            title='جولة في الواحة', description='نظرة سريعة', order=2,
            video_url='https://www.youtube.com/watch?v=abcdefghijk', duration_seconds=95,
        )
        LandingVideo.objects.create(
            title='حفل الختام', order=1,
            video_url='https://cdn.example.com/clips/closing.mp4', duration_seconds=60,
        )
        LandingVideo.objects.create(
            title='مخفي', order=0, is_active=False,
            video_url='https://www.youtube.com/watch?v=hiddenhidden',
        )

    def test_lists_active_videos_in_order(self):
        response = self.client.get('/api/landing/videos/')
        self.assertEqual(response.status_code, 200)
        rows = response.json()
        self.assertEqual([r['title'] for r in rows], ['حفل الختام', 'جولة في الواحة'])
        self.assertEqual(rows[0]['source'], 'link')
        self.assertEqual(rows[0]['video_url'], 'https://cdn.example.com/clips/closing.mp4')
        self.assertIsNone(rows[0]['poster'])
        self.assertEqual(rows[1]['duration_seconds'], 95)

    def test_requires_a_link_or_a_file(self):
        with self.assertRaises(ValidationError):
            LandingVideo(title='فارغ').full_clean()
