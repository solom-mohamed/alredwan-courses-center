#!/usr/bin/env python3
"""
Tests for the unified fingerprint scan endpoint and FingerprintScanLog model.

These tests cover:
- Unified scan endpoint logic (auto check-in/out/re-entry)
- Auto-creation of attendance records
- Rapid scan detection and ignoring
- FingerprintScanLog model functionality
- Edge cases for fingerprint-based attendance
"""
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from datetime import timedelta, time
from decimal import Decimal

from users.models import CustomUser, Instructor
from courses.models import Season, Course, CourseSchedule, Lecture, Weekday
from attendance.models import (
    InstructorAttendance,
    SupervisorSchedule,
    AttendanceDevice,
    AttendanceStatus,
    AttendanceType,
    CheckInMethod,
    FingerprintScanLog,
    ScanAction,
)


class UnifiedFingerprintScanTestCase(TestCase):
    """Base test case with common setup for unified scan tests"""

    @classmethod
    def setUpTestData(cls):
        """Set up test data for all tests in this class"""
        # Create admin user
        cls.admin_user = CustomUser.objects.create_user(
            phone_number1='+201000000001',
            password='adminpass123',
            first_name='Admin',
            last_name='User',
            email='admin@test.com',
            dob='1985-01-01',
            gender='male',
            is_staff=True,
            is_superuser=True
        )

        # Create instructor user
        cls.instructor_user = CustomUser.objects.create_user(
            phone_number1='+201000000002',
            password='userpass123',
            first_name='Test',
            last_name='Instructor',
            email='instructor@test.com',
            dob='1990-01-01',
            gender='male'
        )

        # Create instructor with fingerprint
        cls.instructor = Instructor.objects.create(
            user=cls.instructor_user,
            monthly_salary=5000.00,
            type='normal',
            fingerprint_id='FP_UNIFIED_001'
        )

        # Create season
        cls.season = Season.objects.create(
            name='Test Season 2026',
            season_type='school',
            start_date=timezone.localdate() - timedelta(days=30),
            end_date=timezone.localdate() + timedelta(days=60),
            is_active=True
        )

        # Create device
        cls.device = AttendanceDevice.objects.create(
            device_id='DEVICE_UNIFIED_001',
            name='Test Device',
            location='Test Location',
            is_active=True
        )

    def setUp(self):
        """Set up for each test"""
        self.client = APIClient()
        InstructorAttendance.objects.all().delete()
        FingerprintScanLog.objects.all().delete()


class UnifiedScanAutoCreateTest(UnifiedFingerprintScanTestCase):
    """Tests for auto-creation of attendance records on scan"""

    def test_scan_auto_creates_attendance_no_schedule(self):
        """Test that scan auto-creates attendance when no record exists (no schedule)"""
        response = self.client.post('/api/attendance/scan/', {
            'fingerprint_id': 'FP_UNIFIED_001',
            'device_id': 'DEVICE_UNIFIED_001',
        })

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['action'], 'auto_create_check_in')
        self.assertTrue(response.data['records'][0]['auto_created'])
        
        # Verify attendance was created
        attendance = InstructorAttendance.objects.filter(
            instructor=self.instructor,
            date=timezone.localdate()
        ).first()
        self.assertIsNotNone(attendance)
        self.assertIsNotNone(attendance.check_in_time)
        self.assertEqual(attendance.status, AttendanceStatus.PRESENT)

    def test_scan_auto_creates_from_supervisor_schedule(self):
        """Test that scan creates attendance based on supervisor schedule"""
        today = timezone.localdate()
        weekday = Weekday.of(today)
        
        # Create schedule for today
        schedule = SupervisorSchedule.objects.create(
            instructor=self.instructor,
            day_of_week=weekday,
            start_time=time(8, 0),
            end_time=time(14, 0),
            grace_period_minutes=20
        )

        response = self.client.post('/api/attendance/scan/', {
            'fingerprint_id': 'FP_UNIFIED_001',
            'device_id': 'DEVICE_UNIFIED_001',
        })

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify attendance is linked to schedule
        attendance = InstructorAttendance.objects.filter(
            instructor=self.instructor,
            date=today,
            schedule=schedule
        ).first()
        self.assertIsNotNone(attendance)
        self.assertEqual(attendance.attendance_type, AttendanceType.SUPERVISION)


