"""
Users App — Models
==================
A Django Model is a Python class that maps directly to a database table.
Each attribute = a column in the table.

LEARNING: Why extend AbstractUser instead of using the built-in User?
  Django's built-in User model has: username, password, email, first_name, last_name
  We need to add: interests (a list of what the user enjoys)

  AbstractUser gives us ALL the built-in fields + auth logic, and we add our own.

IMPORTANT: settings.py must have AUTH_USER_MODEL = 'users.User' for Django
to use this model instead of the default one.
"""
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Extended User model with a field to store personal interests.

    FIELD TYPES USED HERE:
      JSONField — stores a Python list/dict as JSON in the database.
                  Perfect for flexible data like a list of interest tags.
                  default=list means new users start with an empty list.

    INTERESTS are strings like: 'dining', 'fitness', 'travel', 'entertainment',
    'shopping', 'arts', 'outdoor', 'technology'
    """
    interests = models.JSONField(
        default=list,   # Each new user gets [] by default
        blank=True,     # The form allows it to be empty
    )

    def __str__(self):
        # This is what displays in the Django admin panel and shell
        return self.username
