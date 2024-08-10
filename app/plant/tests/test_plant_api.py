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

from plant.serializers import PlantSerializer, PlantDetailSerializer


PLANT_URL = reverse('plant:plant-list')


def detail_url(plant_id):
    """Create and return a plant detail URL."""
    return reverse('plant:plant-detail', args=[plant_id])


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


def create_user(**params):
    """Create and return a new user."""
    return get_user_model().objects.create_user(**params)


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
            email='user@example.com',
            password='testpass123',
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
            email='other@example.com',
            password='password123',
        )
        create_plant(user=other_user)
        create_plant(user=self.user)

        res = self.client.get(PLANT_URL)

        plants = Plant.objects.filter(user=self.user)
        serializer = PlantSerializer(plants, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_get_plant_detail(self):
        """Test get plant detail."""
        plant = create_plant(user=self.user)

        url = detail_url(plant.id)
        res = self.client.get(url)

        serializer = PlantDetailSerializer(plant)
        self.assertEqual(res.data, serializer.data)

    def test_create_plant(self):
        """Test creating a plant."""
        payload = {
            'title': 'Sample plant',
            'price': Decimal('5.99'),
        }
        res = self.client.post(PLANT_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        plant = Plant.objects.get(id=res.data['id'])
        for k, v in payload.items():
            self.assertEqual(getattr(plant, k), v)
        self.assertEqual(plant.user, self.user)

    def test_partial_update(self):
        """Test partial update of a plant."""
        original_link = 'https://example.com/plant.pdf'
        plant = create_plant(
            user=self.user,
            title='Sample plant title',
            link=original_link,
        )

        payload = {'title': 'New plant title'}
        url = detail_url(plant.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        plant.refresh_from_db()
        self.assertEqual(plant.title, payload['title'])
        self.assertEqual(plant.link, original_link)
        self.assertEqual(plant.user, self.user)

    def test_full_update(self):
        """Test full update of plant."""
        plant = create_plant(
            user=self.user,
            title='Sample plant title',
            link='https://exmaple.com/plant.pdf',
            description='Sample plant description.',
        )

        payload = {
            'title': 'New plant title',
            'link': 'https://example.com/new-plant.pdf',
            'description': 'New plant description',
            'price': Decimal('2.50'),
        }
        url = detail_url(plant.id)
        res = self.client.put(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        plant.refresh_from_db()
        for k, v in payload.items():
            self.assertEqual(getattr(plant, k), v)
        self.assertEqual(plant.user, self.user)

    def test_update_user_returns_error(self):
        """Test changing the plant user results in an error."""
        new_user = create_user(email='user2@example.com', password='test123')
        plant = create_plant(user=self.user)

        payload = {'user': new_user.id}
        url = detail_url(plant.id)
        self.client.patch(url, payload)

        plant.refresh_from_db()
        self.assertEqual(plant.user, self.user)

    def test_delete_plant(self):
        """Test deleting a plant successful."""
        plant = create_plant(user=self.user)

        url = detail_url(plant.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Plant.objects.filter(id=plant.id).exists())

    def test_deleting_other_users_plant_error(self):
        """Test trying to delete another users plant gives error."""
        new_user = create_user(email='user2@example.com', password='test123')
        plant = create_plant(user=new_user)

        url = detail_url(plant.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Plant.objects.filter(id=plant.id).exists())
