#!/usr/bin/env python3
"""Tests for users API endpoints."""
from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status

from users.models import CustomUser, Instructor, LandingPageInstructor
from courses.models import Tag


class BaseAPITestCase(TestCase):
    """Base test case with common setup for all user API tests."""

    @classmethod
    def setUpTestData(cls):
        """Set up test data for all tests in this class."""
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

        # Create regular user
        cls.regular_user = CustomUser.objects.create_user(
            phone_number1='+201000000002',
            password='userpass123',
            first_name='Regular',
            last_name='User',
            email='user@test.com',
            dob='1990-01-01',
            gender='male'
        )

        # Create instructor users
        cls.instructor_user1 = CustomUser.objects.create_user(
            phone_number1='+201000000003',
            password='instructor123',
            first_name='أحمد',
            last_name='محمد',
            email='ahmed@test.com',
            dob='1980-01-01',
            gender='male'
        )

        cls.instructor_user2 = CustomUser.objects.create_user(
            phone_number1='+201000000004',
            password='instructor123',
            first_name='فاطمة',
            last_name='علي',
            email='fatima@test.com',
            dob='1985-05-15',
            gender='female'
        )

        cls.instructor_user3 = CustomUser.objects.create_user(
            phone_number1='+201000000005',
            password='instructor123',
            first_name='Ibrahim',
            last_name='Hassan',
            email='ibrahim@test.com',
            dob='1975-03-20',
            gender='male'
        )

        # Create instructors
        cls.instructor1 = Instructor.objects.create(
            user=cls.instructor_user1,
            monthly_salary=5000.00,
            type='normal',
            bio='معلم قرآن كريم ذو خبرة طويلة',
            joined_date=timezone.localdate() - timedelta(days=365)
        )

        cls.instructor2 = Instructor.objects.create(
            user=cls.instructor_user2,
            monthly_salary=6000.00,
            type='supervisor',
            bio='مشرفة تربوية متميزة',
            joined_date=timezone.localdate() - timedelta(days=180)
        )

        cls.instructor3 = Instructor.objects.create(
            user=cls.instructor_user3,
            monthly_salary=5500.00,
            type='normal',
            bio='Experienced Tajweed teacher',
            joined_date=timezone.localdate() - timedelta(days=730)
        )

        # Create tags
        cls.tag_quran = Tag.objects.create(name='قرآن')
        cls.tag_tajweed = Tag.objects.create(name='تجويد')

        # Assign tags to instructors
        cls.instructor1.tags.add(cls.tag_quran)
        cls.instructor3.tags.add(cls.tag_quran, cls.tag_tajweed)

        # Create landing page instructors
        cls.landing_instructor1 = LandingPageInstructor.objects.create(
            instructor=cls.instructor1,
            order=100
        )

        cls.landing_instructor2 = LandingPageInstructor.objects.create(
            instructor=cls.instructor2,
            order=90
        )

    def setUp(self):
        """Set up for each test."""
        self.client = APIClient()


