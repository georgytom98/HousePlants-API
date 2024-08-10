"""
Serializers for plant APIs
"""
from rest_framework import serializers

from core.models import Plant, Tag


class TagSerializer(serializers.ModelSerializer):
    """Serializer for tags."""

    class Meta:
        model = Tag
        fields = ['id', 'name']
        read_only_fields = ['id']


class PlantSerializer(serializers.ModelSerializer):
    """Serializer for plants."""
    tags = TagSerializer(many=True, required=False)

    class Meta:
        model = Plant
        fields = ['id', 'title', 'price', 'link', 'tags']
        read_only_fields = ['id']

    def _get_or_create_tags(self, tags, plant):
        """Handle getting or creating tags as needed."""
        auth_user = self.context['request'].user
        for tag in tags:
            tag_obj, created = Tag.objects.get_or_create(
                user=auth_user,
                **tag,
            )
            plant.tags.add(tag_obj)

    def create(self, validated_data):
        """Create a plant."""
        tags = validated_data.pop('tags', [])
        plant = Plant.objects.create(**validated_data)
        self._get_or_create_tags(tags, plant)

        return plant

    def update(self, instance, validated_data):
        """Update plant."""
        tags = validated_data.pop('tags', None)
        if tags is not None:
            instance.tags.clear()
            self._get_or_create_tags(tags, instance)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance


class PlantDetailSerializer(PlantSerializer):
    """Serializer for plant detail view."""

    class Meta(PlantSerializer.Meta):
        fields = PlantSerializer.Meta.fields + ['description']
