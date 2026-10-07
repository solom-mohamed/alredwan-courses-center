#!/usr/bin/env python3
"""
Tests for the attendance generation API endpoint.

These tests cover:
- GenerateAttendanceView for manually generating attendance records
- Date range validation (max 30 days)
- Permission checks (superuser only)
- Duplicate prevention (rejects if records exist)
- Integration with cron log
"""
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from datetime import timedelta, time

from users.models import CustomUser, Instructor
from courses.models import Season
from attendance.models import SupervisorSchedule, InstructorAttendance
from attendance.models.attendance_cron_log import AttendanceCronLog


class GenerateAttendanceTestCase(TestCase):
    """Tests for the generate attendance endpoint."""

    @classmethod
    def setUpTestData(cls):
        """Set up test data for all tests in this class."""
        # Create superuser (the ONLY user who can generate attendance)
        cls.superuser = CustomUser.objects.create_user(
            phone_number1='+201200000001',
            password='superpass123',
            first_name='Super',
            last_name='User',
            email='superuser_gen@test.com',
            dob='1985-01-01',
            gender='male',
            is_staff=True,
            is_superuser=True,
            role='admin'
        )

        # Create admin user (NOT superuser - should be rejected)
        cls.admin_user = CustomUser.objects.create_user(
            phone_number1='+201200000006',
            password='adminpass123',
            first_name='Admin',
            last_name='User',
            email='admin_only_gen@test.com',
            dob='1985-01-01',
            gender='male',
            is_staff=True,
            is_superuser=False,
            role='admin'
        )

        # Create regular user (not admin)
        cls.regular_user = CustomUser.objects.create_user(
            phone_number1='+201200000002',
            password='userpass123',
            first_name='Regular',
            last_name='User',
            email='regular_gen@test.com',
            dob='1990-01-01',
            gender='male'
        )

        # Create instructor user
        cls.instructor_user = CustomUser.objects.create_user(
            phone_number1='+201200000003',
            password='instrpass123',
            first_name='Instructor',
            last_name='One',
            email='instructor_gen@test.com',
            dob='1988-01-01',
            gender='male',
            role='instructor'
        )
        cls.instructor = Instructor.objects.create(
            user=cls.instructor_user,
            monthly_salary=4000.00,
            type='normal',
            fingerprint_id='FP_GEN_001'
        )

        # Create supervisor
        cls.supervisor_user = CustomUser.objects.create_user(
            phone_number1='+201200000004',
            password='superpass123',
            first_name='Supervisor',
            last_name='One',
            email='supervisor_gen@test.com',
            dob='1985-01-01',
            gender='male',
            role='supervisor'
        )
        cls.supervisor = Instructor.objects.create(
            user=cls.supervisor_user,
            monthly_salary=6000.00,
            type='supervisor',
            fingerprint_id='FP_GEN_SUPER_001'
        )

        # Create season
        cls.season = Season.objects.create(
            name='Test Season Generate 2026',
            season_type='school',
            start_date=timezone.localdate() - timedelta(days=30),
            end_date=timezone.localdate() + timedelta(days=60),
            is_active=True
        )

        # Create schedules for supervisor (Saturday and Sunday)
        cls.schedule_sat = SupervisorSchedule.objects.create(
            instructor=cls.supervisor,
            day_of_week=0,  # Saturday
            start_time=time(8, 0),
            end_time=time(14, 0),
            grace_period_minutes=15,
            auto_absent_after_minutes=30
        )
        cls.schedule_sun = SupervisorSchedule.objects.create(
            instructor=cls.supervisor,
            day_of_week=1,  # Sunday
            start_time=time(8, 0),
            end_time=time(14, 0),
            grace_period_minutes=15,
            auto_absent_after_minutes=30
        )

    def setUp(self):
        """Set up for each test."""
        self.client = APIClient()
        self.url = '/api/attendance/generate/'
        # Clear attendance records before each test
        InstructorAttendance.objects.all().delete()
        AttendanceCronLog.objects.all().delete()

    # ========== Permission Tests ==========

    def test_superuser_can_generate_attendance(self):
        """Only superusers can generate attendance records."""
        self.client.force_authenticate(user=self.superuser)

        # Use a date range that includes both Saturday and Sunday
        # Future dates to avoid conflicts
        start_date = timezone.localdate() + timedelta(days=60)
        end_date = start_date + timedelta(days=7)

        response = self.client.post(self.url, {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat()
        })

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('created_count', response.data)
        self.assertIn('message', response.data)

    def test_admin_user_cannot_generate(self):
        """Admin users (not superuser) cannot generate attendance records."""
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.post(self.url, {
            'start_date': timezone.localdate().isoformat(),
            'end_date': (timezone.localdate() + timedelta(days=7)).isoformat()
        })

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('error', response.data)
        self.assertIn('superuser', response.data['error'].lower())

    def test_regular_user_cannot_generate(self):
        """Regular users cannot generate attendance records."""
        self.client.force_authenticate(user=self.regular_user)

        response = self.client.post(self.url, {
            'start_date': timezone.localdate().isoformat(),
            'end_date': (timezone.localdate() + timedelta(days=7)).isoformat()
        })

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_instructor_cannot_generate(self):
        """Instructors cannot generate attendance records."""
        self.client.force_authenticate(user=self.instructor_user)

        response = self.client.post(self.url, {
            'start_date': timezone.localdate().isoformat(),
            'end_date': (timezone.localdate() + timedelta(days=7)).isoformat()
        })

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_supervisor_cannot_generate(self):
        """Supervisors cannot generate attendance records."""
        self.client.force_authenticate(user=self.supervisor_user)

        response = self.client.post(self.url, {
            'start_date': timezone.localdate().isoformat(),
            'end_date': (timezone.localdate() + timedelta(days=7)).isoformat()
        })

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_cannot_generate(self):
        """Unauthenticated users cannot generate attendance records."""
        response = self.client.post(self.url, {
            'start_date': timezone.localdate().isoformat(),
            'end_date': (timezone.localdate() + timedelta(days=7)).isoformat()
        })

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # ========== Validation Tests ==========

    def test_end_date_before_start_date_rejected(self):
        """End date before start date should be rejected."""
        self.client.force_authenticate(user=self.superuser)

        start_date = timezone.localdate() + timedelta(days=7)
        end_date = timezone.localdate()

        response = self.client.post(self.url, {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat()
        })

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('end_date', response.data)

    def test_date_range_exceeds_30_days_rejected(self):
        """Date range exceeding 30 days should be rejected."""
        self.client.force_authenticate(user=self.superuser)

        start_date = timezone.localdate() + timedelta(days=100)  # Far future
        end_date = start_date + timedelta(days=31)

        response = self.client.post(self.url, {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat()
        })

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('end_date', response.data)

    def test_date_range_exactly_30_days_allowed(self):
        """Date range of exactly 30 days should be allowed."""
        self.client.force_authenticate(user=self.superuser)

        start_date = timezone.localdate() + timedelta(days=200)  # Far future
        end_date = start_date + timedelta(days=30)

        response = self.client.post(self.url, {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat()
        })

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_missing_start_date_rejected(self):
        """Missing start_date should be rejected."""
        self.client.force_authenticate(user=self.superuser)

        response = self.client.post(self.url, {
            'end_date': timezone.localdate().isoformat()
        })

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_end_date_rejected(self):
        """Missing end_date should be rejected."""
        self.client.force_authenticate(user=self.superuser)

        response = self.client.post(self.url, {
            'start_date': timezone.localdate().isoformat()
        })

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_date_format_rejected(self):
        """Invalid date format should be rejected."""
        self.client.force_authenticate(user=self.superuser)

        response = self.client.post(self.url, {
            'start_date': 'invalid-date',
            'end_date': timezone.localdate().isoformat()
        })

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ========== Duplicate Prevention Tests ==========

    def test_rejects_if_records_already_exist(self):
        """Should reject if attendance records already exist for the date range."""
        self.client.force_authenticate(user=self.superuser)

        start_date = timezone.localdate() + timedelta(days=70)
        end_date = start_date + timedelta(days=7)

        # First generation should succeed
        response1 = self.client.post(self.url, {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat()
        })
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)

        # Second generation (same range) should be rejected with 409 Conflict
        response2 = self.client.post(self.url, {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat()
        })
        self.assertEqual(response2.status_code, status.HTTP_409_CONFLICT)
        self.assertIn('error', response2.data)
        self.assertIn('already exist', response2.data['error'])
        self.assertIn('existing_count', response2.data)

    def test_rejects_if_partial_overlap_exists(self):
        """Should reject if any records exist within the date range."""
        self.client.force_authenticate(user=self.superuser)

        # Create an attendance record for a specific date
        test_date = timezone.localdate() + timedelta(days=80)
        InstructorAttendance.objects.create(
            instructor=self.supervisor,
            schedule=self.schedule_sat,
            date=test_date,
            season=self.season,
            attendance_type='supervision',
            status='not_started'
        )

        # Try to generate for a range that includes the existing record
        start_date = test_date - timedelta(days=3)
        end_date = test_date + timedelta(days=3)

        response = self.client.post(self.url, {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat()
        })

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(response.data['existing_count'], 1)

    # ========== Functionality Tests ==========

    def test_generates_attendance_for_schedules(self):
        """Should generate attendance records based on schedules."""
        self.client.force_authenticate(user=self.superuser)

        # Use a week-long range in far future
        start_date = timezone.localdate() + timedelta(days=90)
        end_date = start_date + timedelta(days=7)

        response = self.client.post(self.url, {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat()
        })

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Should have created at least 1 attendance record
        # (depends on how many Saturdays/Sundays are in the range)
        self.assertGreaterEqual(response.data['created_count'], 0)

        # Check database
        attendance_count = InstructorAttendance.objects.filter(
            instructor=self.supervisor,
            date__gte=start_date,
            date__lte=end_date
        ).count()
        self.assertEqual(attendance_count, response.data['created_count'])

    def test_logs_generation_in_cron_log(self):
        """Should log the generation in AttendanceCronLog."""
        self.client.force_authenticate(user=self.superuser)

        start_date = timezone.localdate() + timedelta(days=100)
        end_date = start_date + timedelta(days=7)

        response = self.client.post(self.url, {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat()
        })

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Check that a log entry was created
        log = AttendanceCronLog.objects.filter(
            job_name='manual_generate_attendance'
        ).first()

        self.assertIsNotNone(log)
        self.assertIn('Super User', log.details)  # Superuser name
        self.assertIn(str(start_date), log.details)
        self.assertIn(str(end_date), log.details)

    def test_uses_active_season_by_default(self):
        """Should use the active season if none specified."""
        self.client.force_authenticate(user=self.superuser)

        start_date = timezone.localdate() + timedelta(days=110)
        end_date = start_date + timedelta(days=7)

        response = self.client.post(self.url, {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat()
        })

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['season'], 'Active season')

    def test_can_specify_season_id(self):
        """Should use specified season if provided."""
        self.client.force_authenticate(user=self.superuser)

        start_date = timezone.localdate() + timedelta(days=120)
        end_date = start_date + timedelta(days=7)

        response = self.client.post(self.url, {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'season_id': self.season.id
        })

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['season'], self.season.name)

    def test_invalid_season_id_rejected(self):
        """Should return 404 for invalid season ID."""
        self.client.force_authenticate(user=self.superuser)

        start_date = timezone.localdate() + timedelta(days=130)
        end_date = start_date + timedelta(days=7)

        response = self.client.post(self.url, {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'season_id': 99999
        })

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.data)

    def test_response_format(self):
        """Should return expected response format."""
        self.client.force_authenticate(user=self.superuser)

        start_date = timezone.localdate() + timedelta(days=140)
        end_date = start_date + timedelta(days=7)

        response = self.client.post(self.url, {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat()
        })

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('message', response.data)
        self.assertIn('created_count', response.data)
        self.assertIn('start_date', response.data)
        self.assertIn('end_date', response.data)
        self.assertIn('season', response.data)

        self.assertEqual(response.data['start_date'], str(start_date))
        self.assertEqual(response.data['end_date'], str(end_date))


