#!/usr/bin/env python3
"""Filters for attendance app."""

import django_filters
from django_filters import FilterSet

from attendance.models import InstructorAttendance, AttendanceStatus, AttendanceType, SupervisorSchedule
from attendance.models.lecture_attendance import LectureAttendance
from courses.models import Weekday


class InstructorAttendanceFilter(FilterSet):
    """
    FilterSet for filtering instructor attendance records.

    Available filters:
    - date_from: Filter records from this date (inclusive)
    - date_to: Filter records up to this date (inclusive)
    - instructor: Filter by instructor's user ID (UUID)
    - instructor_id: Filter by Instructor ID
    - gender: Filter by instructor's gender (male/female)
    - status: Filter by attendance status (present, absent, late, pending, not_started)
    - attendance_type: Filter by type (lecture, supervision)
    - rated_by: Filter by the admin who rated
    - has_rating: Filter records that have been rated (True/False)
    - season: Filter by season ID
    - checked_in: Filter records that have checked in (True/False)
    - checked_out: Filter records that have checked out (True/False)
    - instructor_type: Filter by instructor type (normal/supervisor)
    """
    date_from = django_filters.DateFilter(
        field_name='date',
        lookup_expr='gte',
        help_text='Filter records from this date (inclusive). Format: YYYY-MM-DD'
    )
    date_to = django_filters.DateFilter(
        field_name='date',
        lookup_expr='lte',
        help_text='Filter records up to this date (inclusive). Format: YYYY-MM-DD'
    )
    instructor = django_filters.UUIDFilter(
        field_name='instructor__user__id',
        help_text='Filter by instructor user ID (UUID)'
    )
    instructor_id = django_filters.NumberFilter(
        field_name='instructor_id',
        help_text='Filter by instructor (Instructor) ID, as in /dashboard/instructors/<id>'
    )
    gender = django_filters.ChoiceFilter(
        field_name='instructor__user__gender',
        choices=[('male', 'Male'), ('female', 'Female')],
        help_text='Filter by instructor gender (male/female)'
    )
    instructor_type = django_filters.ChoiceFilter(
        field_name='instructor__type',
        choices=[('normal', 'Normal'), ('supervisor', 'Supervisor')],
        help_text='Filter by instructor type (normal/supervisor)'
    )
    status = django_filters.ChoiceFilter(
        choices=AttendanceStatus.choices,
        help_text='Filter by attendance status (present, absent, late, pending, not_started)'
    )
    attendance_type = django_filters.ChoiceFilter(
        choices=AttendanceType.choices,
        help_text='Filter by attendance type (lecture, supervision)'
    )
    rated_by = django_filters.UUIDFilter(
        field_name='rated_by__id',
        help_text='Filter by the admin user ID who rated the attendance'
    )
    has_rating = django_filters.BooleanFilter(
        method='filter_has_rating',
        help_text='Filter records that have been rated (true) or not rated (false)'
    )
    season = django_filters.NumberFilter(
        field_name='season__id',
        help_text='Filter by season ID'
    )
    checked_in = django_filters.BooleanFilter(
        method='filter_checked_in',
        help_text='Filter records that have checked in (true) or not (false)'
    )
    checked_out = django_filters.BooleanFilter(
        method='filter_checked_out',
        help_text='Filter records that have checked out (true) or not (false)'
    )

    class Meta:
        model = InstructorAttendance
        fields = [
            'date_from', 'date_to', 'instructor', 'instructor_id', 'gender', 'instructor_type',
            'status', 'attendance_type', 'rated_by', 'has_rating', 'season',
            'checked_in', 'checked_out'
        ]

    def filter_has_rating(self, queryset, name, value):
        """Filter by whether the attendance has been rated."""
        if value is True:
            # Has been rated (rating > 0)
            return queryset.filter(rating__gt=0)
        elif value is False:
            # Not rated yet (rating is null or 0)
            return queryset.filter(rating__isnull=True) | queryset.filter(rating=0)
        return queryset

    def filter_checked_in(self, queryset, name, value):
        """Filter by whether the instructor has checked in."""
        if value is True:
            return queryset.filter(check_in_time__isnull=False)
        elif value is False:
            return queryset.filter(check_in_time__isnull=True)
        return queryset

    def filter_checked_out(self, queryset, name, value):
        """Filter by whether the instructor has checked out."""
        if value is True:
            return queryset.filter(check_out_time__isnull=False)
        elif value is False:
            return queryset.filter(check_out_time__isnull=True)
        return queryset


class SupervisorScheduleFilter(FilterSet):
    """
    FilterSet for filtering supervisor schedules.

    Available filters:
    - instructor: Filter by instructor profile ID (integer PK)
    - day_of_week: Filter by day of week (0=Saturday, 1=Sunday, ..., 6=Friday)
    - start_time_from: Filter schedules starting at or after this time
    - start_time_to: Filter schedules starting at or before this time
    """
    instructor = django_filters.NumberFilter(
        field_name='instructor__id',
        help_text='Filter by instructor profile ID (integer)'
    )
    day_of_week = django_filters.ChoiceFilter(
        choices=Weekday.choices,
        help_text='Filter by day of week (0=Saturday, 1=Sunday, ..., 6=Friday)'
    )
    start_time_from = django_filters.TimeFilter(
        field_name='start_time',
        lookup_expr='gte',
        help_text='Filter schedules starting at or after this time. Format: HH:MM'
    )
    start_time_to = django_filters.TimeFilter(
        field_name='start_time',
        lookup_expr='lte',
        help_text='Filter schedules starting at or before this time. Format: HH:MM'
    )

    class Meta:
        model = SupervisorSchedule
        fields = ['instructor', 'day_of_week',
                  'start_time_from', 'start_time_to']


