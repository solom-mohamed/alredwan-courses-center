from django.urls import path

from .views import LandingVideoListView

urlpatterns = [
    path('videos/', LandingVideoListView.as_view(), name='landing-videos'),
]
