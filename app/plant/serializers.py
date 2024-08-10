"""
Serializers for plant APIs
"""
from rest_framework import serializers

from core.models import Plant, Tag, CareTip


class CareTipSerializer(serializers.ModelSerializer):
    """Serializer for care tips."""

    class Meta:
        model = CareTip
        fields = ['id', 'name']
        read_only_fields = ['id']


class TagSerializer(serializers.ModelSerializer):
    """Serializer for tags."""

    class Meta:
        model = Tag
        fields = ['id', 'name']
        read_only_fields = ['id']


class PlantSerializer(serializers.ModelSerializer):
    """Serializer for plants."""
    tags = TagSerializer(many=True, required=False)
    care_tips = CareTipSerializer(many=True, required=False)

    class Meta:
        model = Plant
        fields = ['id', 'title', 'price', 'link', 'tags', 'care_tips']
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

    def _get_or_create_care_tips(self, care_tips, plant):
        """Handle getting or creating care tips as needed."""
        auth_user = self.context['request'].user
        for caretip in care_tips:
            caretip_obj, created = CareTip.objects.get_or_create(
                user=auth_user,
                **caretip,
            )
            plant.care_tips.add(caretip_obj)

    def create(self, validated_data):
        """Create a plant."""
        tags = validated_data.pop('tags', [])
        care_tips = validated_data.pop('care_tips', [])
        plant = Plant.objects.create(**validated_data)
        self._get_or_create_tags(tags, plant)
        self._get_or_create_care_tips(care_tips, plant)

        return plant

    def update(self, instance, validated_data):
        """Update plant."""
        tags = validated_data.pop('tags', None)
        care_tips = validated_data.pop('care_tips', None)
        if tags is not None:
            instance.tags.clear()
            self._get_or_create_tags(tags, instance)
        if care_tips is not None:
            instance.care_tips.clear()
            self._get_or_create_care_tips(care_tips, instance)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance


class PlantDetailSerializer(PlantSerializer):
    """Serializer for plant detail view."""

    class Meta(PlantSerializer.Meta):
        fields = PlantSerializer.Meta.fields + ['description',
                                                'image']


class PlantImageSerializer(serializers.ModelSerializer):
    """Serializer for uploading images to plants."""

    class Meta:
        model = Plant
        fields = ['id', 'image']
        read_only_fields = ['id']
        extra_kwargs = {'image': {'required': 'True'}}
