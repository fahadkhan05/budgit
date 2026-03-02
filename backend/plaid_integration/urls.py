"""
Plaid Integration — URL Configuration
=======================================
All Plaid endpoints are prefixed with /api/plaid/ (set in config/urls.py).

  POST   /api/plaid/create-link-token/    — Get link token for Plaid Link popup
  POST   /api/plaid/exchange-token/       — Exchange public_token for access_token
  GET    /api/plaid/items/                — List connected banks
  DELETE /api/plaid/items/<id>/remove/    — Disconnect a bank
  POST   /api/plaid/sync/                 — Sync latest transactions
"""
from django.urls import path
from . import views

urlpatterns = [
    path('create-link-token/', views.create_link_token, name='plaid_create_link_token'),
    path('exchange-token/', views.exchange_token, name='plaid_exchange_token'),
    path('items/', views.list_items, name='plaid_list_items'),
    path('items/<int:item_pk>/remove/', views.remove_item, name='plaid_remove_item'),
    path('sync/', views.sync_transactions, name='plaid_sync'),
]
