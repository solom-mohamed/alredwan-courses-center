#!/usr/bin/env python3
from rest_framework import permissions
from django.utils import timezone
from datetime import timedelta

class IsSupervisor(permissions.BasePermission):
    """
    Allows access only to supervisors (or admins).
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        # Adjust this depending on how you identify supervisors/admins in your CustomUser
        return request.user.role in ['supervisor', 'admin']

class IsInstructor(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.role == 'instructor'

class IsUploaderWithin24hOrAdmin(permissions.BasePermission):
    """
    Allows an instructor to edit/delete their own memory if uploaded within the last 24h.
    Admins can do it anytime.
    """
    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
            
        if request.user.role == 'admin':
            return True
            
        if request.user.role in ['instructor', 'supervisor']:
            # Check if this user uploaded it
            if obj.uploaded_by.user == request.user:
                # Check if within 24 hours
                if timezone.now() - obj.created_at <= timedelta(hours=24):
                    return True
                    
        return False
