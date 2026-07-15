#!/usr/bin/env python3
from rest_framework import generics, permissions, status, views
from rest_framework.response import Response
from django.db.models import Q
from .models import Memory
from .serializers import MemorySerializer, MemoryUploadSerializer
from .permissions import IsSupervisor, IsUploaderWithin24hOrAdmin
from parents.models import Child
from users.models import StudentUser

class GeneralFeedView(generics.ListAPIView):
    """
    API endpoint for the general memories feed.
    Visible to any authenticated user. Random order on every load.
    """
    serializer_class = MemorySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # Order randomly for general feed
        return Memory.objects.filter(is_active=True).order_by('?')


class PrivateFeedView(generics.ListAPIView):
    """
    API endpoint for the private memories feed.
    - Parents see memories of their children. Can filter by ?child_id=
    - Students see memories they are tagged in.
    """
    serializer_class = MemorySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        queryset = Memory.objects.filter(is_active=True)
        
        if user.role == 'parent':
            if hasattr(user, 'parent_profile'):
                parent_profile = user.parent_profile
                # Parents can see memories tagged with their primary children or extra children
                child_id_param = self.request.query_params.get('child_id')
                
                if child_id_param:
                    # Filter for specific child, but ensure the parent actually has access to this child
                    return queryset.filter(
                        children__id=child_id_param,
                        children__in=Child.objects.filter(
                            Q(primary_parent=parent_profile) | Q(extra_parents__parent=parent_profile)
                        )
                    ).distinct().order_by('-created_at')
                else:
                    # All children of this parent
                    return queryset.filter(
                        children__in=Child.objects.filter(
                            Q(primary_parent=parent_profile) | Q(extra_parents__parent=parent_profile)
                        )
                    ).distinct().order_by('-created_at')
                    
        elif user.role == 'student':
            if hasattr(user, 'student_profile'):
                return queryset.filter(students=user.student_profile).distinct().order_by('-created_at')
                
        # Empty queryset for other roles if they somehow hit this
        return Memory.objects.none()


class MemoryUploadView(generics.CreateAPIView):
    """
    API endpoint to upload a memory.
    Supervisors only.
    """
    serializer_class = MemoryUploadSerializer
    permission_classes = [permissions.IsAuthenticated, IsSupervisor]
    
    def perform_create(self, serializer):
        from users.models import Instructor
        instructor, created = Instructor.objects.get_or_create(
            user=self.request.user,
            defaults={
                'monthly_salary': 0, 
                'type': Instructor.InstructorType.SUPERVISOR
            }
        )
        serializer.save(uploaded_by=instructor)
        
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        # Return detailed info
        detail_serializer = MemorySerializer(serializer.instance)
        headers = self.get_success_headers(serializer.data)
        return Response(detail_serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class MemoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    API endpoint to update or soft-delete a memory.
    Uploading supervisor within 24h, or admin anytime.
    """
    queryset = Memory.objects.all()
    serializer_class = MemoryUploadSerializer
    permission_classes = [permissions.IsAuthenticated, IsUploaderWithin24hOrAdmin]
    lookup_field = 'id'
    
    def perform_destroy(self, instance):
        # Soft delete
        instance.is_active = False
        instance.save()
        
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({"message": "تم حذف الذكرى بنجاح"}, status=status.HTTP_200_OK)


class ParticipantSearchView(views.APIView):
    """
    API endpoint to search for children/students by name or code.
    Supervisors only (used for tagging).
    """
    permission_classes = [permissions.IsAuthenticated, IsSupervisor]
    
    def get(self, request):
        query = request.query_params.get('q', '').strip()
        if not query or len(query) < 2:
            return Response([])
            
        results = []
        
        # Search Children
        children = Child.objects.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(unique_code__icontains=query)
        )[:10]
        
        for child in children:
            results.append({
                'id': child.id,
                'name': f"{child.first_name} {child.last_name}",
                'code': child.unique_code,
                'type': 'child'
            })
            
        # Search Students
        students = StudentUser.objects.filter(
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query) |
            Q(unique_code__icontains=query)
        )[:10]
        
        for student in students:
            results.append({
                'id': student.id,
                'name': student.user.get_full_name(),
                'code': student.unique_code,
                'type': 'student'
            })
            
        return Response(results)

import cloudinary.utils
import time

class CloudinarySignatureView(views.APIView):
    """
    API endpoint to get a secure signature for direct client-side upload to Cloudinary.
    Supervisors only.
    """
    permission_classes = [permissions.IsAuthenticated, IsSupervisor]
    
    def get(self, request):
        timestamp = int(time.time())
        params_to_sign = {
            'timestamp': timestamp,
            'folder': 'memories'
        }
        signature = cloudinary.utils.api_sign_request(params_to_sign, cloudinary.config().api_secret)
        
        return Response({
            'signature': signature,
            'timestamp': timestamp,
            'cloud_name': cloudinary.config().cloud_name,
            'api_key': cloudinary.config().api_key,
        })

