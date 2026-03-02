"""
Budgets App — Models
=====================
This model represents a user's monthly budget.

KEY CONCEPTS:
  ForeignKey — A relationship between two tables.
    Here, each Budget belongs to one User.
    ON_DELETE=CASCADE means if the User is deleted, all their budgets are too.

  unique_together — A database constraint ensuring no duplicate entries.
    Here, a user can only have ONE budget per month+year combination.
    (You can't have two March 2025 budgets for the same user.)

  DecimalField — For money! Always use DecimalField for currency, never float.
    Float can have rounding errors (e.g., 0.1 + 0.2 = 0.30000000000000004).
    max_digits=10, decimal_places=2 → up to 99,999,999.99
"""
from django.db import models
from django.conf import settings


class Budget(models.Model):
    # ForeignKey creates a column 'user_id' in the budget table
    # related_name='budgets' lets you do user.budgets.all() from a User instance
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='budgets'
    )
    month = models.IntegerField()   # 1 = January, 12 = December
    year = models.IntegerField()    # e.g., 2025
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)  # Set once on creation
    updated_at = models.DateTimeField(auto_now=True)      # Updated every save

    class Meta:
        # This constraint is enforced at the DATABASE level, not just Python level.
        # Even if you bypass Python validation, the DB won't allow duplicates.
        unique_together = ['user', 'month', 'year']
        ordering = ['-year', '-month']  # Most recent first

    def __str__(self):
        return f"{self.user.username} — {self.month}/{self.year}: ${self.amount}"
