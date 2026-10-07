#!/usr/bin/env python3
"""
Tests for Parents app views and models

These tests cover:
- Child CRUD operations
- Parent permissions
- Primary and secondary parent relationships
- Child listing with both primary and extra children
"""
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status

from users.models import CustomUser
from parents.models import Parent, Child, ChildParents


class ParentChildBaseTestCase(TestCase):
    """Base test case with common setup for parent/child tests"""

    @classmethod
    def setUpTestData(cls):
        """Set up test data for all tests"""
        # Create primary parent user
        cls.parent_user = CustomUser.objects.create_user(
            phone_number1='+201000000001',
            password='parentpass123',
            first_name='Primary',
            last_name='Parent',
            email='parent@test.com',
            dob='1980-01-01',
            gender='male',
            role='parent'
        )
        cls.parent = cls.parent_user.parent_profile

        # Create secondary parent user
        cls.secondary_parent_user = CustomUser.objects.create_user(
            phone_number1='+201000000002',
            password='parent2pass123',
            first_name='Secondary',
            last_name='Parent',
            email='parent2@test.com',
            dob='1982-02-02',
            gender='female',
            role='parent'
        )
        cls.secondary_parent = cls.secondary_parent_user.parent_profile

        # Create another parent (not linked to any children)
        cls.other_parent_user = CustomUser.objects.create_user(
            phone_number1='+201000000003',
            password='parent3pass123',
            first_name='Other',
            last_name='Parent',
            email='parent3@test.com',
            dob='1985-03-03',
            gender='male',
            role='parent'
        )
        cls.other_parent = cls.other_parent_user.parent_profile

        # Create admin user
        cls.admin_user = CustomUser.objects.create_user(
            phone_number1='+201000000010',
            password='adminpass123',
            first_name='Admin',
            last_name='User',
            email='admin@test.com',
            dob='1985-01-01',
            gender='male',
            is_staff=True,
            is_superuser=True
        )

    def setUp(self):
        """Set up for each test"""
        self.client = APIClient()


