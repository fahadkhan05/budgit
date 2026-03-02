"""
Transactions App — Serializers
"""
from rest_framework import serializers
from .models import Transaction


class TransactionSerializer(serializers.ModelSerializer):
    # SerializerMethodField lets you add computed read-only fields.
    # DRF will call get_category_display() to populate this field.
    category_display = serializers.SerializerMethodField()

    class Meta:
        model = Transaction
        fields = [
            'id', 'title', 'amount', 'category', 'category_display',
            'date', 'description', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'category_display']

    def get_category_display(self, obj):
        """
        Returns the human-readable category label.
        obj.get_category_display() is a Django method automatically added
        to any field with choices= — it returns the second element of the tuple.
        e.g., 'food' → 'Food & Dining'
        """
        return obj.get_category_display()
