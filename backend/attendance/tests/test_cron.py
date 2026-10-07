#!/usr/bin/env python3
"""
Tests for attendance cron jobs

These tests cover:
- Weekly attendance generation
- Daily absent marking
- Fallback absent marking for yesterday
- Cron log creation
"""
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta, time
from unittest.mock import patch

from users.models import CustomUser, Instructor
from courses.models import Season, Lecture, Course, Tag, Weekday
from courses.models.lecture import LectureStatus
from attendance.models import (
    InstructorAttendance,
    AttendanceCronLog,
    SupervisorSchedule,
    AttendanceStatus,
    AttendanceType,
)
from attendance.cron import (
    generate_instructor_attendance_weekly,
    mark_absent_daily,
    mark_absent_for_yesterday,
    update_pending_to_not_started,
    mark_lectures_without_attendance_as_cancelled,
    mark_lectures_without_attendance_as_cancelled_fallback,
)


class CronJobBaseTestCase(TestCase):
    """Base test case with common setup for cron job tests"""

    @classmethod
    def setUpTestData(cls):
        """Set up test data for all tests in this class"""
        # Create test users
        cls.supervisor_user = CustomUser.objects.create_user(
            phone_number1='+201000000001',
            password='testpass123',
            first_name='Supervisor',
            last_name='Test',
            email='supervisor@test.com',
            dob='1990-01-01',
            gender='male'
        )

        cls.instructor_user = CustomUser.objects.create_user(
            phone_number1='+201000000002',
            password='testpass123',
            first_name='Instructor',
            last_name='Test',
            email='instructor@test.com',
            dob='1991-01-01',
            gender='male'
        )

        # Create instructors
        cls.supervisor = Instructor.objects.create(
            user=cls.supervisor_user,
            monthly_salary=6000.00,
            type='supervisor'
        )

        cls.instructor = Instructor.objects.create(
            user=cls.instructor_user,
            monthly_salary=5000.00,
            type='normal'
        )

        # Create a season
        cls.season = Season.objects.create(
            name='Test Season',
            season_type='school',
            start_date=timezone.localdate() - timedelta(days=30),
            end_date=timezone.localdate() + timedelta(days=60),
            is_active=True
        )


class GenerateInstructorAttendanceWeeklyTest(CronJobBaseTestCase):
    """Tests for the generate_instructor_attendance_weekly cron job"""

    def setUp(self):
        """Set up for each test"""
        InstructorAttendance.objects.all().delete()
        AttendanceCronLog.objects.all().delete()
        SupervisorSchedule.objects.all().delete()

    def test_generates_attendance_for_supervisor_with_schedule(self):
        """Test that attendance is generated for supervisors with schedules"""
        today = timezone.localdate()

        # Create a schedule for today's weekday
        schedule = SupervisorSchedule.objects.create(
            instructor=self.supervisor,
            day_of_week=Weekday.of(today),
            start_time=time(8, 0),
            end_time=time(14, 0)
        )

        # Run the cron job
        generate_instructor_attendance_weekly()

        # Check that attendance was created
        attendance_count = InstructorAttendance.objects.filter(
            instructor=self.supervisor,
            attendance_type=AttendanceType.SUPERVISION,
            date__gte=today,
            date__lte=today + timedelta(days=7)
        ).count()

        # Should have at least 1 record (for today, and possibly next week's same day)
        self.assertGreaterEqual(attendance_count, 1)

        # Verify the attendance has correct type
        attendance = InstructorAttendance.objects.filter(
            instructor=self.supervisor
        ).first()
        self.assertEqual(attendance.attendance_type,
                         AttendanceType.SUPERVISION)
        self.assertEqual(attendance.schedule, schedule)

    def test_does_not_create_duplicate_attendance(self):
        """Test that running cron twice doesn't create duplicate records"""
        today = timezone.localdate()

        # Create a schedule
        SupervisorSchedule.objects.create(
            instructor=self.supervisor,
            day_of_week=Weekday.of(today),
            start_time=time(8, 0),
            end_time=time(14, 0)
        )

        # Run the cron job twice
        generate_instructor_attendance_weekly()
        initial_count = InstructorAttendance.objects.count()

        generate_instructor_attendance_weekly()
        final_count = InstructorAttendance.objects.count()

        # Count should remain the same
        self.assertEqual(initial_count, final_count)

    def test_cron_log_is_created(self):
        """Test that a cron log entry is created"""
        generate_instructor_attendance_weekly()

        log = AttendanceCronLog.objects.filter(
            job_name='generate_attendance_weekly'
        ).first()

        self.assertIsNotNone(log)
        self.assertIn('Created', log.details)
        self.assertIn('attendance records', log.details)

    def test_no_attendance_without_active_season(self):
        """Test that no attendance is created without active season"""
        # Deactivate the season
        self.season.is_active = False
        self.season.save()

        SupervisorSchedule.objects.create(
            instructor=self.supervisor,
            day_of_week=Weekday.of(timezone.localdate()),
            start_time=time(8, 0),
            end_time=time(14, 0)
        )

        generate_instructor_attendance_weekly()

        # Should have 0 records
        self.assertEqual(InstructorAttendance.objects.count(), 0)

        # Reactivate for other tests
        self.season.is_active = True
        self.season.save()