class ChildListViewTest(ParentChildBaseTestCase):
    """Tests for ChildListView - listing children with primary and secondary relationships"""

    def test_list_primary_children_only(self):
        """Test listing when parent only has primary children"""
        # Create primary children
        child1 = Child.objects.create(
            primary_parent=self.parent,
            first_name='Ahmed',
            last_name='Mohamed',
            dob='2010-05-15',
            gender='boy'
        )
        child2 = Child.objects.create(
            primary_parent=self.parent,
            first_name='Fatima',
            last_name='Mohamed',
            dob='2012-08-20',
            gender='girl'
        )

        self.client.force_authenticate(user=self.parent_user)
        response = self.client.get('/api/parents/children/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Handle paginated response
        results = response.data.get('results', response.data)
        self.assertEqual(len(results), 2)
        codes = [child['unique_code'] for child in results]
        self.assertIn(child1.unique_code, codes)
        self.assertIn(child2.unique_code, codes)

    def test_list_includes_secondary_children(self):
        """Test that list includes children where parent is secondary parent"""
        # Create primary child (where other parent is primary)
        primary_child = Child.objects.create(
            primary_parent=self.other_parent,
            first_name='Sara',
            last_name='Ahmed',
            dob='2011-03-10',
            gender='girl'
        )

        # Link current parent as secondary parent
        ChildParents.objects.create(
            child=primary_child,
            parent=self.parent
        )

        # Create a child where current parent IS the primary parent
        secondary_child = Child.objects.create(
            primary_parent=self.parent,
            first_name='Ali',
            last_name='Mohamed',
            dob='2013-07-25',
            gender='boy'
        )

        self.client.force_authenticate(user=self.parent_user)
        response = self.client.get('/api/parents/children/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Handle paginated response
        results = response.data.get('results', response.data)
        self.assertEqual(len(results), 2)

        codes = [child['unique_code'] for child in results]
        self.assertIn(primary_child.unique_code, codes)
        self.assertIn(secondary_child.unique_code, codes)

    def test_list_only_secondary_children(self):
        """Test listing when parent only has secondary children (not primary)"""
        # Create children where other_parent is primary
        child1 = Child.objects.create(
            primary_parent=self.other_parent,
            first_name='Omar',
            last_name='Hassan',
            dob='2010-01-15',
            gender='boy'
        )
        child2 = Child.objects.create(
            primary_parent=self.other_parent,
            first_name='Layla',
            last_name='Hassan',
            dob='2012-06-20',
            gender='girl'
        )

        # Link current parent as secondary to both
        ChildParents.objects.create(child=child1, parent=self.parent)
        ChildParents.objects.create(child=child2, parent=self.parent)

        self.client.force_authenticate(user=self.parent_user)
        response = self.client.get('/api/parents/children/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Handle paginated response
        results = response.data.get('results', response.data)
        self.assertEqual(len(results), 2)

        codes = [child['unique_code'] for child in results]
        self.assertIn(child1.unique_code, codes)
        self.assertIn(child2.unique_code, codes)

    def test_list_empty_for_unlinked_parent(self):
        """Test that parent with no children gets empty list"""
        # Create child but don't link to other_parent
        Child.objects.create(
            primary_parent=self.parent,
            first_name='Test',
            last_name='Child',
            dob='2010-01-01',
            gender='boy'
        )

        self.client.force_authenticate(user=self.other_parent_user)
        response = self.client.get('/api/parents/children/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Handle paginated response
        results = response.data.get('results', response.data)
        self.assertEqual(len(results), 0)

    def test_list_no_duplicates_with_distinct(self):
        """Test that distinct() prevents duplicates if somehow parent is linked multiple ways"""
        child = Child.objects.create(
            primary_parent=self.parent,
            first_name='Test',
            last_name='Child',
            dob='2010-01-01',
            gender='boy'
        )

        self.client.force_authenticate(user=self.parent_user)
        response = self.client.get('/api/parents/children/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Handle paginated response
        results = response.data.get('results', response.data)
        self.assertEqual(len(results), 1)

    def test_list_requires_authentication(self):
        """Test that listing children requires authentication"""
        response = self.client.get('/api/parents/children/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_requires_parent_role(self):
        """Test that only parents can list children"""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get('/api/parents/children/')
        # Admin doesn't have parent_profile, so should be forbidden
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_mixed_primary_and_secondary(self):
        """Test comprehensive scenario with mixed relationships"""
        # Child 1: Current parent is primary
        child1 = Child.objects.create(
            primary_parent=self.parent,
            first_name='Child',
            last_name='One',
            dob='2010-01-01',
            gender='boy'
        )

        # Child 2: Current parent is secondary
        child2 = Child.objects.create(
            primary_parent=self.other_parent,
            first_name='Child',
            last_name='Two',
            dob='2011-02-02',
            gender='girl'
        )
        ChildParents.objects.create(child=child2, parent=self.parent)

        # Child 3: Current parent is primary, has secondary parent too
        child3 = Child.objects.create(
            primary_parent=self.parent,
            first_name='Child',
            last_name='Three',
            dob='2012-03-03',
            gender='boy'
        )
        ChildParents.objects.create(child=child3, parent=self.secondary_parent)

        # Child 4: Neither primary nor secondary for current parent (should not appear)
        child4 = Child.objects.create(
            primary_parent=self.other_parent,
            first_name='Child',
            last_name='Four',
            dob='2013-04-04',
            gender='girl'
        )
        ChildParents.objects.create(child=child4, parent=self.secondary_parent)

        self.client.force_authenticate(user=self.parent_user)
        response = self.client.get('/api/parents/children/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Handle paginated response
        results = response.data.get('results', response.data)
        self.assertEqual(len(results), 3)  # Only child1, child2, child3

        codes = [child['unique_code'] for child in results]
        self.assertIn(child1.unique_code, codes)
        self.assertIn(child2.unique_code, codes)
        self.assertIn(child3.unique_code, codes)
        self.assertNotIn(child4.unique_code, codes)


class ChildCreateViewTest(ParentChildBaseTestCase):
    """Tests for creating children"""

    def test_create_child_success(self):
        """Test successful child creation"""
        self.client.force_authenticate(user=self.parent_user)
        response = self.client.post(
            '/api/parents/children/create/',
            {
                'first_name': 'Ahmed',
                'last_name': 'Mohamed',
                'dob': '2010-05-15',
                'gender': 'boy'
            },
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['first_name'], 'Ahmed')
        self.assertIsNotNone(response.data['unique_code'])

        # Verify child was created with correct primary parent
        child = Child.objects.get(id=response.data['id'])
        self.assertEqual(child.primary_parent, self.parent)

    def test_create_child_requires_authentication(self):
        """Test that creating child requires authentication"""
        response = self.client.post(
            '/api/parents/children/create/',
            {
                'first_name': 'Test',
                'last_name': 'Child',
                'dob': '2010-01-01',
                'gender': 'boy'
            },
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_child_requires_parent_role(self):
        """Test that only parents can create children"""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(
            '/api/parents/children/create/',
            {
                'first_name': 'Test',
                'last_name': 'Child',
                'dob': '2010-01-01',
                'gender': 'boy'
            },
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class ChildDetailViewTest(ParentChildBaseTestCase):
    """Tests for viewing child details"""

    def test_view_own_primary_child(self):
        """Test viewing child where user is primary parent"""
        child = Child.objects.create(
            primary_parent=self.parent,
            first_name='Ahmed',
            last_name='Mohamed',
            dob='2010-05-15',
            gender='boy'
        )

        self.client.force_authenticate(user=self.parent_user)
        response = self.client.get(f'/api/parents/children/{child.id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], str(child.id))

    def test_cannot_view_other_parents_child(self):
        """Test that parent cannot view another parent's child"""
        child = Child.objects.create(
            primary_parent=self.other_parent,
            first_name='Ahmed',
            last_name='Hassan',
            dob='2010-05-15',
            gender='boy'
        )

        self.client.force_authenticate(user=self.parent_user)
        response = self.client.get(f'/api/parents/children/{child.id}/')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class ChildUpdateViewTest(ParentChildBaseTestCase):
    """Tests for updating child information"""

    def test_update_own_child(self):
        """Test updating child as primary parent"""
        child = Child.objects.create(
            primary_parent=self.parent,
            first_name='Ahmed',
            last_name='Mohamed',
            dob='2010-05-15',
            gender='boy'
        )

        self.client.force_authenticate(user=self.parent_user)
        response = self.client.patch(
            f'/api/parents/children/{child.id}/update/',
            {'first_name': 'Mohammed'},
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], 'Mohammed')

        child.refresh_from_db()
        self.assertEqual(child.first_name, 'Mohammed')

    def test_cannot_update_other_parents_child(self):
        """Test that parent cannot update another parent's child"""
        child = Child.objects.create(
            primary_parent=self.other_parent,
            first_name='Ahmed',
            last_name='Hassan',
            dob='2010-05-15',
            gender='boy'
        )

        self.client.force_authenticate(user=self.parent_user)
        response = self.client.patch(
            f'/api/parents/children/{child.id}/update/',
            {'first_name': 'NewName'},
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class ChildDeleteViewTest(ParentChildBaseTestCase):
    """Parents may not delete their children (the endpoint was removed)."""

    def test_parent_cannot_delete_own_child(self):
        child = Child.objects.create(
            primary_parent=self.parent,
            first_name='Ahmed',
            last_name='Mohamed',
            dob='2010-05-15',
            gender='boy'
        )

        self.client.force_authenticate(user=self.parent_user)
        response = self.client.delete(
            f'/api/parents/children/{child.id}/delete/')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Child.objects.filter(id=child.id).exists())

    def test_child_detail_does_not_accept_delete(self):
        child = Child.objects.create(
            primary_parent=self.parent,
            first_name='Ahmed',
            last_name='Mohamed',
            dob='2010-05-15',
            gender='boy'
        )

        self.client.force_authenticate(user=self.parent_user)
        response = self.client.delete(f'/api/parents/children/{child.id}/')

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertTrue(Child.objects.filter(id=child.id).exists())
