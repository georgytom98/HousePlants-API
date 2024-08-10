"""
Tests for plant APIs.
"""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Plant, Tag, CareTip

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

    def test_create_plant_with_new_tags(self):
        """Test creating a plant with new tags."""
        payload = {
            'title': 'ZZ Plant',
            'price': Decimal('12.50'),
            'tags': [{'name': 'low cost'}, {'name': 'popular'}],
        }
        res = self.client.post(PLANT_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        plants = Plant.objects.filter(user=self.user)
        self.assertEqual(plants.count(), 1)
        plant = plants[0]
        self.assertEqual(plant.tags.count(), 2)
        for tag in payload['tags']:
            exists = plant.tags.filter(
                name=tag['name'],
                user=self.user,
            ).exists()
            self.assertTrue(exists)

    def test_create_plant_with_existing_tags(self):
        """Test creating a plant with existing tag."""
        tag_popular = Tag.objects.create(user=self.user, name='popular')
        payload = {
            'title': 'String of Pearls',
            'price': Decimal('9.50'),
            'tags': [{'name': 'succulant'}, {'name': 'popular'}],
        }
        res = self.client.post(PLANT_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        plants = Plant.objects.filter(user=self.user)
        self.assertEqual(plants.count(), 1)
        plant = plants[0]
        self.assertEqual(plant.tags.count(), 2)
        self.assertIn(tag_popular, plant.tags.all())
        for tag in payload['tags']:
            exists = plant.tags.filter(
                name=tag['name'],
                user=self.user,
            ).exists()
            self.assertTrue(exists)

    def test_create_tag_on_update(self):
        """Test create tag when updating a plant."""
        plant = create_plant(user=self.user)

        payload = {'tags': [{'name': 'popular'}]}
        url = detail_url(plant.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_tag = Tag.objects.get(user=self.user, name='popular')
        self.assertIn(new_tag, plant.tags.all())

    def test_update_plant_assign_tag(self):
        """Test assigning an existing tag when updating a plant."""
        tag_breakfast = Tag.objects.create(user=self.user, name='favorite')
        plant = create_plant(user=self.user)
        plant.tags.add(tag_breakfast)

        tag_lunch = Tag.objects.create(user=self.user, name='Lunch')
        payload = {'tags': [{'name': 'Lunch'}]}
        url = detail_url(plant.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(tag_lunch, plant.tags.all())
        self.assertNotIn(tag_breakfast, plant.tags.all())

    def test_clear_plant_tags(self):
        """Test clearing a plants tags."""
        tag = Tag.objects.create(user=self.user, name='Dessert')
        plant = create_plant(user=self.user)
        plant.tags.add(tag)

        payload = {'tags': []}
        url = detail_url(plant.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(plant.tags.count(), 0)

    def test_create_plant_with_new_care_tips(self):
        """Test creating a plant with new care tips."""
        payload = {
            'title': 'ZZ Plant',
            'price': Decimal('4.30'),
            'care_tips': [{'name': 'Add water'}, {'name': 'Trim'}],
        }
        res = self.client.post(PLANT_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        plants = Plant.objects.filter(user=self.user)
        self.assertEqual(plants.count(), 1)
        plant = plants[0]
        self.assertEqual(plant.care_tips.count(), 2)
        for care_tip in payload['care_tips']:
            exists = plant.care_tips.filter(
                name=care_tip['name'],
                user=self.user,
            ).exists()
            self.assertTrue(exists)

    def test_create_plant_with_existing_care_tip(self):
        """Test creating a new plant with existing care tip."""
        care_tip = CareTip.objects.create(user=self.user, name='Trim')
        payload = {
            'title': 'ZZ Plant',
            'price': '3.55',
            'care_tips': [{'name': 'Add Water'}, {'name': 'Trim'}],
        }
        res = self.client.post(PLANT_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        plants = Plant.objects.filter(user=self.user)
        self.assertEqual(plants.count(), 1)
        plant = plants[0]
        self.assertEqual(plant.care_tips.count(), 2)
        self.assertIn(care_tip, plant.care_tips.all())
        for caretip in payload['care_tips']:
            exists = plant.care_tips.filter(
                name=caretip['name'],
                user=self.user,
            ).exists()
            self.assertTrue(exists)

    def test_create_care_tip_on_update(self):
        """Test creating an care tip when updating a plant."""
        plant = create_plant(user=self.user)

        payload = {'care_tips': [{'name': 'Add water'}]}
        url = detail_url(plant.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_care_tip = CareTip.objects.get(user=self.user, name='Add water')
        self.assertIn(new_care_tip, plant.care_tips.all())

    def test_update_plant_assign_care_tip(self):
        """Test assigning an existing care tip when updating a plant."""
        care_tip1 = CareTip.objects.create(user=self.user, name='Pepper')
        plant = create_plant(user=self.user)
        plant.care_tips.add(care_tip1)

        care_tip2 = CareTip.objects.create(user=self.user, name='Trim')
        payload = {'care_tips': [{'name': 'Trim'}]}
        url = detail_url(plant.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(care_tip2, plant.care_tips.all())
        self.assertNotIn(care_tip1, plant.care_tips.all())

    def test_clear_plant_care_tips(self):
        """Test clearing a plants care tips."""
        care_tip = CareTip.objects.create(user=self.user, name='Garlic')
        plant = create_plant(user=self.user)
        plant.care_tips.add(care_tip)

        payload = {'care_tips': []}
        url = detail_url(plant.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(plant.care_tips.count(), 0)
