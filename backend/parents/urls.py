#!/usr/bin/env python3
"""URL configuration for Parents app"""
from django.urls import path
from .views import (
    ChildCreateView,
    ChildListView,
    ChildDetailView,
    ChildUpdateView,
)

app_name = 'parents'

urlpatterns = [
    # Child management endpoints
    path('children/', ChildListView.as_view(), name='child-list'),
    path('children/create/', ChildCreateView.as_view(), name='child-create'),
    path('children/<uuid:id>/', ChildDetailView.as_view(), name='child-detail'),
    path('children/<uuid:id>/update/', ChildUpdateView.as_view(), name='child-update'),
    # No delete endpoint: parents may not delete a child (enrollments,
    # attendance and payments hang off it). Admins delete from Django admin.
]
