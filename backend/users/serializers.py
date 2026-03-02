"""
Users App — Serializers
========================
A Serializer converts between complex Python objects (like Django model instances)
and simple Python data types (dicts, lists) that can then be rendered into JSON.

Think of it as a translation layer:
  DB Record → Python Object → Serializer → JSON (sent to browser)
  JSON → Serializer (validates) → Python Object → DB Record

LEARNING: Why not just use json.dumps() directly?
  Serializers also do VALIDATION. Before saving data, they check:
  - Are all required fields present?
  - Are the values the correct type/format?
  - Do passwords match? Is the email valid?
  They give you clean error messages when validation fails.
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

# get_user_model() returns our custom User class (not the built-in one)
# Always use this instead of importing User directly — it respects AUTH_USER_MODEL
User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """
    Used for reading and updating user profile data.

    ModelSerializer auto-generates fields from the model.
    We explicitly list which fields to expose — never expose the password hash!

    read_only_fields: These fields are returned in responses but ignored
    in incoming data. You can't change your own username via the API.
    """
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'interests']
        read_only_fields = ['id', 'username']


class RegisterSerializer(serializers.ModelSerializer):
    """
    Used ONLY for creating new user accounts.

    Extra complexity here because:
      1. Passwords must be write-only (never returned in a response)
      2. We need to confirm the password matches
      3. We must HASH the password before saving (use create_user, not create)
    """
    password = serializers.CharField(
        write_only=True,              # Never included in response JSON
        required=True,
        validators=[validate_password] # Runs Django's password strength validators
    )
    password2 = serializers.CharField(
        write_only=True,
        required=True,
        label='Confirm Password'
    )

    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'password2',
            'first_name', 'last_name', 'interests'
        ]

    def validate(self, attrs):
        """
        Object-level validation: runs after all individual field validators.
        Here we check that both passwords match.

        LEARNING: If validation fails, raise serializers.ValidationError.
        DRF catches this and automatically returns a 400 Bad Request response
        with the error details as JSON. You don't have to handle it manually!
        """
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({'password': "Passwords don't match."})
        return attrs

    def create(self, validated_data):
        """
        Custom create method: we use create_user() instead of create().

        CRITICAL: create_user() HASHES the password before saving.
        If you used User.objects.create(**data), the password would be
        stored in plain text — a massive security vulnerability!
        """
        validated_data.pop('password2')  # Remove confirmation field
        user = User.objects.create_user(**validated_data)
        return user
