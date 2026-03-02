"""
Users App — URL Configuration
==============================
These URLs are "mounted" at /api/users/ in config/urls.py.
So the full paths are:
  /api/users/register/ → RegisterView
  /api/users/profile/  → ProfileView
"""
from django.urls import path
from .views import RegisterView, ProfileView

# app_name creates a "namespace" so you can use reverse('users:register')
# in Python code to get the URL without hardcoding it
app_name = 'users'

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('profile/', ProfileView.as_view(), name='profile'),
]