class UnifiedScanCheckInOutTest(UnifiedFingerprintScanTestCase):
    """Tests for check-in and check-out toggle behavior"""

    def test_first_scan_checks_in(self):
        """Test that first scan on existing record checks in"""
        InstructorAttendance.objects.create(
            instructor=self.instructor,
            date=timezone.localdate(),
            status=AttendanceStatus.NOT_STARTED,
            season=self.season
        )

        response = self.client.post('/api/attendance/scan/', {
            'fingerprint_id': 'FP_UNIFIED_001',
            'device_id': 'DEVICE_UNIFIED_001',
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['action'], 'check_in')
        self.assertIn('check_in_time', response.data)

    def test_second_scan_checks_out(self):
        """Test that second scan checks out"""
        # Create and check in
        attendance = InstructorAttendance.objects.create(
            instructor=self.instructor,
            date=timezone.localdate(),
            status=AttendanceStatus.PRESENT,
            check_in_time=timezone.now() - timedelta(hours=4),
            season=self.season
        )
        
        # Clear any recent scans
        FingerprintScanLog.objects.all().delete()

        response = self.client.post('/api/attendance/scan/', {
            'fingerprint_id': 'FP_UNIFIED_001',
            'device_id': 'DEVICE_UNIFIED_001',
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['action'], 'check_out')
        
        attendance.refresh_from_db()
        self.assertIsNotNone(attendance.check_out_time)

    def test_third_scan_re_entry(self):
        """Test that third scan after checkout triggers re-entry"""
        # Create with check-in and check-out
        attendance = InstructorAttendance.objects.create(
            instructor=self.instructor,
            date=timezone.localdate(),
            status=AttendanceStatus.PRESENT,
            check_in_time=timezone.now() - timedelta(hours=6),
            check_out_time=timezone.now() - timedelta(hours=1),
            season=self.season
        )
        
        # Clear any recent scans
        FingerprintScanLog.objects.all().delete()

        response = self.client.post('/api/attendance/scan/', {
            'fingerprint_id': 'FP_UNIFIED_001',
            'device_id': 'DEVICE_UNIFIED_001',
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['action'], 're_entry')
        self.assertTrue(response.data['records'][0]['re_entry'])
        
        attendance.refresh_from_db()
        self.assertIsNone(attendance.check_out_time)


class UnifiedScanRapidDuplicateTest(UnifiedFingerprintScanTestCase):
    """Tests for rapid duplicate scan detection"""

    def test_rapid_scan_ignored(self):
        """Test that rapid scans within 2 minutes are ignored"""
        # Create attendance and first scan
        InstructorAttendance.objects.create(
            instructor=self.instructor,
            date=timezone.localdate(),
            status=AttendanceStatus.NOT_STARTED,
            season=self.season
        )

        # First scan
        response1 = self.client.post('/api/attendance/scan/', {
            'fingerprint_id': 'FP_UNIFIED_001',
            'device_id': 'DEVICE_UNIFIED_001',
        })
        self.assertEqual(response1.data['action'], 'check_in')

        # Rapid second scan (should be ignored)
        response2 = self.client.post('/api/attendance/scan/', {
            'fingerprint_id': 'FP_UNIFIED_001',
            'device_id': 'DEVICE_UNIFIED_001',
        })

        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertIn('ignored', response2.data['message'].lower())

        # Verify ignored scan was logged
        ignored_scans = FingerprintScanLog.objects.filter(
            instructor=self.instructor,
            action=ScanAction.IGNORED
        )
        self.assertEqual(ignored_scans.count(), 1)


class UnifiedScanValidationTest(UnifiedFingerprintScanTestCase):
    """Tests for input validation"""

    def test_invalid_fingerprint_id(self):
        """Test scan with invalid fingerprint ID"""
        response = self.client.post('/api/attendance/scan/', {
            'fingerprint_id': 'INVALID_FP',
            'device_id': 'DEVICE_UNIFIED_001',
        })

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_device_id(self):
        """Test scan with invalid device ID"""
        response = self.client.post('/api/attendance/scan/', {
            'fingerprint_id': 'FP_UNIFIED_001',
            'device_id': 'INVALID_DEVICE',
        })

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_inactive_device(self):
        """Test scan with inactive device"""
        inactive_device = AttendanceDevice.objects.create(
            device_id='INACTIVE_DEVICE_001',
            name='Inactive Device',
            is_active=False
        )

        response = self.client.post('/api/attendance/scan/', {
            'fingerprint_id': 'FP_UNIFIED_001',
            'device_id': 'INACTIVE_DEVICE_001',
        })

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_fingerprint_id(self):
        """Test scan without fingerprint ID"""
        response = self.client.post('/api/attendance/scan/', {
            'device_id': 'DEVICE_UNIFIED_001',
        })

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_device_id(self):
        """Test scan without device ID"""
        response = self.client.post('/api/attendance/scan/', {
            'fingerprint_id': 'FP_UNIFIED_001',
        })

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class UnifiedScanNoSeasonTest(UnifiedFingerprintScanTestCase):
    """Tests for behavior when no active season"""

    def test_scan_fails_without_active_season(self):
        """Test that scan fails when no active season exists"""
        # Deactivate the season
        self.season.is_active = False
        self.season.save()

        response = self.client.post('/api/attendance/scan/', {
            'fingerprint_id': 'FP_UNIFIED_001',
            'device_id': 'DEVICE_UNIFIED_001',
        })

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('season', response.data['error'].lower())

        # Re-activate for other tests
        self.season.is_active = True
        self.season.save()


class UnifiedScanOfflineSyncTest(UnifiedFingerprintScanTestCase):
    """Tests for offline sync support"""

    def test_scan_with_custom_timestamp(self):
        """Test scan with device-provided timestamp"""
        InstructorAttendance.objects.create(
            instructor=self.instructor,
            date=timezone.localdate(),
            status=AttendanceStatus.NOT_STARTED,
            season=self.season
        )

        custom_time = timezone.now() - timedelta(hours=2)
        response = self.client.post('/api/attendance/scan/', {
            'fingerprint_id': 'FP_UNIFIED_001',
            'device_id': 'DEVICE_UNIFIED_001',
            'timestamp': custom_time.isoformat(),
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)


class FingerprintScanLogModelTest(TestCase):
    """Tests for FingerprintScanLog model"""

    @classmethod
    def setUpTestData(cls):
        cls.user = CustomUser.objects.create_user(
            phone_number1='+201000000003',
            password='pass123',
            first_name='Log',
            last_name='Test',
            dob='1990-01-01',
            gender='male'
        )
        cls.instructor = Instructor.objects.create(
            user=cls.user,
            monthly_salary=5000.00,
            type='normal',
            fingerprint_id='FP_LOG_001'
        )
        cls.device = AttendanceDevice.objects.create(
            device_id='DEVICE_LOG_001',
            name='Log Test Device',
            is_active=True
        )

    def test_scan_log_creation(self):
        """Test creating a scan log entry"""
        log = FingerprintScanLog.objects.create(
            instructor=self.instructor,
            scan_time=timezone.now(),
            device=self.device,
            action=ScanAction.CHECK_IN,
            is_processed=True
        )
        
        self.assertIsNotNone(log.id)
        self.assertEqual(log.action, ScanAction.CHECK_IN)

    def test_scan_log_str(self):
        """Test string representation of scan log"""
        log = FingerprintScanLog.objects.create(
            instructor=self.instructor,
            scan_time=timezone.now(),
            device=self.device,
            action=ScanAction.CHECK_IN
        )
        
        self.assertIn(self.instructor.user.get_full_name(), str(log))

    def test_get_recent_scans(self):
        """Test getting recent scans for instructor"""
        # Create old scan
        old_scan = FingerprintScanLog.objects.create(
            instructor=self.instructor,
            scan_time=timezone.now() - timedelta(minutes=10),
            device=self.device,
            action=ScanAction.CHECK_IN
        )
        
        # Create recent scan
        recent_scan = FingerprintScanLog.objects.create(
            instructor=self.instructor,
            scan_time=timezone.now(),
            device=self.device,
            action=ScanAction.CHECK_OUT
        )
        
        recent = FingerprintScanLog.get_recent_scans(self.instructor, minutes=5)
        self.assertEqual(recent.count(), 1)
        self.assertEqual(recent.first(), recent_scan)


class SupervisorScheduleAdminTest(TestCase):
    """Tests to verify SupervisorSchedule admin is registered"""

    def test_schedule_admin_accessible(self):
        """Test that schedule admin page is accessible"""
        admin = CustomUser.objects.create_superuser(
            phone_number1='+201000000004',
            password='adminpass123',
            first_name='Super',
            last_name='Admin',
            dob='1985-01-01',
            gender='male'
        )
        
        # Use force_login instead of login for custom user model
        self.client.force_login(admin)
        
        # Admin URL is custom: /Al-Redwan-superadmin-dashboard/
        response = self.client.get('/Al-Redwan-superadmin-dashboard/attendance/supervisorschedule/')
        # Should not be 404 (admin page exists)
        self.assertNotEqual(response.status_code, 404)


class MultipleRecordsSameDayTest(UnifiedFingerprintScanTestCase):
    """Tests for handling multiple attendance records on same day"""

    def test_scan_checks_in_all_records(self):
        """Test that scan checks in all records for the day"""
        today = timezone.localdate()
        
        # Create multiple records (lecture + supervision)
        lecture_record = InstructorAttendance.objects.create(
            instructor=self.instructor,
            date=today,
            status=AttendanceStatus.NOT_STARTED,
            attendance_type=AttendanceType.LECTURE,
            season=self.season
        )
        supervision_record = InstructorAttendance.objects.create(
            instructor=self.instructor,
            date=today,
            status=AttendanceStatus.NOT_STARTED,
            attendance_type=AttendanceType.SUPERVISION,
            season=self.season
        )

        response = self.client.post('/api/attendance/scan/', {
            'fingerprint_id': 'FP_UNIFIED_001',
            'device_id': 'DEVICE_UNIFIED_001',
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['records']), 2)
        
        # Verify both are checked in
        lecture_record.refresh_from_db()
        supervision_record.refresh_from_db()
        self.assertIsNotNone(lecture_record.check_in_time)
        self.assertIsNotNone(supervision_record.check_in_time)


class LateCheckInTest(UnifiedFingerprintScanTestCase):
    """Tests for late check-in detection"""

    def test_late_check_in_with_schedule(self):
        """Test that late check-in is detected with schedule"""
        today = timezone.localdate()
        weekday = Weekday.of(today)
        
        # Create schedule that started 1 hour ago with 15 min grace
        past_start = (timezone.now() - timedelta(hours=1)).time()
        
        schedule = SupervisorSchedule.objects.create(
            instructor=self.instructor,
            day_of_week=weekday,
            start_time=past_start,
            end_time=time(23, 59),
            grace_period_minutes=15
        )
        
        # Create attendance for this schedule
        attendance = InstructorAttendance.objects.create(
            instructor=self.instructor,
            date=today,
            status=AttendanceStatus.NOT_STARTED,
            attendance_type=AttendanceType.SUPERVISION,
            schedule=schedule,
            season=self.season
        )

        response = self.client.post('/api/attendance/scan/', {
            'fingerprint_id': 'FP_UNIFIED_001',
            'device_id': 'DEVICE_UNIFIED_001',
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        attendance.refresh_from_db()
        self.assertEqual(attendance.status, AttendanceStatus.LATE)


class ScanLogAuditTrailTest(UnifiedFingerprintScanTestCase):
    """Tests for verifying scan log audit trail"""

    def test_all_scans_are_logged(self):
        """Test that all scans create log entries"""
        InstructorAttendance.objects.create(
            instructor=self.instructor,
            date=timezone.localdate(),
            status=AttendanceStatus.NOT_STARTED,
            season=self.season
        )

        # First scan - check in
        self.client.post('/api/attendance/scan/', {
            'fingerprint_id': 'FP_UNIFIED_001',
            'device_id': 'DEVICE_UNIFIED_001',
        })

        logs = FingerprintScanLog.objects.filter(instructor=self.instructor)
        self.assertEqual(logs.count(), 1)
        self.assertEqual(logs.first().action, ScanAction.CHECK_IN)

    def test_ignored_scans_are_logged(self):
        """Test that ignored scans are also logged"""
        InstructorAttendance.objects.create(
            instructor=self.instructor,
            date=timezone.localdate(),
            status=AttendanceStatus.NOT_STARTED,
            season=self.season
        )

        # First scan
        self.client.post('/api/attendance/scan/', {
            'fingerprint_id': 'FP_UNIFIED_001',
            'device_id': 'DEVICE_UNIFIED_001',
        })

        # Rapid second scan
        self.client.post('/api/attendance/scan/', {
            'fingerprint_id': 'FP_UNIFIED_001',
            'device_id': 'DEVICE_UNIFIED_001',
        })

        logs = FingerprintScanLog.objects.filter(instructor=self.instructor)
        self.assertEqual(logs.count(), 2)
        
        ignored_log = logs.filter(action=ScanAction.IGNORED).first()
        self.assertIsNotNone(ignored_log)
        self.assertFalse(ignored_log.is_processed)
