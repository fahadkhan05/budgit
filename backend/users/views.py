"""
Users App — Views
=================
A View receives an HTTP request, does some work, and returns an HTTP response.
In DRF (Django REST Framework), views handle the request/response in a
structured, class-based way.

LEARNING: Two styles of DRF views:
  1. APIView — you write each HTTP method (get, post, patch) yourself.
               More code, more control. Good for custom logic.

  2. Generic Views (CreateAPIView, ListCreateAPIView) — DRF provides
     the implementation; you just configure it. Less code, less control.

We use CreateAPIView for register (simple create) and APIView for the
profile (needs custom get + patch logic).
"""
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model

from .serializers import UserSerializer, RegisterSerializer

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    """
    POST /api/users/register/
    Creates a new user account.

    LEARNING: CreateAPIView handles the entire "POST → validate → save → 201 Created"
    cycle automatically. We just specify:
      - queryset:           Which model to work with
      - serializer_class:   How to validate/save the data
      - permission_classes: Who can access this endpoint

    AllowAny overrides the global default (IsAuthenticated) so that
    unauthenticated users CAN reach this endpoint — you need to be able
    to register before you have an account!
    """
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]  # Override global default


class ProfileView(APIView):
    """
    GET  /api/users/profile/  — Returns the current user's profile
    PATCH /api/users/profile/ — Updates the user's profile (e.g., interests)

    LEARNING: request.user is automatically populated by DRF based on
    the JWT token in the Authorization header. You never have to look up
    the user manually — DRF handles authentication for you.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Return the current user's profile data."""
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    def patch(self, request):
        """
        Partially update the user's profile.

        PATCH vs PUT:
          PUT   — requires ALL fields to be sent; replaces the entire resource
          PATCH — only requires the fields you want to change; partial update

        partial=True tells the serializer that missing fields are okay.
        """
        serializer = UserSerializer(
            request.user,
            data=request.data,
            partial=True  # Don't require all fields
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        # If validation fails, return 400 with the error details
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
