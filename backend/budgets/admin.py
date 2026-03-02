from django.contrib import admin
from .models import Budget

@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ['user', 'month', 'year', 'amount', 'updated_at']
    list_filter = ['year', 'month']
