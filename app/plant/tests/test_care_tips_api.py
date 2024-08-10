"""
Tests for the Care Tips API.
"""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import CareTip, Plant

from plant.serializers import CareTipSerializer


CARETIPS_URL = reverse('plant:caretip-list')


def detail_url(care_tip_id):
    """Create and return a care tip detail URL."""
    return reverse('plant:caretip-detail', args=[care_tip_id])


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

    def test_update_care_tip(self):
        """Test updating an care tip."""
        care_tip = CareTip.objects.create(user=self.user, name='Add water')

        payload = {'name': 'Trim'}
        url = detail_url(care_tip.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        care_tip.refresh_from_db()
        self.assertEqual(care_tip.name, payload['name'])

    def test_delete_care_tip(self):
        """Test deleting an care tip."""
        care_tip = CareTip.objects.create(user=self.user, name='Add water')

        url = detail_url(care_tip.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        care_tips = CareTip.objects.filter(user=self.user)
        self.assertFalse(care_tips.exists())

    def test_filter_care_tips_assigned_to_plants(self):
        """Test listing ingedients to those assigned to plants."""
        in1 = CareTip.objects.create(user=self.user, name='Trim')
        in2 = CareTip.objects.create(user=self.user, name='Add water')
        plant = Plant.objects.create(
            title='mint',
            price=Decimal('4.50'),
            user=self.user,
        )
        plant.care_tips.add(in1)

        res = self.client.get(CARETIPS_URL, {'assigned_only': 1})

        s1 = CareTipSerializer(in1)
        s2 = CareTipSerializer(in2)
        self.assertIn(s1.data, res.data)
        self.assertNotIn(s2.data, res.data)

    def test_filtered_care_tips_unique(self):
        """Test filtered care tips returns a unique list."""
        ing = CareTip.objects.create(user=self.user, name='Add water')
        CareTip.objects.create(user=self.user, name='Trim')
        plant1 = Plant.objects.create(
            title='Aloe vera',
            price=Decimal('7.00'),
            user=self.user,
        )
        plant2 = Plant.objects.create(
            title='snake plant',
            price=Decimal('14.00'),
            user=self.user,
        )
        plant1.care_tips.add(ing)
        plant2.care_tips.add(ing)

        res = self.client.get(CARETIPS_URL, {'assigned_only': 1})

        self.assertEqual(len(res.data), 1)
