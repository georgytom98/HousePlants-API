"""
URL mappings for the plant app.
"""
from django.urls import (
    path,
    include,
)

from rest_framework.routers import DefaultRouter

from plant import views


router = DefaultRouter()
router.register('plants', views.PlantViewSet)
router.register('tags', views.TagViewSet)

app_name = 'plant'

urlpatterns = [
    path('', include(router.urls)),
]
