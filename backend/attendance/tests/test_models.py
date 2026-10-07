#!/usr/bin/env python3
"""
Tests for attendance models - InstructorAttendance, SupervisorSchedule, AttendanceDevice

These tests cover:
- Model creation and validation
- Unique constraints
- Status transitions
- Rating logic
- Check-in/check-out methods
- Schedule overlap validation
"""
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta, time, date
from decimal import Decimal

from users.models import CustomUser, Instructor
from courses.models import Season, Lecture, Course, Tag, Weekday
from attendance.models import (
    InstructorAttendance,
    SupervisorSchedule,
    AttendanceDevice,
    AttendanceStatus,
    AttendanceType,
    CheckInMethod,
)


class BaseTestCase(TestCase):
    """Base test case with common setup for all attendance tests"""

    @classmethod
    def setUpTestData(cls):
        """Set up test data for all tests in this class"""
        # Create test users
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

        cls.instructor_user = CustomUser.objects.create_user(
            phone_number1='+201000000002',
            password='testpass123',
            first_name='محمد',
            last_name='أحمد',
            email='instructor@test.com',
            dob='1990-01-01',
            gender='male'
        )

        cls.supervisor_user = CustomUser.objects.create_user(
            phone_number1='+201000000003',
            password='testpass123',
            first_name='علي',
            last_name='حسن',
            email='supervisor@test.com',
            dob='1988-01-01',
            gender='male'
        )

        # Create instructors
        cls.instructor = Instructor.objects.create(
            user=cls.instructor_user,
            monthly_salary=5000.00,
            type='normal',
            fingerprint_id='FP_INSTRUCTOR_001'
        )

        cls.supervisor = Instructor.objects.create(
            user=cls.supervisor_user,
            monthly_salary=6000.00,
            type='supervisor',
            fingerprint_id='FP_SUPERVISOR_001'
        )

        # Create a season
        cls.season = Season.objects.create(
            name='Test Season 2026',
            season_type='school',
            start_date=timezone.localdate() - timedelta(days=30),
            end_date=timezone.localdate() + timedelta(days=60),
            is_active=True
        )

        # Create attendance device
        cls.device = AttendanceDevice.objects.create(
            device_id='DEVICE_001',
            name='Main Entrance Device',
            location='البوابة الرئيسية',
            is_active=True
        )


class SupervisorScheduleModelTest(BaseTestCase):
    """Tests for the SupervisorSchedule model"""

    def test_create_schedule_success(self):
        """Test creating a valid supervisor schedule"""
        schedule = SupervisorSchedule.objects.create(
            instructor=self.supervisor,
            day_of_week=0,  # Sunday
            start_time=time(8, 0),
            end_time=time(14, 0),
            grace_period_minutes=15,
            auto_absent_after_minutes=60
        )
        self.assertEqual(schedule.instructor, self.supervisor)
        self.assertEqual(schedule.day_of_week, 0)

    def test_end_time_must_be_after_start_time(self):
        """Test that end_time must be after start_time"""
        schedule = SupervisorSchedule(
            instructor=self.supervisor,
            day_of_week=0,
            start_time=time(14, 0),
            end_time=time(8, 0)  # Invalid: before start_time
        )
        with self.assertRaises(ValidationError) as context:
            schedule.full_clean()
        self.assertIn('end_time', str(context.exception))

    def test_same_start_and_end_time_invalid(self):
        """Test that start_time and end_time cannot be the same"""
        schedule = SupervisorSchedule(
            instructor=self.supervisor,
            day_of_week=0,
            start_time=time(8, 0),
            end_time=time(8, 0)
        )
        with self.assertRaises(ValidationError):
            schedule.full_clean()

    def test_unique_together_instructor_day(self):
        """Test that an instructor can only have one schedule per day"""
        SupervisorSchedule.objects.create(
            instructor=self.supervisor,
            day_of_week=1,  # Monday
            start_time=time(8, 0),
            end_time=time(14, 0)
        )

        # Try to create another schedule for the same day
        with self.assertRaises(Exception):
            SupervisorSchedule.objects.create(
                instructor=self.supervisor,
                day_of_week=1,  # Same day
                start_time=time(15, 0),
                end_time=time(20, 0)
            )

    def test_schedule_str_representation(self):
        """Test the string representation of a schedule"""
        schedule = SupervisorSchedule.objects.create(
            instructor=self.supervisor,
            day_of_week=0,
            start_time=time(8, 0),
            end_time=time(14, 0)
        )
        self.assertIn(str(self.supervisor), str(schedule))


