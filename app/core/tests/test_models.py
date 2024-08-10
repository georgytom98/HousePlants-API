"""
Tests for models.
"""
from unittest.mock import patch

from decimal import Decimal

from django.test import TestCase
from django.contrib.auth import get_user_model

from core import models


def create_user(email='user@example.com', password='testpass123'):
    """Create a return a new user."""
    return get_user_model().objects.create_user(email, password)


class ModelTests(TestCase):
    """Test models"""

    def test_create_user_with_email_successful(self):
        """Test creating a user with an email is successful"""
        email = 'test@example.com'
        password = 'testpass123'
        user = get_user_model().objects.create_user(
            email=email,
            password=password
        )
        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_new_user_email_normalize(self):
        """Test email is normalized for new users."""
        sample_emails = [
            ['test@EXAMPLE.com', 'test@example.com'],
            ['Test2@Example.com', 'Test2@example.com'],
            ['TEST3@EXAMPLE.com', 'TEST3@example.com'],
            ['test4@example.com', 'test4@example.com']
        ]
        for email, expected in sample_emails:
            user = get_user_model().objects.create_user(email, 'sample123')
            self.assertEqual(user.email, expected)

    def test_new_user_without_email_raise(self):
        """Test that createing a user without email raises ValueError"""
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user('', 'test123')

    def test_create_superuser(self):
        """Test creating a superuser."""
        user = get_user_model().objects.create_superuser(
            'test@example.com',
            'test123'
        )
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_create_plant(self):
        """Test creating a plant is successful."""
        user = get_user_model().objects.create_user(
            'test@example.com',
            'testpass123',
        )
        plant = models.Plant.objects.create(
            user=user,
            title='Sample plant name',
            price=Decimal('5.50'),
            description='Sample plant description.',
        )

        self.assertEqual(str(plant), plant.title)

    def test_create_tag(self):
        """Test creating a tag is successful."""
        user = create_user()
        tag = models.Tag.objects.create(user=user, name='Tag1')

        self.assertEqual(str(tag), tag.name)

    def test_create_care_tip(self):
        """Test creating a care tip is successful."""
        user = create_user()
        care_tip = models.CareTip.objects.create(
            user=user,
            name='Care Tip 1'
        )

        self.assertEqual(str(care_tip), care_tip.name)

    @patch('core.models.uuid.uuid4')
    def test_plant_file_name_uuid(self, mock_uuid):
        """Test generating image path."""
        uuid = 'test-uuid'
        mock_uuid.return_value = uuid
        file_path = models.plant_image_file_path(None, 'example.jpg')

        self.assertEqual(file_path, f'uploads/plant/{uuid}.jpg')
