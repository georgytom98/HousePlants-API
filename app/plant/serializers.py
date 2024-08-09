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