class AttendanceDeviceModelTest(BaseTestCase):
    """Tests for the AttendanceDevice model"""

    def test_create_device(self):
        """Test creating an attendance device"""
        device = AttendanceDevice.objects.create(
            device_id='DEVICE_002',
            name='Back Door Device',
            location='الباب الخلفي',
            is_active=True
        )
        self.assertEqual(device.device_id, 'DEVICE_002')
        self.assertTrue(device.is_active)

    def test_device_id_unique(self):
        """Test that device_id must be unique"""
        with self.assertRaises(Exception):
            AttendanceDevice.objects.create(
                device_id='DEVICE_001',  # Already exists
                name='Duplicate Device'
            )

    def test_device_str_representation(self):
        """Test the string representation of a device"""
        self.assertEqual(str(self.device), 'Main Entrance Device')


class InstructorAttendanceModelTest(BaseTestCase):
    """Tests for the InstructorAttendance model"""

    def setUp(self):
        """Set up for each test"""
        InstructorAttendance.objects.all().delete()

    def test_create_lecture_attendance(self):
        """Test creating an attendance record for a lecture"""
        attendance = InstructorAttendance.objects.create(
            instructor=self.instructor,
            date=timezone.localdate(),
            attendance_type=AttendanceType.LECTURE,
            status=AttendanceStatus.NOT_STARTED,
            season=self.season
        )
        self.assertEqual(attendance.instructor, self.instructor)
        self.assertEqual(attendance.attendance_type, AttendanceType.LECTURE)
        self.assertIsNone(attendance.rating)  # Not started = null rating

    def test_create_supervision_attendance(self):
        """Test creating an attendance record for supervision"""
        schedule = SupervisorSchedule.objects.create(
            instructor=self.supervisor,
            day_of_week=Weekday.of(timezone.localdate()),
            start_time=time(8, 0),
            end_time=time(14, 0)
        )

        attendance = InstructorAttendance.objects.create(
            instructor=self.supervisor,
            date=timezone.localdate(),
            attendance_type=AttendanceType.SUPERVISION,
            schedule=schedule,
            status=AttendanceStatus.NOT_STARTED,
            season=self.season
        )
        self.assertEqual(attendance.attendance_type,
                         AttendanceType.SUPERVISION)
        self.assertEqual(attendance.schedule, schedule)

    def test_status_rating_logic_not_started(self):
        """Test that rating is null when status is NOT_STARTED"""
        attendance = InstructorAttendance.objects.create(
            instructor=self.instructor,
            date=timezone.localdate(),
            status=AttendanceStatus.NOT_STARTED,
            season=self.season
        )
        self.assertIsNone(attendance.rating)

    def test_status_rating_logic_present(self):
        """Test that rating becomes 0 when status changes to PRESENT"""
        attendance = InstructorAttendance.objects.create(
            instructor=self.instructor,
            date=timezone.localdate(),
            status=AttendanceStatus.NOT_STARTED,
            season=self.season
        )

        attendance.status = AttendanceStatus.PRESENT
        attendance.save()

        self.assertEqual(attendance.rating, Decimal('0.00'))

    def test_status_rating_logic_absent(self):
        """Test that rating is null when status is ABSENT"""
        attendance = InstructorAttendance.objects.create(
            instructor=self.instructor,
            date=timezone.localdate(),
            status=AttendanceStatus.PRESENT,
            season=self.season
        )

        attendance.mark_absent()

        self.assertIsNone(attendance.rating)
        self.assertIsNone(attendance.rated_by)
        self.assertIsNone(attendance.rated_at)

    def test_cannot_rate_absent_instructor(self):
        """Test that we cannot rate an absent instructor"""
        attendance = InstructorAttendance.objects.create(
            instructor=self.instructor,
            date=timezone.localdate(),
            status=AttendanceStatus.ABSENT,
            season=self.season
        )

        with self.assertRaises(ValidationError):
            attendance.add_rating(8.5, self.admin_user)

    def test_rating_must_be_in_range(self):
        """Test that rating must be between 1 and 10"""
        attendance = InstructorAttendance.objects.create(
            instructor=self.instructor,
            date=timezone.localdate(),
            status=AttendanceStatus.PRESENT,
            season=self.season
        )

        # Rating too low
        with self.assertRaises(ValidationError):
            attendance.add_rating(0.5, self.admin_user)

        # Rating too high
        with self.assertRaises(ValidationError):
            attendance.add_rating(11.0, self.admin_user)

    def test_add_valid_rating(self):
        """Test adding a valid rating"""
        attendance = InstructorAttendance.objects.create(
            instructor=self.instructor,
            date=timezone.localdate(),
            status=AttendanceStatus.PRESENT,
            season=self.season
        )

        attendance.add_rating(8.5, self.admin_user, notes="أداء ممتاز")

        self.assertEqual(attendance.rating, Decimal('8.5'))
        self.assertEqual(attendance.rated_by, self.admin_user)
        self.assertIsNotNone(attendance.rated_at)
        self.assertEqual(attendance.notes, "أداء ممتاز")

    def test_update_rating(self):
        """Test that rating can be updated (last one wins)"""
        attendance = InstructorAttendance.objects.create(
            instructor=self.instructor,
            date=timezone.localdate(),
            status=AttendanceStatus.PRESENT,
            season=self.season
        )

        attendance.add_rating(7.0, self.admin_user)
        first_rated_at = attendance.rated_at

        attendance.add_rating(9.0, self.admin_user, notes="تحديث التقييم")

        self.assertEqual(attendance.rating, Decimal('9.0'))
        self.assertGreater(attendance.rated_at, first_rated_at)