class SupervisionWeekdayMappingTest(TestCase):
    """day_of_week is the Weekday enum (Sat=0), so a Saturday schedule must land on Saturdays."""

    def test_schedules_land_on_their_own_weekday(self):
        user = CustomUser.objects.create_user(
            phone_number1='+201000000977', password='Password123!',
            first_name='Sup', last_name='Ervisor', role='instructor',
            dob='1980-01-01', gender='male')
        supervisor = Instructor.objects.create(
            user=user, monthly_salary=1000, type='supervisor')
        today = timezone.localdate()
        Season.objects.create(
            name='Weekday season', season_type='school',
            start_date=today - timedelta(days=30),
            end_date=today + timedelta(days=60), is_active=True)
        SupervisorSchedule.objects.create(
            instructor=supervisor, day_of_week=0,  # Saturday
            start_time=time(8, 0), end_time=time(14, 0))
        SupervisorSchedule.objects.create(
            instructor=supervisor, day_of_week=2,  # Monday
            start_time=time(8, 0), end_time=time(14, 0))

        InstructorAttendance.generate_for_date_range(today, today + timedelta(days=6))

        # Python weekday(): Monday=0 … Saturday=5
        days = sorted(a.date.weekday() for a in InstructorAttendance.objects.filter(
            instructor=supervisor))
        self.assertEqual(days, [0, 5])