class MarkAbsentDailyTest(CronJobBaseTestCase):
    """Tests for the mark_absent_daily cron job"""

    def setUp(self):
        """Set up for each test"""
        InstructorAttendance.objects.all().delete()
        AttendanceCronLog.objects.all().delete()

    def test_marks_pending_as_absent(self):
        """Test that pending attendance is marked as absent"""
        today = timezone.localdate()

        # Create a pending attendance record
        attendance = InstructorAttendance.objects.create(
            instructor=self.instructor,
            date=today,
            status=AttendanceStatus.PENDING,
            season=self.season
        )

        # Run the cron job
        mark_absent_daily()

        # Refresh from database
        attendance.refresh_from_db()

        # Status should now be absent
        self.assertEqual(attendance.status, AttendanceStatus.ABSENT)
        # Rating should be null for absent
        self.assertIsNone(attendance.rating)

    def test_marks_not_started_as_absent(self):
        """Test that not_started attendance is marked as absent"""
        today = timezone.localdate()

        # Create a not_started attendance record
        attendance = InstructorAttendance.objects.create(
            instructor=self.instructor,
            date=today,
            status=AttendanceStatus.NOT_STARTED,
            season=self.season
        )

        # Run the cron job
        mark_absent_daily()

        # Refresh from database
        attendance.refresh_from_db()

        # Status should now be absent
        self.assertEqual(attendance.status, AttendanceStatus.ABSENT)

    def test_does_not_change_present_status(self):
        """Test that present attendance is not changed"""
        today = timezone.localdate()

        # Create a present attendance record
        attendance = InstructorAttendance.objects.create(
            instructor=self.instructor,
            date=today,
            status=AttendanceStatus.PRESENT,
            season=self.season
        )

        # Run the cron job
        mark_absent_daily()

        # Refresh from database
        attendance.refresh_from_db()

        # Status should still be present
        self.assertEqual(attendance.status, AttendanceStatus.PRESENT)

    def test_does_not_change_late_status(self):
        """Test that late attendance is not changed"""
        today = timezone.localdate()

        # Create a late attendance record
        attendance = InstructorAttendance.objects.create(
            instructor=self.instructor,
            date=today,
            status=AttendanceStatus.LATE,
            season=self.season
        )

        # Run the cron job
        mark_absent_daily()

        # Refresh from database
        attendance.refresh_from_db()

        # Status should still be late
        self.assertEqual(attendance.status, AttendanceStatus.LATE)

    def test_cron_log_is_created(self):
        """Test that a cron log entry is created"""
        mark_absent_daily()

        log = AttendanceCronLog.objects.filter(
            job_name='mark_absent_daily'
        ).first()

        self.assertIsNotNone(log)
        self.assertIn('Marked', log.details)
        self.assertIn('ABSENT', log.details)

    def test_cron_log_shows_correct_count(self):
        """Test that the cron log shows the correct count of updated records"""
        today = timezone.localdate()

        # Create multiple pending/not_started records
        InstructorAttendance.objects.create(
            instructor=self.supervisor,
            date=today,
            status=AttendanceStatus.PENDING,
            season=self.season
        )
        InstructorAttendance.objects.create(
            instructor=self.instructor,
            date=today,
            status=AttendanceStatus.NOT_STARTED,
            season=self.season
        )

        # Run the cron job
        mark_absent_daily()

        log = AttendanceCronLog.objects.filter(
            job_name='mark_absent_daily'
        ).first()

        # Should mention 2 instructors marked absent
        self.assertIn('2', log.details)


