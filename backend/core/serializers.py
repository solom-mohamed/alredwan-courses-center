from rest_framework import serializers

from .models import LandingVideo


class LandingVideoSerializer(serializers.ModelSerializer):
    """Public shape of a landing page clip: one playable URL plus display data."""
    source = serializers.CharField(read_only=True)
    video_url = serializers.CharField(source='playback_url', read_only=True)
    poster = serializers.CharField(source='poster_url', read_only=True)

    class Meta:
        model = LandingVideo
        fields = ['id', 'title', 'description', 'source', 'video_url', 'poster',
                  'duration_seconds', 'order']
        read_only_fields = fields