class LectureAttendanceFilter(FilterSet):
    """
    FilterSet for filtering lecture attendance records (students/children).

    Available filters:
    - lecture: Filter by lecture ID
    - course: Filter by course ID
    - gender: Filter by participant gender (male/female for students, boy/girl for children)
    - participant_type: Filter by participant type (student/child)
    - present: Filter by attendance status (true=present, false=absent, null=not marked)
    - has_rating: Filter records that have been rated (True/False)
    - rating_min: Filter by minimum rating
    - rating_max: Filter by maximum rating
    - marked_by: Filter by the user who marked the attendance
    - marked_via: Filter by marking method (manual/qr_scan)
    - date_from: Filter by lecture date from (inclusive)
    - date_to: Filter by lecture date to (inclusive)
    """
    lecture = django_filters.NumberFilter(
        field_name='lecture__id',
        help_text='Filter by lecture ID'
    )
    course = django_filters.NumberFilter(
        field_name='lecture__course__id',
        help_text='Filter by course ID'
    )
    gender = django_filters.CharFilter(
        method='filter_gender',
        help_text='Filter by participant gender (male/female for students, boy/girl for children)'
    )
    participant_type = django_filters.ChoiceFilter(
        method='filter_participant_type',
        choices=[('student', 'Student'), ('child', 'Child')],
        help_text='Filter by participant type (student/child)'
    )
    present = django_filters.BooleanFilter(
        field_name='present',
        help_text='Filter by attendance status (true=present, false=absent)'
    )
    not_marked = django_filters.BooleanFilter(
        method='filter_not_marked',
        help_text='Filter records that have not been marked yet (true/false)'
    )
    has_rating = django_filters.BooleanFilter(
        method='filter_has_rating',
        help_text='Filter records that have been rated (true) or not rated (false)'
    )
    rating_min = django_filters.NumberFilter(
        field_name='rating',
        lookup_expr='gte',
        help_text='Filter by minimum rating'
    )
    rating_max = django_filters.NumberFilter(
        field_name='rating',
        lookup_expr='lte',
        help_text='Filter by maximum rating'
    )
    marked_by = django_filters.UUIDFilter(
        field_name='marked_by__id',
        help_text='Filter by the user ID who marked the attendance'
    )
    marked_via = django_filters.ChoiceFilter(
        choices=[('manual', 'Manual'), ('qr_scan', 'QR Scan')],
        help_text='Filter by marking method (manual/qr_scan)'
    )
    date_from = django_filters.DateFilter(
        field_name='lecture__day',
        lookup_expr='gte',
        help_text='Filter by lecture date from (inclusive). Format: YYYY-MM-DD'
    )
    date_to = django_filters.DateFilter(
        field_name='lecture__day',
        lookup_expr='lte',
        help_text='Filter by lecture date to (inclusive). Format: YYYY-MM-DD'
    )
    instructor = django_filters.NumberFilter(
        field_name='lecture__instructor__id',
        help_text='Filter by instructor ID'
    )
    season = django_filters.NumberFilter(
        field_name='lecture__course__season__id',
        help_text='Filter by season ID'
    )

    class Meta:
        model = LectureAttendance
        fields = [
            'lecture', 'course', 'gender', 'participant_type', 'present',
            'not_marked', 'has_rating', 'rating_min', 'rating_max',
            'marked_by', 'marked_via', 'date_from', 'date_to',
            'instructor', 'season'
        ]

    def filter_gender(self, queryset, name, value):
        """
        Filter by participant gender.
        For students: male/female (from user model)
        For children: boy/girl (from child model)
        """
        from django.db.models import Q

        if not value:
            return queryset

        value_lower = value.lower()

        # Map variations to database values
        if value_lower in ('male', 'boy', 'm', 'ذكر', 'ولد'):
            # Match male students OR boy children
            return queryset.filter(
                Q(student__user__gender='male') | Q(child__gender='boy')
            )
        elif value_lower in ('female', 'girl', 'f', 'أنثى', 'بنت'):
            # Match female students OR girl children
            return queryset.filter(
                Q(student__user__gender='female') | Q(child__gender='girl')
            )
        return queryset

    def filter_participant_type(self, queryset, name, value):
        """Filter by participant type (student or child)."""
        if value == 'student':
            return queryset.filter(student__isnull=False)
        elif value == 'child':
            return queryset.filter(child__isnull=False)
        return queryset

    def filter_not_marked(self, queryset, name, value):
        """Filter records that have not been marked yet."""
        if value is True:
            return queryset.filter(present__isnull=True)
        elif value is False:
            return queryset.filter(present__isnull=False)
        return queryset

    def filter_has_rating(self, queryset, name, value):
        """Filter by whether the attendance has been rated."""
        if value is True:
            return queryset.filter(rating__isnull=False)
        elif value is False:
            return queryset.filter(rating__isnull=True)
        return queryset
