#!/usr/bin/env python3
"""Views for instructor attendance (fingerprint devices and admin dashboard)."""

from attendance.models import (
    InstructorAttendance,
    AttendanceDevice,
    SupervisorSchedule,
    AttendanceStatus,
    AttendanceType,
    CheckInMethod,
    FingerprintScanLog,
    ScanAction,
)
from courses.models import Season, CourseSchedule
from users.models import Instructor
from attendance.filters import InstructorAttendanceFilter, SupervisorScheduleFilter
from attendance.serializers import (
    InstructorAttendanceSerializer,
    InstructorAttendanceListSerializer,
    FingerprintCheckInSerializer,
    FingerprintCheckOutSerializer,
    FingerprintScanSerializer,
    RateInstructorSerializer,
    AttendanceDeviceSerializer,
    SupervisorScheduleSerializer,
    TodayAttendanceSummarySerializer,
    GenerateAttendanceSerializer,
    InstructorCourseScheduleSerializer,
)
from attendance.models.attendance_cron_log import AttendanceCronLog
from rest_framework import generics, status, views
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny, BasePermission
from rest_framework.decorators import api_view, permission_classes
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError


class IsAdminOrSupervisorRole(BasePermission):
    """
    Permission class that checks for admin or supervisor role.
    Allows access if:
    - user.role == 'admin' or 'supervisor'
    - user.is_staff or user.is_superuser
    - user has instructor_profile with type == 'supervisor'
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # Superuser/staff always allowed
        if request.user.is_superuser or request.user.is_staff:
            return True

        # Check role attribute
        if hasattr(request.user, 'role') and request.user.role in ['admin', 'supervisor']:
            return True

        # Check instructor profile type
        if hasattr(request.user, 'instructor_profile'):
            if request.user.instructor_profile.type == 'supervisor':
                return True

        return False


class IsAdminRoleOnly(BasePermission):
    """
    Permission class that checks for admin role only.
    Allows access if:
    - user.role == 'admin'
    - user.is_superuser
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # Superuser always allowed
        if request.user.is_superuser:
            return True

        # Check role attribute
        if hasattr(request.user, 'role') and request.user.role == 'admin':
            return True

        return False


class DeviceAuthenticationMixin:
    """
    Mixin for device authentication.
    Devices authenticate using their device_id.
    """
    permission_classes = [
        AllowAny]  # Devices don't use JWT, they use device_id

    def get_device(self, device_id):
        """Get the device by device_id or raise 404."""
        return get_object_or_404(
            AttendanceDevice,
            device_id=device_id,
            is_active=True
        )


class FingerprintCheckInView(DeviceAuthenticationMixin, views.APIView):
    """
    API endpoint for fingerprint device check-in.

    POST /api/attendance/check-in/
    {
        "fingerprint_id": "FP123456",
        "device_id": "DEVICE001",
        "method": "fingerprint"
    }

    This endpoint:
    1. Validates the fingerprint_id maps to an instructor
    2. Validates the device is active
    3. Finds all attendance records for today for this instructor
    4. Marks them as checked in with appropriate status (PRESENT/LATE)
    """

    def post(self, request):
        serializer = FingerprintCheckInSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        fingerprint_id = serializer.validated_data['fingerprint_id']
        device_id = serializer.validated_data['device_id']
        method = serializer.validated_data.get(
            'method', CheckInMethod.FINGERPRINT)

        # Get instructor and device
        instructor = get_object_or_404(
            Instructor, fingerprint_id=fingerprint_id)
        device = self.get_device(device_id)

        today = timezone.localdate()

        # Check if already checked in first
        already_checked_in = InstructorAttendance.objects.filter(
            instructor=instructor,
            date=today,
            check_in_time__isnull=False
        ).first()

        if already_checked_in:
            return Response(
                {
                    "message": "Already checked in",
                    "instructor": instructor.user.get_full_name(),
                    "check_in_time": already_checked_in.check_in_time,
                },
                status=status.HTTP_200_OK
            )

        # Find all attendance records for this instructor today that need check-in
        attendance_records = InstructorAttendance.objects.filter(
            instructor=instructor,
            date=today,
            status__in=[AttendanceStatus.NOT_STARTED, AttendanceStatus.PENDING]
        )

        if not attendance_records.exists():
            return Response(
                {
                    "error": "No attendance records found for today",
                    "instructor": instructor.user.get_full_name(),
                    "date": str(today)
                },
                status=status.HTTP_404_NOT_FOUND
            )

        # Mark all records as checked in
        checked_in_records = []
        for record in attendance_records:
            record.mark_checked_in(device=device, method=method)
            checked_in_records.append({
                "id": record.id,
                "type": record.attendance_type,
                "status": record.status,
            })

        return Response(
            {
                "message": "Check-in successful",
                "instructor": instructor.user.get_full_name(),
                "check_in_time": timezone.now(),
                "records": checked_in_records,
            },
            status=status.HTTP_200_OK
        )


