#!/usr/bin/env python3
"""Views for Parents app"""
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404

from .models.parent import Child, Parent
from .serializers import (
    ChildCreateSerializer,
    ChildDetailSerializer,
    ChildUpdateSerializer
)
from .permissions import IsParent, IsChildPrimaryParent


class ChildCreateView(generics.CreateAPIView):
    """
    API endpoint for parents to create a child.
    Only authenticated parents can access this endpoint.
    The primary_parent is automatically set to the authenticated parent.
    """
    queryset = Child.objects.all()
    serializer_class = ChildCreateSerializer
    permission_classes = [permissions.IsAuthenticated, IsParent]
    
    def perform_create(self, serializer):
        """Save the child with the authenticated parent as primary_parent."""
        serializer.save()
    
    def create(self, request, *args, **kwargs):
        """Override create to return detailed child info after creation."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        # Return detailed information using ChildDetailSerializer
        child = serializer.instance
        detail_serializer = ChildDetailSerializer(child)
        
        headers = self.get_success_headers(serializer.data)
        return Response(
            detail_serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )


class ChildListView(generics.ListAPIView):
    """
    API endpoint to list all children of the authenticated parent.
    Returns both primary children (where parent is primary_parent) and 
    extra children (where parent is linked as secondary parent via ChildParents).
    """
    serializer_class = ChildDetailSerializer
    permission_classes = [permissions.IsAuthenticated, IsParent]
    
    def get_queryset(self):
        """Return children where the user is either the primary parent or a secondary parent."""
        from django.db.models import Q
        
        parent = self.request.user.parent_profile
        
        # Return children where parent is either:
        # 1. The primary parent (primary_parent=parent)
        # 2. A secondary parent (linked via ChildParents - extra_parents relationship)
        return Child.objects.filter(
            Q(primary_parent=parent) | Q(extra_parents__parent=parent)
        ).distinct()  # Use distinct() to avoid duplicates if parent is linked multiple ways


class ChildDetailView(generics.RetrieveAPIView):
    """
    API endpoint to retrieve details of a specific child.
    Only the primary parent can view their child's details.
    """
    queryset = Child.objects.all()
    serializer_class = ChildDetailSerializer
    permission_classes = [permissions.IsAuthenticated, IsParent, IsChildPrimaryParent]
    lookup_field = 'id'


class ChildUpdateView(generics.UpdateAPIView):
    """
    API endpoint to update a child's information.
    Only the primary parent can update their child.
    """
    queryset = Child.objects.all()
    serializer_class = ChildUpdateSerializer
    permission_classes = [permissions.IsAuthenticated, IsParent, IsChildPrimaryParent]
    lookup_field = 'id'
    
    def update(self, request, *args, **kwargs):
        """Override update to return detailed child info after update."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        # Return detailed information
        detail_serializer = ChildDetailSerializer(instance)
        return Response(detail_serializer.data)
