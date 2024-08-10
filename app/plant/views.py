"""
Views for the plants APIs
"""
from rest_framework import viewsets, mixins
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from core.models import Plant, Tag, CareTip
from plant import serializers


class PlantViewSet(viewsets.ModelViewSet):
    """View for manage plant APIs."""
    serializer_class = serializers.PlantDetailSerializer
    queryset = Plant.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Retrieve plants for authenticated user."""
        return self.queryset.filter(user=self.request.user).order_by('-id')

    def get_serializer_class(self):
        """Return the serializer class for request."""
        if self.action == 'list':
            return serializers.PlantSerializer

        return self.serializer_class

    def perform_create(self, serializer):
        """Create a new plant."""
        serializer.save(user=self.request.user)


class BasePlantAttrViewSet(mixins.DestroyModelMixin,
                           mixins.UpdateModelMixin,
                           mixins.ListModelMixin,
                           viewsets.GenericViewSet):
    """Base viewset for plant attributes."""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter queryset to authenticated user."""
        return self.queryset.filter(user=self.request.user).order_by('-name')


class TagViewSet(BasePlantAttrViewSet):
    """Manage tags in the database."""
    serializer_class = serializers.TagSerializer
    queryset = Tag.objects.all()


class CareTipViewSet(BasePlantAttrViewSet):
    """Manage care tips in the database."""
    serializer_class = serializers.CareTipSerializer
    queryset = CareTip.objects.all()
