"""
Serializers for plant APIs
"""
from rest_framework import serializers

from core.models import Plant


class PlantSerializer(serializers.ModelSerializer):
    """Serializer for plants."""

    class Meta:
        model = Plant
        fields = ['id', 'title', 'price', 'link']
        read_only_fields = ['id']


class PlantDetailSerializer(PlantSerializer):
    """Serializer for plant detail view."""

    class Meta(PlantSerializer.Meta):
        fields = PlantSerializer.Meta.fields + ['description']
