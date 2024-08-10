"""
Views for the plants APIs
"""
from rest_framework import viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from core.models import Plant
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
