"""
Plaid Integration — Models
===========================
PlaidItem represents one bank connection for a user.
A user can connect multiple banks — each is a separate PlaidItem.

LEARNING — Why a separate model instead of fields on User?
  A user might connect Chase AND Bank of America. Each connection has
  its own access_token, item_id, and sync cursor. Putting these on the
  User model would only allow ONE connected bank per user.
  A separate model with a ForeignKey to User supports unlimited connections.

SECURITY — The access_token is sensitive!
  Never send access_token to the frontend. The PlaidItemSerializer
  explicitly excludes it. Only the backend ever reads it.
"""
from django.db import models
from django.conf import settings


class PlaidItem(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='plaid_items'
    )

    # Plaid credentials — NEVER expose these to the frontend
    access_token = models.CharField(max_length=255)
    item_id = models.CharField(max_length=255, unique=True)

    # Display info
    institution_name = models.CharField(max_length=200, blank=True, default='')

    # List of account dicts: [{'account_id': ..., 'name': ..., 'mask': ..., 'type': ...}]
    accounts = models.JSONField(default=list)

    # Cursor for Plaid's transactions/sync endpoint.
    # Plaid returns only NEW transactions since the last cursor.
    # Empty string = start from beginning (first sync).
    cursor = models.CharField(max_length=500, blank=True, default='')

    last_synced = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} — {self.institution_name or self.item_id}"
