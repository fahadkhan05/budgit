"""
Transactions App — URLs

LEARNING — Router:
  When using ModelViewSet, you register it with a Router instead of
  manually writing path() for each action. The Router auto-generates:
    GET    /                → list
    POST   /                → create
    GET    /{id}/           → retrieve
    PUT    /{id}/           → update
    PATCH  /{id}/           → partial_update
    DELETE /{id}/           → destroy
    GET    /stats/          → our custom @action
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TransactionViewSet

app_name = 'transactions'

router = DefaultRouter()
# '' means the ViewSet is mounted at the root of this URL pattern
# Combined with the prefix in config/urls.py ('api/transactions/'), you get:
#   /api/transactions/
#   /api/transactions/{id}/
#   /api/transactions/stats/
router.register('', TransactionViewSet, basename='transaction')

urlpatterns = [
    path('', include(router.urls)),
]