class MarkAbsentForYesterdayTest(CronJobBaseTestCase):
    """Tests for the mark_absent_for_yesterday fallback cron job"""

    def setUp(self):
        """Set up for each test"""
        InstructorAttendance.objects.all().delete()
        AttendanceCronLog.objects.all().delete()

    def test_marks_yesterday_pending_as_absent(self):
        """Test that yesterday's pending attendance is marked as absent"""
        yesterday = timezone.localdate() - timedelta(days=1)

        # Create a pending attendance record for yesterday
        attendance = InstructorAttendance.objects.create(
            instructor=self.instructor,
            date=yesterday,
            status=AttendanceStatus.PENDING,
            season=self.season
        )

        # Run the cron job
        mark_absent_for_yesterday()

        # Refresh from database
        attendance.refresh_from_db()

        # Status should now be absent
        self.assertEqual(attendance.status, AttendanceStatus.ABSENT)

    def test_does_not_affect_today(self):
        """Test that today's records are not affected"""
        today = timezone.localdate()

        # Create a pending attendance record for today
        attendance = InstructorAttendance.objects.create(
            instructor=self.instructor,
            date=today,
            status=AttendanceStatus.PENDING,
            season=self.season
        )

        # Run the cron job
        mark_absent_for_yesterday()

        # Refresh from database
        attendance.refresh_from_db()

        # Status should still be pending
        self.assertEqual(attendance.status, AttendanceStatus.PENDING)

    def test_no_log_if_no_updates(self):
        """Test that no log is created if no updates were made"""
        # No records to update
        mark_absent_for_yesterday()

        log = AttendanceCronLog.objects.filter(
            job_name='mark_absent_for_yesterday'
        ).first()

        # Should not create log if count is 0
        self.assertIsNone(log)


