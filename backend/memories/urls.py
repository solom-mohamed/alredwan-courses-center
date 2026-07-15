#!/usr/bin/env python3
from django.urls import path
from .views import (
    GeneralFeedView,
    PrivateFeedView,
    MemoryUploadView,
    MemoryDetailView,
    ParticipantSearchView,
    CloudinarySignatureView
)

app_name = 'memories'

urlpatterns = [
    path('feed/general/', GeneralFeedView.as_view(), name='general-feed'),
    path('feed/private/', PrivateFeedView.as_view(), name='private-feed'),
    path('upload/', MemoryUploadView.as_view(), name='memory-upload'),
    path('<uuid:id>/', MemoryDetailView.as_view(), name='memory-detail'),
    path('participants/search/', ParticipantSearchView.as_view(), name='participant-search'),
    path('cloudinary/signature/', CloudinarySignatureView.as_view(), name='cloudinary-signature'),
]
