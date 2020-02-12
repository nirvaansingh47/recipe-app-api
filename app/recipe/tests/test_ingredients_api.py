from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient

from recipe.serializers import IngredientSerializer


INGREDIENTS_URL = reverse('recipe:ingredient-list')


class PublicIngredientApiTest(TestCase):
    """Test public facing ingredients"""
    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        """Test login is required to access list"""
        res =self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientsApiTests(TestCase):
    """Test ingredients can be retrieved by authorized users"""
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email = "test@gmail.com",
            password = "test123"
        )
        self.client.force_authenticate(self.user)

    def test_retrieve_ingredients_list(self):
        """Test retrieving a list of ingredients"""
        Ingredient.objects.create(
            name='salt',
            user = self.user
        )
        Ingredient.objects.create(
            name='carrot',
            user = self.user
        )
        res = self.client.get(INGREDIENTS_URL)

        ingredients = Ingredient.objects.all().order_by('-name')
        serializer = IngredientSerializer(ingredients, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_ingredients_limited_to_user(self):
        """Test ingredients for authenticated users are returned"""
        user2 = get_user_model().objects.create_user(
            email = 'testusertwo@gmail.com',
            password = 'testpass'
        )
        Ingredient.objects.create(user=user2, name="pepper")
        ingredient = Ingredient.objects.create(user=self.user, name="salt")

        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], ingredient.name)

    def test_create_ingredient_successful(self):
        """Test only authenticated user can create ingredient"""
        payload = {'name': 'salt'}
        res = self.client.post(INGREDIENTS_URL, payload)
        exists = Ingredient.objects.filter(
            user = self.user,
            name = payload['name']
        ).exists()

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(exists)

    def test_create_invalid_ingredient_fails(self):
        """Test only valid ingredients can be created"""
        payload = {'name':''}
        res = self.client.post(INGREDIENTS_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        