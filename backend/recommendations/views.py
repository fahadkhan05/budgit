"""
Recommendations App — Views
============================
A single endpoint that pulls together data from multiple apps (users, budgets,
transactions) and feeds it to the recommendation engine.

LEARNING — Cross-App Queries:
  In Django, apps are loosely coupled but can import from each other.
  Here we import models from both 'transactions' and 'budgets' to
  calculate the user's remaining budget before generating recommendations.

  The key insight: a VIEW can orchestrate data from many models/apps.
  The MODEL should not know about other apps (keep models focused).
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from django.db.models import Sum
from datetime import date

from transactions.models import Transaction
from budgets.models import Budget
from .engine import get_recommendations


def _get_recommendations(interests, remaining_budget):
    """
    Try the AI engine first; fall back to the static engine if anything fails.

    LEARNING — Graceful Degradation:
      External API calls can fail (no key, network error, bad response).
      Wrapping them in a try/except and falling back to a reliable local
      alternative means the feature always works, even without an API key.
      Users without a key just get the static recommendations instead of an error.
    """
    try:
        from .ai_engine import get_ai_recommendations
        return get_ai_recommendations(interests, remaining_budget)
    except Exception as e:
        print(f"[AI engine failed, using static fallback] {type(e).__name__}: {e}")
        return get_recommendations(interests, remaining_budget)


class RecommendationsView(APIView):
    """
    GET /api/recommendations/

    Returns:
      - The user's interests
      - Budget summary (budget, spent, remaining)
      - A list of personalized recommendations
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        today = date.today()

        # --- Step 1: Get this month's budget ---
        try:
            budget = Budget.objects.get(
                user=user,
                month=today.month,
                year=today.year
            )
            budget_amount = float(budget.amount)
        except Budget.DoesNotExist:
            budget_amount = 0.0

        # --- Step 2: Get total spent this month (expenses only) ---
        total_spent = Transaction.objects.filter(
            user=user,
            date__month=today.month,
            date__year=today.year,
        ).exclude(category='income').aggregate(
            total=Sum('amount')
        )['total'] or 0

        remaining_budget = budget_amount - float(total_spent)

        # --- Step 3: Generate recommendations ---
        interests = user.interests or []
        recommendations = _get_recommendations(interests, remaining_budget)

        return Response({
            'budget_amount': budget_amount,
            'total_spent': float(total_spent),
            'remaining_budget': remaining_budget,
            'interests': interests,
            'recommendations': recommendations,
        })
