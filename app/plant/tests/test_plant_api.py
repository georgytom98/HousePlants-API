"""
Tests for plant APIs.
"""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Plant

from plant.serializers import PlantSerializer


PLANT_URL = reverse('plant:plant-list')


def create_plant(user, **params):
    """Create and return a sample plant."""
    defaults = {
        'title': 'Sample plant title',
        'price': Decimal('5.25'),
        'description': 'Sample description',
        'link': 'http://example.com/plant.pdf',
    }
    defaults.update(params)

    plant = Plant.objects.create(user=user, **defaults)
    return plant


class PublicPlantAPITests(TestCase):
    """Test unauthenticated API requests."""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required to call API."""
        res = self.client.get(PLANT_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivatePlantApiTests(TestCase):
    """Test authenticated API requests."""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            'user@example.com',
            'testpass123',
        )
        self.client.force_authenticate(self.user)

    def test_retrieve_plants(self):
        """Test retrieving a list of plants."""
        create_plant(user=self.user)
        create_plant(user=self.user)

        res = self.client.get(PLANT_URL)

        plants = Plant.objects.all().order_by('-id')
        serializer = PlantSerializer(plants, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_plant_list_limited_to_user(self):
        """Test list of plants is limited to authenticated user."""
        other_user = get_user_model().objects.create_user(
            'other@example.com',
            'password123',
        )
        create_plant(user=other_user)
        create_plant(user=self.user)

        res = self.client.get(PLANT_URL)

        plants = Plant.objects.filter(user=self.user)
        serializer = PlantSerializer(plants, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)
