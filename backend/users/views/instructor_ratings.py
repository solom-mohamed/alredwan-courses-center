#!/usr/bin/env python3
"""Views for Instructor Ratings"""
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.pagination import PageNumberPagination
from django.db.models import Avg, Count
from django.shortcuts import get_object_or_404

from users.models import Instructor
from users.models.student_instructor_rating import StudentInstructorRating, ParentInstructorRating
from users.serializers import InstructorRatingSerializer, InstructorRatingDetailSerializer


class StudentRatingsPagination(PageNumberPagination):
    page_size = 20
    page_query_param = 'student_page'


class ParentRatingsPagination(PageNumberPagination):
    page_size = 20
    page_query_param = 'parent_page'


class InstructorRatingsView(generics.RetrieveAPIView):
    """
    API endpoint for retrieving ratings of a specific instructor.
    GET /api/instructors/{id}/ratings/

    Returns aggregated rating statistics and individual ratings in paginated envelopes.
    Public, like course ratings: the instructor profile page shows them to visitors.
    """
    permission_classes = [AllowAny]
    serializer_class = InstructorRatingDetailSerializer

    def get_object(self):
        """Get instructor by ID"""
        instructor_id = self.kwargs.get('pk')
        return get_object_or_404(Instructor, pk=instructor_id)

    def retrieve(self, request, *args, **kwargs):
        """Retrieve instructor ratings and statistics"""
        instructor = self.get_object()

        # Get aggregated statistics using database aggregation
        student_stats = StudentInstructorRating.objects.filter(instructor=instructor).aggregate(
            avg_rating=Avg('rating'),
            total_ratings=Count('id')
        )
        parent_stats = ParentInstructorRating.objects.filter(instructor=instructor).aggregate(
            avg_rating=Avg('rating'),
            total_ratings=Count('id')
        )

        # Calculate combined average
        student_total = (student_stats['avg_rating'] or 0) * \
            (student_stats['total_ratings'] or 0)
        parent_total = (parent_stats['avg_rating'] or 0) * \
            (parent_stats['total_ratings'] or 0)
        total_count = (student_stats['total_ratings']
                       or 0) + (parent_stats['total_ratings'] or 0)

        combined_avg = None
        if total_count > 0:
            combined_avg = round(
                (student_total + parent_total) / total_count, 2)

        # Get individual ratings with pagination support
        student_ratings = StudentInstructorRating.objects.filter(
            instructor=instructor
        ).select_related('student__user', 'course', 'online_course').order_by('-created_at')

        parent_ratings = ParentInstructorRating.objects.filter(
            instructor=instructor
        ).select_related('parent__user', 'course', 'online_course').order_by('-created_at')

        student_paginator = StudentRatingsPagination()
        parent_paginator = ParentRatingsPagination()

        student_page = student_paginator.paginate_queryset(student_ratings, request)
        if student_page is not None:
            student_ratings_data = InstructorRatingSerializer(
                student_page, many=True, context={'type': 'student'}).data
            student_paginated = student_paginator.get_paginated_response(student_ratings_data).data
        else:
            student_ratings_data = InstructorRatingSerializer(
                student_ratings, many=True, context={'type': 'student'}).data
            student_paginated = {
                'count': len(student_ratings_data),
                'next': None,
                'previous': None,
                'results': student_ratings_data
            }

        parent_page = parent_paginator.paginate_queryset(parent_ratings, request)
        if parent_page is not None:
            parent_ratings_data = InstructorRatingSerializer(
                parent_page, many=True, context={'type': 'parent'}).data
            parent_paginated = parent_paginator.get_paginated_response(parent_ratings_data).data
        else:
            parent_ratings_data = InstructorRatingSerializer(
                parent_ratings, many=True, context={'type': 'parent'}).data
            parent_paginated = {
                'count': len(parent_ratings_data),
                'next': None,
                'previous': None,
                'results': parent_ratings_data
            }

        response_data = {
            'instructor_id': instructor.id,
            'instructor_name': instructor.user.get_full_name(),
            'statistics': {
                'average_rating': combined_avg,
                'total_ratings': total_count,
                'student_ratings_count': student_stats['total_ratings'] or 0,
                'student_average': round(student_stats['avg_rating'], 2) if student_stats['avg_rating'] else None,
                'parent_ratings_count': parent_stats['total_ratings'] or 0,
                'parent_average': round(parent_stats['avg_rating'], 2) if parent_stats['avg_rating'] else None,
            },
            'ratings': {
                'student_ratings': student_paginated,
                'parent_ratings': parent_paginated,
            }
        }

        return Response(response_data)


class InstructorRateView(generics.CreateAPIView):
    """
    API endpoint for submitting a rating for a specific instructor.
    POST /api/instructors/{id}/rate/
    """
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.user.role == 'parent':
            from users.serializers import ParentInstructorRateSerializer
            return ParentInstructorRateSerializer
        from users.serializers import StudentInstructorRateSerializer
        return StudentInstructorRateSerializer

    def create(self, request, *args, **kwargs):
        instructor_id = self.kwargs.get('pk')
        instructor = get_object_or_404(Instructor, pk=instructor_id)

        serializer = self.get_serializer(
            data=request.data, 
            context={'request': request, 'instructor': instructor}
        )
        serializer.is_valid(raise_exception=True)
        
        if request.user.role == 'parent':
            rating, created = ParentInstructorRating.objects.update_or_create(
                parent=request.user.parent_profile,
                instructor=instructor,
                defaults={
                    'course': serializer.validated_data.get('course'),
                    'online_course': serializer.validated_data.get('online_course'),
                    'rating': serializer.validated_data['rating'], 
                    'feedback': serializer.validated_data.get('feedback', '')
                }
            )
        else:
            rating, created = StudentInstructorRating.objects.update_or_create(
                student=request.user.student_profile,
                instructor=instructor,
                defaults={
                    'course': serializer.validated_data.get('course'),
                    'online_course': serializer.validated_data.get('online_course'),
                    'rating': serializer.validated_data['rating'], 
                    'feedback': serializer.validated_data.get('feedback', '')
                }
            )

        return Response(
            {"detail": "تم حفظ التقييم بنجاح.", "created": created},
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
        )