class FingerprintCheckOutView(DeviceAuthenticationMixin, views.APIView):
    """
    API endpoint for fingerprint device check-out.

    POST /api/attendance/check-out/
    {
        "fingerprint_id": "FP123456",
        "device_id": "DEVICE001",
        "method": "fingerprint"
    }
    """

    def post(self, request):
        serializer = FingerprintCheckOutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        fingerprint_id = serializer.validated_data['fingerprint_id']
        device_id = serializer.validated_data['device_id']
        method = serializer.validated_data.get(
            'method', CheckInMethod.FINGERPRINT)

        # Get instructor and device
        instructor = get_object_or_404(
            Instructor, fingerprint_id=fingerprint_id)
        device = self.get_device(device_id)

        today = timezone.localdate()

        # Find attendance records that are checked in but not checked out
        attendance_records = InstructorAttendance.objects.filter(
            instructor=instructor,
            date=today,
            check_in_time__isnull=False,
            check_out_time__isnull=True
        )

        if not attendance_records.exists():
            # Check if already checked out
            already_out = InstructorAttendance.objects.filter(
                instructor=instructor,
                date=today,
                check_out_time__isnull=False
            ).first()

            if already_out:
                return Response(
                    {
                        "message": "Already checked out",
                        "instructor": instructor.user.get_full_name(),
                        "check_out_time": already_out.check_out_time,
                    },
                    status=status.HTTP_200_OK
                )

            return Response(
                {
                    "error": "Must check in before checking out",
                    "instructor": instructor.user.get_full_name(),
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Mark all records as checked out
        checked_out_records = []
        for record in attendance_records:
            try:
                record.mark_checked_out(device=device, method=method)
                checked_out_records.append({
                    "id": record.id,
                    "type": record.attendance_type,
                    "check_out_time": record.check_out_time,
                })
            except ValidationError as e:
                return Response(
                    {"error": str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )

        return Response(
            {
                "message": "Check-out successful",
                "instructor": instructor.user.get_full_name(),
                "check_out_time": timezone.now(),
                "records": checked_out_records,
            },
            status=status.HTTP_200_OK
        )


class UnifiedFingerprintScanView(DeviceAuthenticationMixin, views.APIView):
    """
    Unified endpoint for fingerprint device scans.

    POST /api/attendance/scan/
    {
        "fingerprint_id": "FP123456",
        "device_id": "DEVICE001",
        "timestamp": "2026-02-14T08:30:00+02:00"  // Optional, for offline sync
    }

    This is the RECOMMENDED endpoint for fingerprint devices that don't distinguish
    between check-in and check-out actions.

    Logic:
    1. No attendance record for today → Auto-create based on schedule/lecture and check-in
    2. Has record but not checked-in → Check-in
    3. Checked-in but not out → Check-out
    4. Already checked out → Re-entry (clears check-out, logs as re-entry)
    5. Rapid scans (< 2 min) → Ignored as duplicates

    All scans are logged to FingerprintScanLog for audit trail.
    """

    # Minimum time between scans (in seconds) to prevent rapid duplicates
    MIN_SCAN_INTERVAL_SECONDS = 120  # 2 minutes

    def post(self, request):
        serializer = FingerprintScanSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        fingerprint_id = serializer.validated_data['fingerprint_id']
        device_id = serializer.validated_data['device_id']
        scan_time = serializer.validated_data.get('timestamp', timezone.now())

        # Get instructor and device from serializer context
        instructor = serializer.context.get('instructor')
        if not instructor:
            instructor = get_object_or_404(
                Instructor, fingerprint_id=fingerprint_id)

        device = serializer.context.get('device')
        if not device:
            device = self.get_device(device_id)

        today = timezone.localdate()

        # Check for rapid duplicate scans
        recent_scans = FingerprintScanLog.objects.filter(
            instructor=instructor,
            scan_time__gte=timezone.now() - timezone.timedelta(seconds=self.MIN_SCAN_INTERVAL_SECONDS)
        ).exclude(action=ScanAction.IGNORED)

        if recent_scans.exists():
            last_scan = recent_scans.first()
            # Log as ignored
            FingerprintScanLog.objects.create(
                instructor=instructor,
                attendance=last_scan.attendance,
                scan_time=scan_time,
                device=device,
                action=ScanAction.IGNORED,
                is_processed=False,
                notes=f"تم تجاهل البصمة - تكرار خلال {self.MIN_SCAN_INTERVAL_SECONDS} ثانية"
            )
            return Response(
                {
                    "message": "Scan ignored - too soon after last scan",
                    "instructor": instructor.user.get_full_name(),
                    "last_scan": last_scan.scan_time,
                    "min_interval_seconds": self.MIN_SCAN_INTERVAL_SECONDS,
                },
                status=status.HTTP_200_OK
            )

        # Get or create attendance records for today
        attendance_records = InstructorAttendance.objects.filter(
            instructor=instructor,
            date=today
        )

        action_taken = None
        response_data = {
            "instructor": instructor.user.get_full_name(),
            "scan_time": scan_time,
            "records": [],
        }

        # CASE 1: No attendance records exist - auto-create based on schedules/lectures
        if not attendance_records.exists():
            created_records = self._auto_create_attendance(
                instructor, today, device)
            if created_records:
                action_taken = ScanAction.AUTO_CREATED
                for record in created_records:
                    record.mark_checked_in(
                        device=device, method=CheckInMethod.FINGERPRINT)
                    response_data["records"].append({
                        "id": record.id,
                        "type": record.attendance_type,
                        "status": record.status,
                        "auto_created": True,
                    })
                response_data["message"] = "Auto-created attendance and checked in"
                response_data["action"] = "auto_create_check_in"

                # Log the scan
                for record in created_records:
                    FingerprintScanLog.objects.create(
                        instructor=instructor,
                        attendance=record,
                        scan_time=scan_time,
                        device=device,
                        action=ScanAction.AUTO_CREATED,
                        is_processed=True,
                        notes="تم إنشاء سجل الحضور تلقائياً وتسجيل الدخول"
                    )

                return Response(response_data, status=status.HTTP_201_CREATED)
            else:
                # No schedules or lectures found - create a general attendance record
                season = Season.objects.filter(is_active=True).first()
                if not season:
                    return Response(
                        {
                            "error": "No active season found",
                            "instructor": instructor.user.get_full_name(),
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )

                record = InstructorAttendance.objects.create(
                    instructor=instructor,
                    date=today,
                    attendance_type=AttendanceType.SUPERVISION,
                    status=AttendanceStatus.NOT_STARTED,
                    season=season
                )
                record.mark_checked_in(
                    device=device, method=CheckInMethod.FINGERPRINT)

                FingerprintScanLog.objects.create(
                    instructor=instructor,
                    attendance=record,
                    scan_time=scan_time,
                    device=device,
                    action=ScanAction.AUTO_CREATED,
                    is_processed=True,
                    notes="تم إنشاء سجل حضور عام (بدون جدول)"
                )

                response_data["message"] = "Auto-created general attendance and checked in"
                response_data["action"] = "auto_create_check_in"
                response_data["records"] = [{
                    "id": record.id,
                    "type": record.attendance_type,
                    "status": record.status,
                    "auto_created": True,
                }]
                return Response(response_data, status=status.HTTP_201_CREATED)

        # Check current state of attendance records
        not_checked_in = attendance_records.filter(check_in_time__isnull=True)
        checked_in_not_out = attendance_records.filter(
            check_in_time__isnull=False,
            check_out_time__isnull=True
        )
        checked_out = attendance_records.filter(check_out_time__isnull=False)

        # CASE 2: Has records not checked in → Check-in
        if not_checked_in.exists():
            for record in not_checked_in:
                record.mark_checked_in(
                    device=device, method=CheckInMethod.FINGERPRINT)
                response_data["records"].append({
                    "id": record.id,
                    "type": record.attendance_type,
                    "status": record.status,
                })
                FingerprintScanLog.objects.create(
                    instructor=instructor,
                    attendance=record,
                    scan_time=scan_time,
                    device=device,
                    action=ScanAction.CHECK_IN,
                    is_processed=True
                )
            response_data["message"] = "Check-in successful"
            response_data["action"] = "check_in"
            response_data["check_in_time"] = scan_time
            return Response(response_data, status=status.HTTP_200_OK)

        # CASE 3: Checked in but not out → Check-out
        if checked_in_not_out.exists():
            for record in checked_in_not_out:
                try:
                    record.mark_checked_out(
                        device=device, method=CheckInMethod.FINGERPRINT)
                    response_data["records"].append({
                        "id": record.id,
                        "type": record.attendance_type,
                        "check_out_time": record.check_out_time,
                    })
                    FingerprintScanLog.objects.create(
                        instructor=instructor,
                        attendance=record,
                        scan_time=scan_time,
                        device=device,
                        action=ScanAction.CHECK_OUT,
                        is_processed=True
                    )
                except ValidationError as e:
                    return Response(
                        {"error": str(e)},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            response_data["message"] = "Check-out successful"
            response_data["action"] = "check_out"
            response_data["check_out_time"] = scan_time
            return Response(response_data, status=status.HTTP_200_OK)

        # CASE 4: Already checked out → Re-entry (clear check-out)
        if checked_out.exists():
            for record in checked_out:
                record.check_out_time = None
                record.check_out_device = None
                record.check_out_method = None
                record.save()
                record.broadcast_update()
                response_data["records"].append({
                    "id": record.id,
                    "type": record.attendance_type,
                    "status": record.status,
                    "re_entry": True,
                })
                FingerprintScanLog.objects.create(
                    instructor=instructor,
                    attendance=record,
                    scan_time=scan_time,
                    device=device,
                    action=ScanAction.RE_ENTRY,
                    is_processed=True,
                    notes="إعادة دخول - تم مسح وقت الخروج السابق"
                )
            response_data["message"] = "Re-entry recorded - check-out cleared"
            response_data["action"] = "re_entry"
            return Response(response_data, status=status.HTTP_200_OK)

        # Fallback - should not reach here
        return Response(
            {"error": "Unexpected state"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    def _auto_create_attendance(self, instructor, date, device):
        """
        Auto-create attendance records based on instructor's schedules and lectures.

        Returns list of created InstructorAttendance records.
        """
        from courses.models import Lecture, Weekday

        season = Season.objects.filter(is_active=True).first()
        if not season:
            return []

        created_records = []
        # day_of_week uses the Weekday enum (Sat=0), not Python's Mon=0
        weekday = Weekday.of(date)

        # Check supervisor schedules for today
        schedules = SupervisorSchedule.objects.filter(
            instructor=instructor,
            day_of_week=weekday
        )

        for schedule in schedules:
            record, created = InstructorAttendance.objects.get_or_create(
                instructor=instructor,
                schedule=schedule,
                date=date,
                defaults={
                    "attendance_type": AttendanceType.SUPERVISION,
                    "status": AttendanceStatus.NOT_STARTED,
                    "season": season
                }
            )
            if created:
                created_records.append(record)

        # Check lectures for today
        lectures = Lecture.objects.filter(
            instructor=instructor,
            day=date
        )

        for lecture in lectures:
            record, created = InstructorAttendance.objects.get_or_create(
                instructor=instructor,
                lecture=lecture,
                defaults={
                    "date": date,
                    "attendance_type": AttendanceType.LECTURE,
                    "status": AttendanceStatus.NOT_STARTED,
                    "season": season
                }
            )
            if created:
                created_records.append(record)

        return created_records


class TodayAttendanceListView(generics.ListAPIView):
    """
    List all attendance records for today.
    Used by the admin dashboard for real-time monitoring.

    GET /api/attendance/today/
    """
    serializer_class = InstructorAttendanceListSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get_queryset(self):
        today = timezone.localdate()
        return InstructorAttendance.objects.filter(
            date=today
        ).select_related(
            'instructor__user',
            'lecture',
            'schedule'
        ).order_by('-check_in_time', 'instructor__user__first_name')


class TodayAttendanceSummaryView(views.APIView):
    """
    Get summary statistics for today's attendance.

    GET /api/attendance/today/summary/
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        today = timezone.localdate()

        qs = InstructorAttendance.objects.filter(date=today)

        summary = {
            'date': today,
            'total_expected': qs.count(),
            'checked_in': qs.filter(check_in_time__isnull=False).count(),
            'checked_out': qs.filter(check_out_time__isnull=False).count(),
            'present': qs.filter(status=AttendanceStatus.PRESENT).count(),
            'late': qs.filter(status=AttendanceStatus.LATE).count(),
            'absent': qs.filter(status=AttendanceStatus.ABSENT).count(),
            'pending': qs.filter(status=AttendanceStatus.PENDING).count(),
            'not_started': qs.filter(status=AttendanceStatus.NOT_STARTED).count(),
            'lecture_attendance_count': qs.filter(
                attendance_type=AttendanceType.LECTURE
            ).count(),
            'supervision_attendance_count': qs.filter(
                attendance_type=AttendanceType.SUPERVISION
            ).count(),
        }

        serializer = TodayAttendanceSummarySerializer(summary)
        return Response(serializer.data)


class AttendanceDetailView(generics.RetrieveUpdateAPIView):
    """
    Retrieve or update a specific attendance record.

    GET /api/attendance/<id>/
    PATCH /api/attendance/<id>/
    """
    serializer_class = InstructorAttendanceSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    queryset = InstructorAttendance.objects.select_related(
        'instructor__user',
        'lecture',
        'schedule',
        'rated_by'
    )


class RateAttendanceView(views.APIView):
    """
    Rate an instructor's attendance record.

    POST /api/attendance/<id>/rate/
    {
        "rating": 8.5,
        "notes": "Great performance today"
    }
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request, pk):
        attendance = get_object_or_404(InstructorAttendance, pk=pk)

        serializer = RateInstructorSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            attendance.add_rating(
                value=serializer.validated_data['rating'],
                admin_user=request.user,
                notes=serializer.validated_data.get('notes')
            )
        except ValidationError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            InstructorAttendanceSerializer(attendance).data,
            status=status.HTTP_200_OK
        )


class AttendanceByDateView(generics.ListAPIView):
    """
    List attendance records for a specific date.

    GET /api/attendance/date/<date>/
    """
    serializer_class = InstructorAttendanceListSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get_queryset(self):
        date_str = self.kwargs.get('date')
        try:
            from datetime import datetime
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return InstructorAttendance.objects.none()

        return InstructorAttendance.objects.filter(
            date=date
        ).select_related(
            'instructor__user'
        ).order_by('instructor__user__first_name')


class InstructorAttendanceHistoryView(generics.ListAPIView):
    """
    Get attendance history for a specific instructor.

    GET /api/attendance/instructor/<instructor_id>/
    """
    serializer_class = InstructorAttendanceListSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get_queryset(self):
        instructor_id = self.kwargs.get('instructor_id')
        return InstructorAttendance.objects.filter(
            instructor_id=instructor_id
        ).select_related(
            'instructor__user',
            'lecture',
            'lecture__course',
            'schedule'
        ).order_by('-date')


class AdminAllAttendanceListView(generics.ListAPIView):
    """
    List ALL attendance records (past and future) with comprehensive filters.

    This endpoint is admin-only and provides access to the complete attendance history
    with powerful filtering capabilities.

    GET /api/attendance/all/

    Roles: Admin, Supervisor (role == 'admin' or 'supervisor')

    Query Parameters:
    - date_from: Filter records from this date (inclusive). Format: YYYY-MM-DD
    - date_to: Filter records up to this date (inclusive). Format: YYYY-MM-DD
    - instructor: Filter by instructor user ID (UUID)
    - status: Filter by attendance status (present, absent, late, pending, not_started)
    - attendance_type: Filter by type (lecture, supervision)
    - rated_by: Filter by the admin user ID who rated the attendance
    - has_rating: Filter records that have been rated (true/false)
    - season: Filter by season ID
    - checked_in: Filter by check-in status (true/false)
    - checked_out: Filter by check-out status (true/false)

    Examples:
    - GET /api/attendance/all/?date_from=2025-01-01&date_to=2025-01-31
    - GET /api/attendance/all/?instructor=<uuid>&status=present
    - GET /api/attendance/all/?attendance_type=supervision&has_rating=false
    """
    serializer_class = InstructorAttendanceListSerializer
    permission_classes = [IsAuthenticated, IsAdminOrSupervisorRole]
    filter_backends = [DjangoFilterBackend]
    filterset_class = InstructorAttendanceFilter

    def get_queryset(self):
        return InstructorAttendance.objects.select_related(
            'instructor__user',
            'lecture',
            'schedule',
            'rated_by',
            'season'
        ).order_by('-date', '-check_in_time', 'instructor__user__first_name')


class AdminEditAttendanceView(generics.RetrieveUpdateAPIView):
    """
    Retrieve or update ANY attendance record (including past records).

    This endpoint allows admins to edit attendance records from any date,
    including past records. Useful for correcting historical data.

    GET /api/attendance/all/{id}/
    PUT /api/attendance/all/{id}/
    PATCH /api/attendance/all/{id}/

    Roles: Admin only (role == 'admin' or is_superuser)

    Editable Fields:
    - status: Change attendance status (present, absent, late, pending, not_started)
    - check_in_time: Manually set check-in time
    - check_out_time: Manually set check-out time
    - check_in_method: Set method (fingerprint, rfid, qr_code, manual)
    - check_out_method: Set method
    - rating: Set rating (1.00 - 10.00), requires instructor to be present/late
    - notes: Add/update notes
    - attendance_type: Change type (lecture, supervision)

    Note: Changing status to absent will clear the rating. Setting rating
    requires the attendance to be present or late.
    """
    serializer_class = InstructorAttendanceSerializer
    permission_classes = [IsAuthenticated, IsAdminRoleOnly]
    queryset = InstructorAttendance.objects.select_related(
        'instructor__user',
        'lecture',
        'schedule',
        'rated_by',
        'season'
    )

    def perform_update(self, serializer):
        """Track who made the edit if rating is updated."""
        instance = self.get_object()
        old_rating = instance.rating

        # Save the update
        updated_instance = serializer.save()

        # If rating was changed and is now > 0, track the rater
        new_rating = updated_instance.rating
        if new_rating and new_rating > 0 and new_rating != old_rating:
            updated_instance.rated_by = self.request.user
            updated_instance.rated_at = timezone.now()
            updated_instance.save()
            # Broadcast the rating update
            updated_instance.broadcast_rating()

        return updated_instance


class AttendanceDeviceListView(generics.ListCreateAPIView):
    """
    List or create attendance devices.

    GET /api/attendance/devices/
    POST /api/attendance/devices/
    """
    serializer_class = AttendanceDeviceSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    queryset = AttendanceDevice.objects.all()


class AttendanceDeviceDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete an attendance device.

    GET /api/attendance/devices/<id>/
    PATCH /api/attendance/devices/<id>/
    DELETE /api/attendance/devices/<id>/
    """
    serializer_class = AttendanceDeviceSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    queryset = AttendanceDevice.objects.all()


class SupervisorScheduleListView(generics.ListCreateAPIView):
    """
    List or create supervisor schedules.

    GET /api/attendance/schedules/
    POST /api/attendance/schedules/

    Roles:
    - Admin/Supervisor: See all schedules, can create new schedules
    - Instructor: See only their own schedules (read-only)

    Query Parameters (for admins):
    - instructor: Filter by instructor user ID (UUID)
    - day_of_week: Filter by day (0=Saturday, 1=Sunday, ..., 6=Friday)
    - start_time_from: Filter by minimum start time (HH:MM)
    - start_time_to: Filter by maximum start time (HH:MM)
    """
    serializer_class = SupervisorScheduleSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = SupervisorScheduleFilter

    def get_queryset(self):
        """
        Return schedules based on user role:
        - Admin/Supervisor/Staff: All schedules
        - Instructor: Only their own schedules
        """
        user = self.request.user
        base_qs = SupervisorSchedule.objects.select_related('instructor__user')

        # Admin, supervisor, or staff see all
        if user.is_staff or user.is_superuser:
            return base_qs.order_by('day_of_week', 'start_time')

        if hasattr(user, 'role') and user.role in ['admin', 'supervisor']:
            return base_qs.order_by('day_of_week', 'start_time')

        if hasattr(user, 'instructor_profile'):
            instructor_profile = user.instructor_profile
            # Supervisors see all
            if instructor_profile.type == 'supervisor':
                return base_qs.order_by('day_of_week', 'start_time')
            # Regular instructors see only their own
            return base_qs.filter(instructor=instructor_profile).order_by('day_of_week', 'start_time')

        # Non-instructors see nothing
        return SupervisorSchedule.objects.none()

    def create(self, request, *args, **kwargs):
        """Only admins can create schedules."""
        user = request.user
        is_admin = (
            user.is_staff or
            user.is_superuser or
            (hasattr(user, 'role') and user.role in ['admin', 'supervisor'])
        )

        if not is_admin:
            return Response(
                {"error": "Only admins can create schedules"},
                status=status.HTTP_403_FORBIDDEN
            )

        return super().create(request, *args, **kwargs)


class SupervisorScheduleDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete a supervisor schedule.

    GET /api/attendance/schedules/<id>/
    PATCH /api/attendance/schedules/<id>/
    DELETE /api/attendance/schedules/<id>/

    Roles:
    - Admin/Supervisor: Full access to any schedule
    - Instructor: Read-only access to their own schedules
    """
    serializer_class = SupervisorScheduleSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return schedules based on user role."""
        user = self.request.user
        base_qs = SupervisorSchedule.objects.select_related('instructor__user')

        # Admin, supervisor, or staff see all
        if user.is_staff or user.is_superuser:
            return base_qs

        if hasattr(user, 'role') and user.role in ['admin', 'supervisor']:
            return base_qs

        if hasattr(user, 'instructor_profile'):
            instructor_profile = user.instructor_profile
            # Supervisors see all
            if instructor_profile.type == 'supervisor':
                return base_qs
            # Regular instructors see only their own
            return base_qs.filter(instructor=instructor_profile)

        return SupervisorSchedule.objects.none()

    def update(self, request, *args, **kwargs):
        """Only admins can update schedules."""
        user = request.user
        is_admin = (
            user.is_staff or
            user.is_superuser or
            (hasattr(user, 'role') and user.role in ['admin', 'supervisor'])
        )

        if not is_admin:
            return Response(
                {"error": "Only admins can update schedules"},
                status=status.HTTP_403_FORBIDDEN
            )

        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """Only admins can delete schedules."""
        user = request.user
        is_admin = (
            user.is_staff or
            user.is_superuser or
            (hasattr(user, 'role') and user.role in ['admin', 'supervisor'])
        )

        if not is_admin:
            return Response(
                {"error": "Only admins can delete schedules"},
                status=status.HTTP_403_FORBIDDEN
            )

        return super().destroy(request, *args, **kwargs)


class MyScheduleView(views.APIView):
    """
    Get the current instructor's full weekly schedule across a season.

    Combines two schedule types:
    - **supervisor_schedules**: recurring weekly supervision shifts
      (SupervisorSchedule — day-of-week + time window)
    - **course_schedules**: lecture-day schedules for courses assigned to
      the instructor in the given season (CourseSchedule — weekday + time)

    GET /api/attendance/my-schedule/
    GET /api/attendance/my-schedule/?season_id=3

    Query parameters:
    - ``season_id`` (optional): restrict course_schedules to this season.
      Defaults to the currently active season.  Pass ``season_id=all`` to
      return course schedules across every season.

    Performance: both querysets use select_related to avoid N+1 queries.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        if not hasattr(user, 'instructor_profile'):
            return Response(
                {"detail": "No instructor profile found for this user."},
                status=status.HTTP_404_NOT_FOUND,
            )

        instructor = user.instructor_profile

        # --- Supervisor schedules (not season-scoped; they repeat weekly) ---
        supervisor_qs = (
            SupervisorSchedule.objects
            .filter(instructor=instructor)
            .select_related('instructor__user')
            .order_by('day_of_week', 'start_time')
        )

        # --- Course schedules (season-scoped) ---
        season_param = request.query_params.get('season_id')

        course_qs = (
            CourseSchedule.objects
            .filter(course__instructor=instructor)
            .select_related('course__season')
            .order_by('weekday', 'start_time')
        )

        if season_param and season_param != 'all':
            try:
                season_id = int(season_param)
            except ValueError:
                return Response(
                    {"detail": "season_id must be an integer or 'all'."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            course_qs = course_qs.filter(course__season_id=season_id)
        elif season_param != 'all':
            # Default: active season only
            active_season = Season.objects.filter(is_active=True).first()
            if active_season:
                course_qs = course_qs.filter(course__season=active_season)
            else:
                course_qs = course_qs.none()

        return Response({
            "supervisor_schedules": SupervisorScheduleSerializer(
                supervisor_qs, many=True
            ).data,
            "course_schedules": InstructorCourseScheduleSerializer(
                course_qs, many=True
            ).data,
        })


class MyAttendanceView(generics.ListAPIView):
    """
    List all attendance records (past and future) for the authenticated instructor.

    GET /api/attendance/my-attendance/
    GET /api/attendance/my-attendance/?season_id=3
    GET /api/attendance/my-attendance/?status=present
    GET /api/attendance/my-attendance/?attendance_type=lecture

    Query parameters:
    - ``season_id``       – filter by season (default: active season; ``all`` = no filter)
    - ``status``          – one of: present, absent, late, pending, not_started
    - ``attendance_type`` – lecture | supervision
    - ``date_from``       – YYYY-MM-DD (inclusive lower bound)
    - ``date_to``         – YYYY-MM-DD (inclusive upper bound)

    Performance: uses select_related to avoid N+1 queries on lecture/schedule/season.
    """

    serializer_class = InstructorAttendanceListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        if not hasattr(user, 'instructor_profile'):
            return InstructorAttendance.objects.none()

        qs = (
            InstructorAttendance.objects
            .filter(instructor=user.instructor_profile)
            .select_related(
                'instructor__user',
                'lecture__course',
                'schedule',
                'season',
            )
            .order_by('-date', 'attendance_type')
        )

        params = self.request.query_params
        season_param = params.get('season_id')

        if season_param and season_param != 'all':
            try:
                qs = qs.filter(season_id=int(season_param))
            except ValueError:
                return InstructorAttendance.objects.none()
        elif season_param != 'all':
            active_season = Season.objects.filter(is_active=True).first()
            if active_season:
                qs = qs.filter(season=active_season)

        if status_filter := params.get('status'):
            qs = qs.filter(status=status_filter)

        if atype := params.get('attendance_type'):
            qs = qs.filter(attendance_type=atype)

        if date_from := params.get('date_from'):
            qs = qs.filter(date__gte=date_from)

        if date_to := params.get('date_to'):
            qs = qs.filter(date__lte=date_to)

        return qs


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def manual_check_in(request, pk):
    """
    Manually check in an instructor (by admin).

    POST /api/attendance/<id>/manual-check-in/
    """
    attendance = get_object_or_404(InstructorAttendance, pk=pk)

    if attendance.check_in_time:
        return Response(
            {"error": "Already checked in"},
            status=status.HTTP_400_BAD_REQUEST
        )

    attendance.mark_checked_in(device=None, method=CheckInMethod.MANUAL)

    return Response(
        InstructorAttendanceSerializer(attendance).data,
        status=status.HTTP_200_OK
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def manual_check_out(request, pk):
    """
    Manually check out an instructor (by admin).

    POST /api/attendance/<id>/manual-check-out/
    """
    attendance = get_object_or_404(InstructorAttendance, pk=pk)

    try:
        attendance.mark_checked_out(device=None, method=CheckInMethod.MANUAL)
    except ValidationError as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )

    return Response(
        InstructorAttendanceSerializer(attendance).data,
        status=status.HTTP_200_OK
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def mark_absent(request, pk):
    """
    Mark an instructor as absent (by admin).

    POST /api/attendance/<id>/mark-absent/
    """
    attendance = get_object_or_404(InstructorAttendance, pk=pk)
    attendance.mark_absent()

    return Response(
        InstructorAttendanceSerializer(attendance).data,
        status=status.HTTP_200_OK
    )


class GenerateAttendanceView(views.APIView):
    """
    Generate attendance records for a date range.

    POST /api/attendance/generate/
    {
        "start_date": "2026-03-01",
        "end_date": "2026-03-07",
        "season_id": 1  // optional
    }

    This endpoint allows SUPERUSERS ONLY to manually generate attendance records
    for instructors and supervisors within a specified date range.

    Features:
    - Checks if records already exist for the date range and rejects if so
    - Records are created based on:
      - SupervisorSchedule entries for each day (supervision attendance)
      - Scheduled lectures for each day (lecture attendance)
    - Logs the generation in AttendanceCronLog for audit trail

    Restrictions:
    - Only superusers can access this endpoint
    - Maximum date range is 30 days
    - Cannot generate if records already exist for the date range
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Only superusers can generate attendance
        if not request.user.is_superuser:
            return Response(
                {"error": "Only superusers can generate attendance records"},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = GenerateAttendanceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        start_date = serializer.validated_data['start_date']
        end_date = serializer.validated_data['end_date']
        season_id = serializer.validated_data.get('season_id')

        # Get season if specified
        season = None
        if season_id:
            season = Season.objects.filter(id=season_id).first()
            if not season:
                return Response(
                    {"error": f"Season with ID {season_id} not found"},
                    status=status.HTTP_404_NOT_FOUND
                )

        # Check if attendance records already exist for this date range
        existing_count = InstructorAttendance.objects.filter(
            date__gte=start_date,
            date__lte=end_date
        ).count()

        if existing_count > 0:
            return Response(
                {
                    "error": "Attendance records already exist for this date range",
                    "existing_count": existing_count,
                    "start_date": str(start_date),
                    "end_date": str(end_date),
                    "hint": "Choose a date range with no existing records"
                },
                status=status.HTTP_409_CONFLICT
            )

        # Generate attendance records
        created_count = InstructorAttendance.generate_for_date_range(
            start_date=start_date,
            end_date=end_date,
            season=season
        )

        # Log the manual generation
        AttendanceCronLog.objects.create(
            job_name="manual_generate_attendance",
            details=(
                f"Superuser {request.user.get_full_name()} manually generated "
                f"{created_count} attendance records from {start_date} to {end_date}"
                f"{f' for season {season.name}' if season else ''}"
            )
        )

        return Response({
            "message": "Attendance records generated successfully",
            "created_count": created_count,
            "start_date": str(start_date),
            "end_date": str(end_date),
            "season": season.name if season else "Active season"
        }, status=status.HTTP_201_CREATED)

