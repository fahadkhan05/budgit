"""
Budgets App — Serializers
"""
from rest_framework import serializers
from .models import Budget


class BudgetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Budget
        fields = ['id', 'month', 'year', 'amount', 'updated_at']
        read_only_fields = ['id', 'updated_at']
