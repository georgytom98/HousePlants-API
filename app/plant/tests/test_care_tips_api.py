"""
Tests for the Care Tips API.
"""
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import CareTip

from plant.serializers import CareTipSerializer


CARETIPS_URL = reverse('plant:caretip-list')


def create_user(email='user@example.com', password='testpass123'):
    """Create and return user."""
    return get_user_model().objects.create_user(email=email, password=password)


class PublicCareTipsApiTests(TestCase):
    """Test unauthenticated API requests."""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required for retrieving care tips."""
        res = self.client.get(CARETIPS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateCareTipsApiTests(TestCase):
    """Test authenticated API requests."""

    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_care_tips(self):
        """Test retrieving a list of care tips."""
        CareTip.objects.create(user=self.user, name='Kale')
        CareTip.objects.create(user=self.user, name='Vanilla')

        res = self.client.get(CARETIPS_URL)

        care_tips = CareTip.objects.all().order_by('-name')
        serializer = CareTipSerializer(care_tips, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_care_tips_limited_to_user(self):
        """Test list of care tips is limited to authenticated user."""
        user2 = create_user(email='user2@example.com')
        CareTip.objects.create(user=user2, name='Salt')
        care_tip = CareTip.objects.create(user=self.user, name='Pepper')

        res = self.client.get(CARETIPS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], care_tip.name)
        self.assertEqual(res.data[0]['id'], care_tip.id)
