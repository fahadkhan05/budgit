from django.urls import path
from .views import CurrentBudgetView

app_name = 'budgets'

urlpatterns = [
    path('current/', CurrentBudgetView.as_view(), name='current'),
]
