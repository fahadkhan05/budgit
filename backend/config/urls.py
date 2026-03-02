"""
Root URL Configuration
======================
This file is the "router" — the first place Django looks when a request arrives.
Every URL in the application must be connected here (directly or via include()).

LEARNING: URL routing flows like this:
  Request: GET /api/transactions/
  Django checks each path() in urlpatterns top-to-bottom
  → Finds 'api/transactions/' → delegates to transactions/urls.py
  → transactions/urls.py maps it to the correct view function

The 'include()' function lets you split URL config across multiple files,
keeping each app's URLs organized in their own urls.py file.
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    # Django's built-in admin panel — accessible at /admin/
    # After running createsuperuser, you can log in here to manage data visually
    path('admin/', admin.site.urls),

    # -----------------------------------------------------------------------
    # JWT Authentication endpoints (provided by djangorestframework-simplejwt)
    # -----------------------------------------------------------------------
    # POST /api/token/         — Login: exchange username+password for tokens
    # POST /api/token/refresh/ — Get a new access token using your refresh token
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # -----------------------------------------------------------------------
    # Our App URLs
    # -----------------------------------------------------------------------
    # include() delegates to each app's own urls.py
    # The first argument is the URL prefix — all URLs in users/urls.py
    # will start with /api/users/
    path('api/users/', include('users.urls')),
    path('api/budgets/', include('budgets.urls')),
    path('api/transactions/', include('transactions.urls')),
    path('api/recommendations/', include('recommendations.urls')),
    path('api/plaid/', include('plaid_integration.urls')),
]
