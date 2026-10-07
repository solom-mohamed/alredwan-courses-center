"""GET /api/courses/ catalogue filters (state, availability, season_name) and ordering."""
from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from courses.models import Course, Season
from enrollments_payments.models import Enrollment, EnrollmentStatus
from users.models import CustomUser, Instructor
from users.models.student_instructor_rating import StudentCourseRating


class CourseListFilterTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        today = timezone.localdate()

        self.summer = Season.objects.create(
            name='Summer', season_type='summer_camp',
            start_date=today - timedelta(days=400), is_active=True)
        self.ramadan = Season.objects.create(
            name='Ramadan', season_type='ramadan',
            start_date=today - timedelta(days=400), is_active=True)

        instructor_user = CustomUser.objects.create_user(
            phone_number1='+201000000901', password='Password123!',
            first_name='Ins', last_name='Tructor', role='instructor',
            dob='1980-01-01', gender='male')
        self.instructor = Instructor.objects.create(
            user=instructor_user, monthly_salary=1000)

        def course(name, season, start, end, capacity=10):
            return Course.objects.create(
                name=name, description='', instructor=self.instructor,
                season=season, price=100, capacity=capacity,
                start_date=start, end_date=end, is_active=True)

        self.ongoing = course('Ongoing', self.summer,
                              today - timedelta(days=5), today + timedelta(days=5),
                              capacity=1)
        self.open_ended = course('Open ended', self.summer,
                                 today - timedelta(days=5), None)
        self.upcoming = course('Upcoming', self.ramadan,
                               today + timedelta(days=5), today + timedelta(days=30))
        self.ended = course('Ended', self.ramadan,
                            today - timedelta(days=30), today - timedelta(days=5))

        # Fill `ongoing` (capacity 1), and add a rating so the ratings join
        # would multiply the enrollment rows without distinct counting.
        self.students = []
        for i in range(2):
            user = CustomUser.objects.create_user(
                phone_number1=f'+20100000091{i}', password='Password123!',
                first_name='S', last_name=str(i), role='student',
                dob='2006-01-01', gender='male')
            self.students.append(user.student_profile)
        Enrollment.objects.create(
            course=self.ongoing, student=self.students[0],
            status=EnrollmentStatus.ACTIVE)
        StudentCourseRating.objects.create(
            student=self.students[0], course=self.ongoing, rating=9)
        StudentCourseRating.objects.create(
            student=self.students[1], course=self.ongoing, rating=7)

    def names(self, **params):
        response = self.client.get('/api/courses/', params)
        self.assertEqual(response.status_code, 200, response.content)
        return [c['name'] for c in response.data['results']]

    def test_state_filter(self):
        self.assertCountEqual(self.names(state='ongoing'), ['Ongoing', 'Open ended'])
        self.assertEqual(self.names(state='upcoming'), ['Upcoming'])
        self.assertEqual(self.names(state='ended'), ['Ended'])

    def test_availability_filter(self):
        self.assertEqual(self.names(availability='full'), ['Ongoing'])
        self.assertCountEqual(
            self.names(availability='open'), ['Open ended', 'Upcoming', 'Ended'])

    def test_enrolled_count_not_multiplied_by_ratings(self):
        response = self.client.get('/api/courses/', {'availability': 'full'})
        self.assertEqual(response.data['results'][0]['enrolled_count'], 1)

    def test_season_name_filter(self):
        self.assertCountEqual(self.names(season_name='Ramadan'), ['Upcoming', 'Ended'])

    def test_ordering_by_name_season_and_enrollments(self):
        self.assertEqual(
            self.names(ordering='name'),
            ['Ended', 'Ongoing', 'Open ended', 'Upcoming'])
        # Summer > Ramadan, so descending puts the two Summer courses first.
        self.assertCountEqual(self.names(ordering='-season__name')[:2],
                              ['Ongoing', 'Open ended'])
        self.assertEqual(self.names(ordering='-_enrolled_count')[0], 'Ongoing')

    def test_invalid_filter_value_is_rejected(self):
        response = self.client.get('/api/courses/', {'state': 'nope'})
        self.assertEqual(response.status_code, 400)