class InstructorListAPITest(BaseAPITestCase):
    """Tests for instructor list endpoint."""

    def test_list_instructors_requires_auth(self):
        """Test that instructor list requires authentication."""
        response = self.client.get('/api/users/instructors/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_instructors_success(self):
        """Test successful listing of instructors."""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get('/api/users/instructors/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Handle paginated response
        results = response.data.get('results', response.data)
        self.assertEqual(len(results), 3)

    def test_filter_by_type(self):
        """Test filtering instructors by type."""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get('/api/users/instructors/?type=supervisor')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get('results', response.data)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['type'], 'supervisor')

    def test_filter_by_tag(self):
        """Test filtering instructors by tag."""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(
            f'/api/users/instructors/?tags={self.tag_quran.id}')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get('results', response.data)
        self.assertEqual(len(results), 2)

    def test_search_by_name(self):
        """Test searching instructors by name."""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get('/api/users/instructors/?search=أحمد')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get('results', response.data)
        self.assertEqual(len(results), 1)

    def test_search_by_bio(self):
        """Test searching instructors by bio."""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get('/api/users/instructors/?search=Tajweed')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get('results', response.data)
        self.assertEqual(len(results), 1)

    def test_ordering_by_joined_date(self):
        """Test ordering instructors by joined date."""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(
            '/api/users/instructors/?ordering=joined_date')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get('results', response.data)
        # Should be ordered from oldest to newest
        self.assertEqual(len(results), 3)


class InstructorDetailAPITest(BaseAPITestCase):
    """Tests for instructor detail endpoint."""

    def test_get_instructor_detail_public(self):
        """Test that instructor detail is publicly accessible."""
        response = self.client.get(
            f'/api/users/instructors/{self.instructor1.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.instructor1.id)

    def test_get_instructor_detail_includes_tags(self):
        """Test that instructor detail includes tags."""
        response = self.client.get(
            f'/api/users/instructors/{self.instructor3.id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('tags', response.data)
        self.assertEqual(len(response.data['tags']), 2)

    def test_get_nonexistent_instructor(self):
        """Test getting a non-existent instructor returns 404."""
        response = self.client.get('/api/users/instructors/99999/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class LandingPageInstructorAPITest(BaseAPITestCase):
    """Tests for landing page instructor endpoint."""

    def test_landing_page_instructors_public(self):
        """Test that landing page instructors is publicly accessible."""
        response = self.client.get('/api/users/landingpageinstructors/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_landing_page_instructors_ordered_by_order(self):
        """Test that landing page instructors are ordered by order field."""
        response = self.client.get('/api/users/landingpageinstructors/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get('results', response.data)
        self.assertEqual(len(results), 2)
        # Default ordering is -order (highest first)
        self.assertGreaterEqual(results[0]['order'], results[1]['order'])

    def test_landing_page_instructors_count(self):
        """Test that only featured instructors are returned."""
        response = self.client.get('/api/users/landingpageinstructors/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get('results', response.data)
        # Only 2 instructors are featured
        self.assertEqual(len(results), 2)


class InstructorRatingsAPITest(BaseAPITestCase):
    """Tests for instructor ratings endpoint."""

    def test_ratings_are_public(self):
        """Ratings are shown on the public instructor page, so visitors may read them."""
        response = self.client.get(
            f'/api/users/instructors/{self.instructor1.id}/ratings/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('statistics', response.data)

    def test_rating_submission_requires_auth(self):
        """Submitting a rating still requires authentication."""
        response = self.client.post(
            f'/api/users/instructors/{self.instructor1.id}/rate/',
            {'rating': 5, 'feedback': 'x'})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_ratings_success(self):
        """Test successful retrieval of instructor ratings."""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(
            f'/api/users/instructors/{self.instructor1.id}/ratings/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)


class CustomUserModelTest(TestCase):
    """Tests for CustomUser model."""

    def test_create_user_with_phone(self):
        """Test creating a user with phone number."""
        user = CustomUser.objects.create_user(
            phone_number1='+201111111111',
            password='testpass123',
            first_name='Test',
            last_name='User',
            dob='1990-01-01',
            gender='male'
        )
        self.assertEqual(user.phone_number1, '+201111111111')
        self.assertTrue(user.check_password('testpass123'))

    def test_user_get_full_name(self):
        """Test user's get_full_name method."""
        user = CustomUser.objects.create_user(
            phone_number1='+201111111112',
            password='testpass123',
            first_name='محمد',
            last_name='أحمد',
            dob='1990-01-01',
            gender='male'
        )
        self.assertEqual(user.get_full_name(), 'محمد أحمد')


class InstructorModelTest(TestCase):
    """Tests for Instructor model."""

    def test_create_instructor(self):
        """Test creating an instructor."""
        user = CustomUser.objects.create_user(
            phone_number1='+201222222222',
            password='testpass123',
            first_name='Test',
            last_name='Instructor',
            dob='1985-01-01',
            gender='male'
        )
        instructor = Instructor.objects.create(
            user=user,
            monthly_salary=5000.00,
            type='normal'
        )
        self.assertEqual(instructor.user, user)
        self.assertEqual(instructor.type, 'normal')

    def test_instructor_str(self):
        """Test instructor string representation."""
        user = CustomUser.objects.create_user(
            phone_number1='+201222222223',
            password='testpass123',
            first_name='أحمد',
            last_name='محمود',
            dob='1985-01-01',
            gender='male'
        )
        instructor = Instructor.objects.create(
            user=user,
            monthly_salary=5000.00,
            type='supervisor'
        )
        self.assertIn('أحمد', str(instructor))


class UserMeEndpointTest(TestCase):
    """Tests for the /auth/users/me/ endpoint with instructor_id field."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()

        # Create regular user (no instructor profile)
        self.regular_user = CustomUser.objects.create_user(
            phone_number1='+201033333001',
            password='testpass123',
            first_name='Regular',
            last_name='User',
            email='regular@test.com',
            dob='1990-01-01',
            gender='male'
        )

        # Create instructor user
        self.instructor_user = CustomUser.objects.create_user(
            phone_number1='+201033333002',
            password='testpass123',
            first_name='Instructor',
            last_name='User',
            email='instructor@test.com',
            dob='1985-05-15',
            gender='male'
        )
        self.instructor = Instructor.objects.create(
            user=self.instructor_user,
            monthly_salary=5000.00,
            type='normal',
            bio='Test instructor bio'
        )

    def test_user_me_requires_authentication(self):
        """Test that /auth/users/me/ requires authentication."""
        response = self.client.get('/auth/users/me/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_me_regular_user_has_null_instructor_id(self):
        """Test that regular users have instructor_id as null."""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get('/auth/users/me/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('instructor_id', response.data)
        self.assertIsNone(response.data['instructor_id'])

    def test_user_me_instructor_has_instructor_id(self):
        """Test that instructors have their instructor_id populated."""
        self.client.force_authenticate(user=self.instructor_user)
        response = self.client.get('/auth/users/me/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('instructor_id', response.data)
        self.assertEqual(response.data['instructor_id'], self.instructor.id)

    def test_user_me_response_contains_all_fields(self):
        """Test that /auth/users/me/ returns all expected fields."""
        self.client.force_authenticate(user=self.instructor_user)
        response = self.client.get('/auth/users/me/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        expected_fields = [
            'id', 'phone_number1', 'phone_number2', 'email',
            'first_name', 'last_name', 'dob', 'gender',
            'identity_number', 'identity_type', 'address', 'location',
            'role', 'is_verified', 'date_joined', 'instructor_id'
        ]

        for field in expected_fields:
            self.assertIn(field, response.data, f"Missing field: {field}")

    def test_user_me_instructor_id_matches_correct_instructor(self):
        """Test that instructor_id matches the correct instructor profile."""
        # Create another instructor to ensure correct matching
        other_user = CustomUser.objects.create_user(
            phone_number1='+201033333003',
            password='testpass123',
            first_name='Other',
            last_name='Instructor',
            dob='1988-03-20',
            gender='male'
        )
        other_instructor = Instructor.objects.create(
            user=other_user,
            monthly_salary=6000.00,
            type='supervisor'
        )

        # Test first instructor
        self.client.force_authenticate(user=self.instructor_user)
        response = self.client.get('/auth/users/me/')
        self.assertEqual(response.data['instructor_id'], self.instructor.id)

        # Test second instructor
        self.client.force_authenticate(user=other_user)
        response = self.client.get('/auth/users/me/')
        self.assertEqual(response.data['instructor_id'], other_instructor.id)

    def test_user_me_instructor_id_is_read_only(self):
        """Test that instructor_id cannot be modified via PATCH."""
        self.client.force_authenticate(user=self.regular_user)

        # Try to set instructor_id via PATCH (should be ignored)
        response = self.client.patch('/auth/users/me/', {
            'instructor_id': 999
        }, format='json')

        # Request should succeed but instructor_id should remain null
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.data['instructor_id'])


class NullEmailUniquenessTest(TestCase):
    """
    Tests for email uniqueness behavior with null and empty string values.

    email = models.EmailField(unique=True, null=True, blank=True)

    Expected behavior:
    - Multiple NULL emails: allowed (SQL NULL != NULL, so no unique violation)
    - Multiple empty string emails: FAILS (unique constraint violation)
    - The save() method does NOT convert '' to None for email (unlike identity_number)
    """

    BASE_USER = dict(password='testpass123', first_name='Test',
                     last_name='User', dob='1990-01-01', gender='male')

    def _make_user(self, phone, email):
        return CustomUser.objects.create_user(
            phone_number1=phone, email=email, **self.BASE_USER
        )

    # --- NULL email ---

    def test_two_users_with_null_email_both_succeed(self):
        """Multiple users with email=None should be allowed (NULL != NULL in SQL)."""
        user1 = self._make_user('+201500000001', None)
        user2 = self._make_user('+201500000002', None)
        self.assertIsNone(user1.email)
        self.assertIsNone(user2.email)

    def test_three_users_with_null_email_all_succeed(self):
        """Three users with email=None should all be saved without error."""
        users = [self._make_user(f'+20150000000{i}', None) for i in range(3, 6)]
        self.assertEqual(CustomUser.objects.filter(email__isnull=True).count(), 3)

    def test_null_email_via_api_registration_two_users(self):
        """Two users omitting email during API registration should both succeed."""
        client = APIClient()
        payload = {
            'phone_number1': '+201500000010',
            'password': 'StrongPass!1',
            're_password': 'StrongPass!1',
            'first_name': 'Ali',
            'last_name': 'Hassan',
            'dob': '2000-01-01',
            'gender': 'male',
            'role': 'student',
        }
        r1 = client.post('/auth/users/', {**payload})
        payload['phone_number1'] = '+201500000011'
        r2 = client.post('/auth/users/', {**payload})

        self.assertEqual(r1.status_code, status.HTTP_201_CREATED)
        self.assertEqual(r2.status_code, status.HTTP_201_CREATED)

    # --- Empty string email ---

    def test_first_user_empty_string_email_is_saved_as_null(self):
        """Empty string email IS converted to None (same as identity_number)."""
        user = self._make_user('+201500000020', '')
        user.refresh_from_db()
        self.assertIsNone(user.email)

    def test_second_user_with_empty_string_email_succeeds(self):
        """A second user with email='' now succeeds because '' is stored as NULL."""
        user1 = self._make_user('+201500000030', '')
        user2 = self._make_user('+201500000031', '')
        user1.refresh_from_db()
        user2.refresh_from_db()
        self.assertIsNone(user1.email)
        self.assertIsNone(user2.email)

    def test_empty_string_email_via_api_second_registration_succeeds(self):
        """
        Two API registrations with email='' should both succeed because
        '' is converted to NULL before saving.
        """
        client = APIClient()
        payload = {
            'phone_number1': '+201500000040',
            'password': 'StrongPass!1',
            're_password': 'StrongPass!1',
            'first_name': 'Ali',
            'last_name': 'Hassan',
            'dob': '2000-01-01',
            'gender': 'male',
            'role': 'student',
            'email': '',
        }
        r1 = client.post('/auth/users/', {**payload})
        payload['phone_number1'] = '+201500000041'
        r2 = client.post('/auth/users/', {**payload})

        self.assertEqual(r1.status_code, status.HTTP_201_CREATED)
        self.assertEqual(r2.status_code, status.HTTP_201_CREATED)

    # --- Direct DB insertion ---

    def test_direct_db_null_emails_allowed(self):
        """Direct DB creation of users with NULL email should not raise."""
        import uuid
        from django.db import connection
        now_val = timezone.now()
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO users_customuser
                    (id, phone_number1, password, first_name, last_name,
                     dob, gender, is_active, is_staff, is_superuser,
                     is_verified, date_joined, role, email)
                VALUES
                    (%s, '+201500000050', 'x', 'A', 'B',
                     '2000-01-01', 'male', true, false, false, false,
                     %s, 'student', NULL),
                    (%s, '+201500000051', 'x', 'C', 'D',
                     '2000-01-01', 'male', true, false, false, false,
                     %s, 'student', NULL)
                """,
                [str(uuid.uuid4()), now_val, str(uuid.uuid4()), now_val]
            )
        self.assertEqual(
            CustomUser.objects.filter(email__isnull=True).count(), 2
        )

    def test_direct_db_empty_string_email_duplicate_raises(self):
        """
        Direct SQL bypasses save(), so '' is NOT converted to None.
        Two rows with email='' still violate the unique constraint at DB level.
        Use the ORM (or normalise '' to None before inserting) to avoid this.
        """
        import uuid
        from django.db import IntegrityError, connection, transaction
        now_val = timezone.now()
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO users_customuser
                            (id, phone_number1, password, first_name, last_name,
                             dob, gender, is_active, is_staff, is_superuser,
                             is_verified, date_joined, role, email)
                        VALUES
                            (%s, '+201500000060', 'x', 'E', 'F',
                             '2000-01-01', 'male', true, false, false, false,
                             %s, 'student', ''),
                            (%s, '+201500000061', 'x', 'G', 'H',
                             '2000-01-01', 'male', true, false, false, false,
                             %s, 'student', '')
                        """,
                        [str(uuid.uuid4()), now_val, str(uuid.uuid4()), now_val]
                    )


class InstructorRatingsPaginationTests(TestCase):
    """Tests for InstructorRatingsView pagination envelopes and query parameters."""

    def setUp(self):
        self.client = APIClient()

        self.instructor_user = CustomUser.objects.create_user(
            phone_number1='+201099990001',
            password='Password123!',
            first_name='Kareem',
            last_name='Teacher',
            role='instructor',
            dob='1982-01-01',
            gender='male'
        )
        self.instructor = Instructor.objects.create(
            user=self.instructor_user,
            monthly_salary=2000
        )

        self.student_user = CustomUser.objects.create_user(
            phone_number1='+201099990002',
            password='Password123!',
            first_name='Yara',
            last_name='Student',
            role='student',
            dob='2006-01-01',
            gender='female'
        )

        self.parent_user = CustomUser.objects.create_user(
            phone_number1='+201099990003',
            password='Password123!',
            first_name='Sameh',
            last_name='Parent',
            role='parent',
            dob='1976-01-01',
            gender='male'
        )

        from datetime import date
        from courses.models import Season, Course
        self.season = Season.objects.create(
            name='Winter 2026',
            season_type='winter',
            start_date=date(2026, 1, 1),
            end_date=date(2026, 5, 30),
            is_active=True
        )
        self.course = Course.objects.create(
            name='Biology 101',
            description='Intro to Biology',
            instructor=self.instructor,
            season=self.season,
            price=300.00,
            capacity=20,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 5, 30),
            is_active=True
        )

        from users.models.student_instructor_rating import StudentInstructorRating, ParentInstructorRating
        StudentInstructorRating.objects.create(
            student=self.student_user.student_profile,
            instructor=self.instructor,
            course=self.course,
            rating=10,
            feedback='Great teacher!'
        )
        ParentInstructorRating.objects.create(
            parent=self.parent_user.parent_profile,
            instructor=self.instructor,
            course=self.course,
            rating=9,
            feedback='Very supportive.'
        )

    def test_instructor_ratings_pagination_envelope(self):
        self.client.force_authenticate(user=self.student_user)
        response = self.client.get(f'/api/users/instructors/{self.instructor.id}/ratings/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        self.assertEqual(data['statistics']['total_ratings'], 2)
        self.assertEqual(data['statistics']['average_rating'], 9.5)

        # Check paginated envelopes
        self.assertIn('student_ratings', data['ratings'])
        self.assertIn('parent_ratings', data['ratings'])

        student_ratings = data['ratings']['student_ratings']
        self.assertIn('results', student_ratings)
        self.assertEqual(student_ratings['count'], 1)
        self.assertEqual(len(student_ratings['results']), 1)
        self.assertEqual(student_ratings['results'][0]['rating'], 10)

        parent_ratings = data['ratings']['parent_ratings']
        self.assertIn('results', parent_ratings)
        self.assertEqual(parent_ratings['count'], 1)
        self.assertEqual(len(parent_ratings['results']), 1)
        self.assertEqual(parent_ratings['results'][0]['rating'], 9)


class InstructorRatingOnlineCourseTests(TestCase):
    """Rating an instructor through one of their online courses."""

    def setUp(self):
        from courses_online.models import OnlineCourse
        from enrollments_payments.models import Enrollment, EnrollmentStatus
        from parents.models import Child

        self.client = APIClient()
        instructor_user = CustomUser.objects.create_user(
            phone_number1='+201000000951', password='Password123!',
            first_name='Ins', last_name='Tructor', role='instructor',
            dob='1980-01-01', gender='male')
        self.instructor = Instructor.objects.create(
            user=instructor_user, monthly_salary=1000)
        self.online_course = OnlineCourse.objects.create(
            name='Tajweed Online', instructor=self.instructor, price=100)
        self.other_online_course = OnlineCourse.objects.create(
            name='Someone else', price=100)

        self.student_user = CustomUser.objects.create_user(
            phone_number1='+201000000952', password='Password123!',
            first_name='Stu', last_name='Dent', role='student',
            dob='2006-01-01', gender='male')
        Enrollment.objects.create(
            online_course=self.online_course,
            student=self.student_user.student_profile,
            status=EnrollmentStatus.ACTIVE)

        self.parent_user = CustomUser.objects.create_user(
            phone_number1='+201000000953', password='Password123!',
            first_name='Par', last_name='Ent', role='parent',
            dob='1976-01-01', gender='male')
        child = Child.objects.create(
            first_name='Kid', last_name='Ent',
            primary_parent=self.parent_user.parent_profile,
            dob='2014-01-01', gender='male')
        Enrollment.objects.create(
            online_course=self.online_course, child=child,
            status=EnrollmentStatus.ACTIVE)

        self.url = f'/api/users/instructors/{self.instructor.id}/rate/'

    def test_student_rates_through_online_course(self):
        from users.models.student_instructor_rating import StudentInstructorRating

        self.client.force_authenticate(user=self.student_user)
        response = self.client.post(self.url, {
            'online_course': str(self.online_course.id), 'rating': 8, 'feedback': 'good'})

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        rating = StudentInstructorRating.objects.get(instructor=self.instructor)
        self.assertEqual(rating.online_course, self.online_course)
        self.assertIsNone(rating.course)

        ratings = self.client.get(
            f'/api/users/instructors/{self.instructor.id}/ratings/').data
        self.assertEqual(
            ratings['ratings']['student_ratings']['results'][0]['course_name'],
            'Tajweed Online')

    def test_parent_rates_through_child_online_course(self):
        self.client.force_authenticate(user=self.parent_user)
        response = self.client.post(self.url, {
            'online_course': str(self.online_course.id), 'rating': 9})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)

    def test_online_course_of_another_instructor_is_rejected(self):
        self.client.force_authenticate(user=self.student_user)
        response = self.client.post(self.url, {
            'online_course': str(self.other_online_course.id), 'rating': 8})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_course_is_required(self):
        self.client.force_authenticate(user=self.student_user)
        response = self.client.post(self.url, {'rating': 8})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