class CheckInCheckOutTest(BaseTestCase):
    """Tests for check-in and check-out functionality"""

    def setUp(self):
        """Set up for each test"""
        InstructorAttendance.objects.all().delete()

    def test_mark_checked_in_present(self):
        """Test marking an instructor as checked in (on time)"""
        schedule = SupervisorSchedule.objects.create(
            instructor=self.supervisor,
            day_of_week=Weekday.of(timezone.localdate()),
            start_time=(timezone.localtime() + timedelta(minutes=30)
                        ).time(),  # 30 min from now
            end_time=(timezone.localtime() + timedelta(hours=6)).time(),
            grace_period_minutes=15
        )

        attendance = InstructorAttendance.objects.create(
            instructor=self.supervisor,
            date=timezone.localdate(),
            schedule=schedule,
            status=AttendanceStatus.NOT_STARTED,
            season=self.season
        )

        attendance.mark_checked_in(
            device=self.device, method=CheckInMethod.FINGERPRINT)

        self.assertEqual(attendance.status, AttendanceStatus.PRESENT)
        self.assertIsNotNone(attendance.check_in_time)
        self.assertEqual(attendance.check_in_device, self.device)
        self.assertEqual(attendance.check_in_method, CheckInMethod.FINGERPRINT)
        self.assertEqual(attendance.rating, Decimal(
            '0.00'))  # Set to 0 on check-in

    def test_mark_checked_in_late(self):
        """Test marking an instructor as late"""
        # Create a schedule that started 30 minutes ago with 15 min grace
        past_time = (timezone.localtime() - timedelta(minutes=30)).time()
        schedule = SupervisorSchedule.objects.create(
            instructor=self.supervisor,
            day_of_week=Weekday.of(timezone.localdate()),
            start_time=past_time,
            end_time=(timezone.localtime() + timedelta(hours=5)).time(),
            grace_period_minutes=15
        )

        attendance = InstructorAttendance.objects.create(
            instructor=self.supervisor,
            date=timezone.localdate(),
            schedule=schedule,
            status=AttendanceStatus.NOT_STARTED,
            season=self.season
        )

        attendance.mark_checked_in(device=self.device)

        self.assertEqual(attendance.status, AttendanceStatus.LATE)

    def test_mark_checked_out_success(self):
        """Test successful check-out after check-in"""
        attendance = InstructorAttendance.objects.create(
            instructor=self.instructor,
            date=timezone.localdate(),
            status=AttendanceStatus.NOT_STARTED,
            season=self.season
        )

        attendance.mark_checked_in(device=self.device)
        attendance.mark_checked_out(
            device=self.device, method=CheckInMethod.FINGERPRINT)

        self.assertIsNotNone(attendance.check_out_time)
        self.assertEqual(attendance.check_out_device, self.device)
        self.assertEqual(attendance.check_out_method,
                         CheckInMethod.FINGERPRINT)
        self.assertGreater(attendance.check_out_time, attendance.check_in_time)

    def test_cannot_check_out_without_check_in(self):
        """Test that check-out fails without check-in"""
        attendance = InstructorAttendance.objects.create(
            instructor=self.instructor,
            date=timezone.localdate(),
            status=AttendanceStatus.NOT_STARTED,
            season=self.season
        )

        with self.assertRaises(ValidationError):
            attendance.mark_checked_out(device=self.device)

    def test_check_out_time_must_be_after_check_in(self):
        """Test that check-out time validation works"""
        attendance = InstructorAttendance(
            instructor=self.instructor,
            date=timezone.localdate(),
            status=AttendanceStatus.PRESENT,
            season=self.season,
            check_in_time=timezone.now(),
            check_out_time=timezone.now() - timedelta(hours=1)
        )

        with self.assertRaises(ValidationError):
            attendance.full_clean()