class AttendanceInstructorIdFilterTest(TestCase):
    """GET /api/attendance/all/?instructor_id=<Instructor.id> — used by "سجل الحضور الكامل"."""

    def test_filters_by_instructor_id_without_date(self):
        from rest_framework.test import APIClient
        from attendance.models import AttendanceType, AttendanceStatus

        admin = CustomUser.objects.create_user(
            phone_number1='+201000000981', password='Password123!',
            first_name='Ad', last_name='Min', role='admin',
            dob='1980-01-01', gender='male', is_staff=True)
        instructors = []
        for i in range(2):
            user = CustomUser.objects.create_user(
                phone_number1=f'+20100000098{i + 2}', password='Password123!',
                first_name='Ins', last_name=str(i), role='instructor',
                dob='1980-01-01', gender='male')
            instructors.append(Instructor.objects.create(user=user, monthly_salary=1000))
        today = timezone.localdate()
        season = Season.objects.create(
            name='Filter season', season_type='school',
            start_date=today - timedelta(days=90), is_active=True)
        for offset in (0, 10, 40):
            for instructor in instructors:
                InstructorAttendance.objects.create(
                    instructor=instructor, date=today - timedelta(days=offset),
                    attendance_type=AttendanceType.SUPERVISION,
                    status=AttendanceStatus.NOT_STARTED, season=season)

        client = APIClient()
        client.force_authenticate(user=admin)
        response = client.get('/api/attendance/all/', {
            'instructor_id': instructors[0].id, 'page_size': 100})

        self.assertEqual(response.status_code, 200, response.data)
        results = response.data['results'] if isinstance(response.data, dict) else response.data
        self.assertEqual(len(results), 3)
