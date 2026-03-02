from django.urls import path
from .views import RecommendationsView

app_name = 'recommendations'

urlpatterns = [
    path('', RecommendationsView.as_view(), name='recommendations'),
]
