"""
Transactions App — Models
==========================
A Transaction records a single expense or income event.

KEY CONCEPTS:
  choices — A list of (value, display_label) tuples that restricts what
             can be stored in a field. The DB stores the short code ('food'),
             but Django shows the human-readable label ('Food & Dining').

  DateField vs DateTimeField — DateField stores just a date (2025-03-15).
             DateTimeField stores date + time. For a transaction date, we
             only need the date, so DateField is the right choice.
"""
from django.db import models
from django.conf import settings


class Transaction(models.Model):
    CATEGORY_CHOICES = [
        ('food', 'Food & Dining'),
        ('entertainment', 'Entertainment'),
        ('shopping', 'Shopping'),
        ('fitness', 'Fitness'),
        ('travel', 'Travel'),
        ('utilities', 'Utilities & Bills'),
        ('income', 'Income'),
        ('other', 'Other'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='transactions'
    )
    title = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='other')
    date = models.DateField()
    description = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    # Set when imported from Plaid — used to prevent duplicate imports.
    # Null for manually entered transactions.
    plaid_transaction_id = models.CharField(max_length=200, blank=True, null=True, unique=True)

    class Meta:
        ordering = ['-date', '-created_at']  # Newest first

    def __str__(self):
        return f"{self.user.username} — {self.title}: ${self.amount}"
