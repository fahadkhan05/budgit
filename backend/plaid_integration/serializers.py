"""
Plaid Integration — Serializers
=================================
SECURITY: access_token and cursor are intentionally excluded from all
serializers. These are backend-only secrets and must never be sent to
the frontend.
"""
from rest_framework import serializers
from .models import PlaidItem


class PlaidItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlaidItem
        # access_token and cursor are excluded — they're backend-only secrets
        fields = ['id', 'institution_name', 'accounts', 'last_synced', 'created_at']