class MarkLecturesWithoutAttendanceAsCancelledTest(CronJobBaseTestCase):
    """Tests for the mark_lectures_without_attendance_as_cancelled cron job"""

    def setUp(self):
        """Set up for each test"""
        Lecture.objects.all().delete()
        AttendanceCronLog.objects.all().delete()
        Course.objects.all().delete()
        # Create a test tag
        self.tag = Tag.objects.create(name='Test Tag')
        # Create a test course
        self.course = Course.objects.create(
            name='Test Course',
            price=100.00,
            capacity=30,
            start_date=timezone.localdate() - timedelta(days=30),
            season=self.season,
            instructor=self.instructor
        )
        self.course.tags.add(self.tag)

    def test_marks_yesterday_lecture_without_attendance_as_cancelled(self):
        """Test that yesterday's lecture without attendance is marked cancelled"""
        yesterday = timezone.localdate() - timedelta(days=1)

        lecture = Lecture.objects.create(
            course=self.course,
            day=yesterday,
            lecture_number=1,
            status=LectureStatus.SCHEDULED,
            attendance_taken=False,
            instructor=self.instructor
        )

        # Run the cron job
        cancelled_count = mark_lectures_without_attendance_as_cancelled()

        # Refresh from database
        lecture.refresh_from_db()

        # Status should now be cancelled
        self.assertEqual(lecture.status, LectureStatus.CANCELLED)
        self.assertEqual(cancelled_count, 1)

    def test_does_not_cancel_today_lecture(self):
        """Test that today's lecture is not cancelled (might still be ongoing)"""
        today = timezone.localdate()

        lecture = Lecture.objects.create(
            course=self.course,
            day=today,
            lecture_number=1,
            status=LectureStatus.SCHEDULED,
            attendance_taken=False,
            instructor=self.instructor
        )

        # Run the cron job
        cancelled_count = mark_lectures_without_attendance_as_cancelled()

        # Refresh from database
        lecture.refresh_from_db()

        # Status should still be scheduled
        self.assertEqual(lecture.status, LectureStatus.SCHEDULED)
        self.assertEqual(cancelled_count, 0)

    def test_does_not_cancel_lecture_with_attendance_taken(self):
        """Test that lecture with attendance taken is not cancelled"""
        yesterday = timezone.localdate() - timedelta(days=1)

        lecture = Lecture.objects.create(
            course=self.course,
            day=yesterday,
            lecture_number=1,
            status=LectureStatus.SCHEDULED,
            attendance_taken=True,  # Attendance was taken
            instructor=self.instructor
        )

        # Run the cron job
        cancelled_count = mark_lectures_without_attendance_as_cancelled()

        # Refresh from database
        lecture.refresh_from_db()

        # Status should still be scheduled
        self.assertEqual(lecture.status, LectureStatus.SCHEDULED)
        self.assertEqual(cancelled_count, 0)

    def test_does_not_cancel_already_cancelled_lecture(self):
        """Test that already cancelled lecture is not changed"""
        yesterday = timezone.localdate() - timedelta(days=1)

        lecture = Lecture.objects.create(
            course=self.course,
            day=yesterday,
            lecture_number=1,
            status=LectureStatus.CANCELLED,  # Already cancelled
            attendance_taken=False,
            instructor=self.instructor
        )

        # Run the cron job
        cancelled_count = mark_lectures_without_attendance_as_cancelled()

        # Refresh from database
        lecture.refresh_from_db()

        # Status should still be cancelled
        self.assertEqual(lecture.status, LectureStatus.CANCELLED)
        self.assertEqual(cancelled_count, 0)

    def test_does_not_cancel_completed_lecture(self):
        """Test that completed lecture is not changed"""
        yesterday = timezone.localdate() - timedelta(days=1)

        lecture = Lecture.objects.create(
            course=self.course,
            day=yesterday,
            lecture_number=1,
            status=LectureStatus.COMPLETED,
            attendance_taken=False,  # Even without attendance marked
            instructor=self.instructor
        )

        # Run the cron job
        cancelled_count = mark_lectures_without_attendance_as_cancelled()

        # Refresh from database
        lecture.refresh_from_db()

        # Status should still be completed
        self.assertEqual(lecture.status, LectureStatus.COMPLETED)
        self.assertEqual(cancelled_count, 0)

    def test_cancels_multiple_lectures(self):
        """Test that multiple lectures from past days are cancelled"""
        yesterday = timezone.localdate() - timedelta(days=1)
        two_days_ago = timezone.localdate() - timedelta(days=2)

        lecture1 = Lecture.objects.create(
            course=self.course,
            day=yesterday,
            lecture_number=1,
            status=LectureStatus.SCHEDULED,
            attendance_taken=False,
            instructor=self.instructor
        )

        lecture2 = Lecture.objects.create(
            course=self.course,
            day=two_days_ago,
            lecture_number=2,
            status=LectureStatus.SCHEDULED,
            attendance_taken=False,
            instructor=self.instructor
        )

        # Run the cron job
        cancelled_count = mark_lectures_without_attendance_as_cancelled()

        # Refresh from database
        lecture1.refresh_from_db()
        lecture2.refresh_from_db()

        # Both should be cancelled
        self.assertEqual(lecture1.status, LectureStatus.CANCELLED)
        self.assertEqual(lecture2.status, LectureStatus.CANCELLED)
        self.assertEqual(cancelled_count, 2)

    def test_cron_log_created_when_lectures_cancelled(self):
        """Test that cron log is created when lectures are cancelled"""
        yesterday = timezone.localdate() - timedelta(days=1)

        Lecture.objects.create(
            course=self.course,
            day=yesterday,
            lecture_number=1,
            status=LectureStatus.SCHEDULED,
            attendance_taken=False,
            instructor=self.instructor
        )

        # Run the cron job
        mark_lectures_without_attendance_as_cancelled()

        log = AttendanceCronLog.objects.filter(
            job_name='mark_lectures_without_attendance_as_cancelled'
        ).first()

        self.assertIsNotNone(log)
        self.assertIn('1', log.details)
        self.assertIn('CANCELLED', log.details)

    def test_no_cron_log_when_nothing_cancelled(self):
        """Test that no cron log is created when nothing to cancel"""
        # No lectures to cancel
        mark_lectures_without_attendance_as_cancelled()

        log = AttendanceCronLog.objects.filter(
            job_name='mark_lectures_without_attendance_as_cancelled'
        ).first()

        self.assertIsNone(log)

    def test_mixed_lectures_only_cancels_eligible(self):
        """Test mixed scenario where only some lectures are cancelled"""
        yesterday = timezone.localdate() - timedelta(days=1)
        today = timezone.localdate()

        # Should be cancelled (scheduled, no attendance, past)
        lecture1 = Lecture.objects.create(
            course=self.course,
            day=yesterday,
            lecture_number=1,
            status=LectureStatus.SCHEDULED,
            attendance_taken=False,
            instructor=self.instructor
        )

        # Should NOT be cancelled (today)
        lecture2 = Lecture.objects.create(
            course=self.course,
            day=today,
            lecture_number=2,
            status=LectureStatus.SCHEDULED,
            attendance_taken=False,
            instructor=self.instructor
        )

        # Should NOT be cancelled (attendance taken)
        lecture3 = Lecture.objects.create(
            course=self.course,
            day=yesterday,
            lecture_number=3,
            status=LectureStatus.SCHEDULED,
            attendance_taken=True,
            instructor=self.instructor
        )

        # Should NOT be cancelled (already completed)
        lecture4 = Lecture.objects.create(
            course=self.course,
            day=yesterday,
            lecture_number=4,
            status=LectureStatus.COMPLETED,
            attendance_taken=False,
            instructor=self.instructor
        )

        # Run the cron job
        cancelled_count = mark_lectures_without_attendance_as_cancelled()

        # Refresh from database
        lecture1.refresh_from_db()
        lecture2.refresh_from_db()
        lecture3.refresh_from_db()
        lecture4.refresh_from_db()

        # Only lecture1 should be cancelled
        self.assertEqual(lecture1.status, LectureStatus.CANCELLED)
        self.assertEqual(lecture2.status, LectureStatus.SCHEDULED)
        self.assertEqual(lecture3.status, LectureStatus.SCHEDULED)
        self.assertEqual(lecture4.status, LectureStatus.COMPLETED)
        self.assertEqual(cancelled_count, 1)


