"""
Users App — Admin Registration
================================
Registering models here makes them visible and editable in Django's
built-in admin panel at /admin/.

After running `python manage.py createsuperuser`, you can log into /admin/
and directly view/edit/delete User records — super useful for debugging!
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

# UserAdmin provides a nice pre-built admin interface for user management
# (password change form, permissions, groups, etc.)
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    # Add our custom 'interests' field to the admin display
    list_display = ['username', 'email', 'first_name', 'last_name', 'is_staff']
    fieldsets = UserAdmin.fieldsets + (
        ('Profile', {'fields': ('interests',)}),
    )
