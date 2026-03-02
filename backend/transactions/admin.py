from django.contrib import admin
from .models import Transaction

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'amount', 'category', 'date']
    list_filter = ['category', 'date']
    search_fields = ['title', 'user__username']