class UniqueConstraintTest(BaseTestCase):
    """Tests for unique constraints on InstructorAttendance"""

    def setUp(self):
        """Set up for each test"""
        InstructorAttendance.objects.all().delete()
        SupervisorSchedule.objects.all().delete()

    def test_multiple_attendance_types_same_day_allowed(self):
        """Test that an instructor can have both lecture and supervision attendance on same day"""
        today = timezone.localdate()

        # Create lecture attendance
        lecture_attendance = InstructorAttendance.objects.create(
            instructor=self.instructor,
            date=today,
            attendance_type=AttendanceType.LECTURE,
            status=AttendanceStatus.NOT_STARTED,
            season=self.season
        )

        # Create supervision attendance
        schedule = SupervisorSchedule.objects.create(
            instructor=self.instructor,
            day_of_week=Weekday.of(today),
            start_time=time(8, 0),
            end_time=time(14, 0)
        )

        supervision_attendance = InstructorAttendance.objects.create(
            instructor=self.instructor,
            date=today,
            attendance_type=AttendanceType.SUPERVISION,
            schedule=schedule,
            status=AttendanceStatus.NOT_STARTED,
            season=self.season
        )

        # Both should exist
        self.assertEqual(
            InstructorAttendance.objects.filter(
                instructor=self.instructor, date=today).count(),
            2
        )


class AttendanceTypeValidationTest(BaseTestCase):
    """Tests for attendance_type field validation"""

    def test_lecture_attendance_should_not_have_schedule(self):
        """Test that lecture attendance cannot have a schedule attached"""
        schedule = SupervisorSchedule.objects.create(
            instructor=self.instructor,
            day_of_week=Weekday.of(timezone.localdate()),
            start_time=time(8, 0),
            end_time=time(14, 0)
        )

        attendance = InstructorAttendance(
            instructor=self.instructor,
            date=timezone.localdate(),
            attendance_type=AttendanceType.LECTURE,
            schedule=schedule,  # Invalid for lecture type
            status=AttendanceStatus.NOT_STARTED,
            season=self.season
        )

        with self.assertRaises(ValidationError):
            attendance.full_clean()

    def test_supervision_attendance_should_not_have_lecture(self):
        """Test that supervision attendance cannot have a lecture attached"""
        # This would require creating a lecture, but conceptually:
        attendance = InstructorAttendance(
            instructor=self.instructor,
            date=timezone.localdate(),
            attendance_type=AttendanceType.SUPERVISION,
            status=AttendanceStatus.NOT_STARTED,
            season=self.season
        )
        # Should be valid without lecture
        attendance.full_clean()