class MarkLecturesWithoutAttendanceFallbackTest(CronJobBaseTestCase):
    """Tests for the mark_lectures_without_attendance_as_cancelled_fallback cron job"""

    def setUp(self):
        """Set up for each test"""
        Lecture.objects.all().delete()
        AttendanceCronLog.objects.all().delete()
        Course.objects.all().delete()
        # Create a test tag
        self.tag = Tag.objects.create(name='Test Tag Fallback')
        # Create a test course
        self.course = Course.objects.create(
            name='Test Course Fallback',
            price=100.00,
            capacity=30,
            start_date=timezone.localdate() - timedelta(days=30),
            season=self.season,
            instructor=self.instructor
        )
        self.course.tags.add(self.tag)

    def test_cancels_lectures_from_two_days_ago(self):
        """Test that fallback cancels lectures from 2+ days ago"""
        two_days_ago = timezone.localdate() - timedelta(days=2)

        lecture = Lecture.objects.create(
            course=self.course,
            day=two_days_ago,
            lecture_number=1,
            status=LectureStatus.SCHEDULED,
            attendance_taken=False,
            instructor=self.instructor
        )

        # Run the fallback cron job
        cancelled_count = mark_lectures_without_attendance_as_cancelled_fallback()

        # Refresh from database
        lecture.refresh_from_db()

        # Status should be cancelled
        self.assertEqual(lecture.status, LectureStatus.CANCELLED)
        self.assertEqual(cancelled_count, 1)

    def test_does_not_cancel_yesterday_lecture(self):
        """Test that fallback does not cancel yesterday's lecture (primary job handles it)"""
        yesterday = timezone.localdate() - timedelta(days=1)

        lecture = Lecture.objects.create(
            course=self.course,
            day=yesterday,
            lecture_number=1,
            status=LectureStatus.SCHEDULED,
            attendance_taken=False,
            instructor=self.instructor
        )

        # Run the fallback cron job
        cancelled_count = mark_lectures_without_attendance_as_cancelled_fallback()

        # Refresh from database
        lecture.refresh_from_db()

        # Status should still be scheduled (fallback doesn't handle yesterday)
        self.assertEqual(lecture.status, LectureStatus.SCHEDULED)
        self.assertEqual(cancelled_count, 0)

    def test_cancels_very_old_lectures(self):
        """Test that fallback cancels very old lectures that were missed"""
        ten_days_ago = timezone.localdate() - timedelta(days=10)

        lecture = Lecture.objects.create(
            course=self.course,
            day=ten_days_ago,
            lecture_number=1,
            status=LectureStatus.SCHEDULED,
            attendance_taken=False,
            instructor=self.instructor
        )

        # Run the fallback cron job
        cancelled_count = mark_lectures_without_attendance_as_cancelled_fallback()

        # Refresh from database
        lecture.refresh_from_db()

        # Status should be cancelled
        self.assertEqual(lecture.status, LectureStatus.CANCELLED)
        self.assertEqual(cancelled_count, 1)

    def test_fallback_creates_log_on_cancellation(self):
        """Test that fallback job creates log entry"""
        two_days_ago = timezone.localdate() - timedelta(days=2)

        Lecture.objects.create(
            course=self.course,
            day=two_days_ago,
            lecture_number=1,
            status=LectureStatus.SCHEDULED,
            attendance_taken=False,
            instructor=self.instructor
        )

        # Run the fallback cron job
        mark_lectures_without_attendance_as_cancelled_fallback()

        log = AttendanceCronLog.objects.filter(
            job_name='mark_lectures_without_attendance_as_cancelled_fallback'
        ).first()

        self.assertIsNotNone(log)
        self.assertIn('1', log.details)
        self.assertIn('fallback', log.details)

    def test_fallback_no_log_when_nothing_cancelled(self):
        """Test that fallback creates no log when nothing to cancel"""
        mark_lectures_without_attendance_as_cancelled_fallback()

        log = AttendanceCronLog.objects.filter(
            job_name='mark_lectures_without_attendance_as_cancelled_fallback'
        ).first()

        self.assertIsNone(log)

    def test_fallback_does_not_affect_lectures_with_attendance(self):
        """Test fallback doesn't cancel lectures where attendance was taken"""
        three_days_ago = timezone.localdate() - timedelta(days=3)

        lecture = Lecture.objects.create(
            course=self.course,
            day=three_days_ago,
            lecture_number=1,
            status=LectureStatus.SCHEDULED,
            attendance_taken=True,  # Attendance was taken
            instructor=self.instructor
        )

        # Run the fallback cron job
        cancelled_count = mark_lectures_without_attendance_as_cancelled_fallback()

        # Refresh from database
        lecture.refresh_from_db()

        # Status should still be scheduled
        self.assertEqual(lecture.status, LectureStatus.SCHEDULED)
        self.assertEqual(cancelled_count, 0)
