"""
Budgets App — Views
====================
Handles getting and setting the monthly budget.

LEARNING: APIView gives you full control over each HTTP method.
We use it here because the logic for GET (find or return zero) and
POST (create or update) is custom enough to warrant it.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from datetime import date

from .models import Budget
from .serializers import BudgetSerializer


class CurrentBudgetView(APIView):
    """
    GET  /api/budgets/current/  — Get the budget for the current (or specified) month
    POST /api/budgets/current/  — Create or update a monthly budget

    Query params:
      ?month=3&year=2025 — get/set a specific month (defaults to current month)
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        today = date.today()
        month = int(request.query_params.get('month', today.month))
        year = int(request.query_params.get('year', today.year))

        try:
            budget = Budget.objects.get(user=request.user, month=month, year=year)
            return Response(BudgetSerializer(budget).data)
        except Budget.DoesNotExist:
            # Return a "zero budget" response instead of a 404
            # This makes the frontend simpler — it always gets a valid response
            return Response({
                'id': None,
                'amount': '0.00',
                'month': month,
                'year': year,
                'exists': False
            })

    def post(self, request):
        today = date.today()
        month = int(request.data.get('month', today.month))
        year = int(request.data.get('year', today.year))
        amount = request.data.get('amount')

        if not amount:
            return Response({'error': 'Amount is required.'}, status=status.HTTP_400_BAD_REQUEST)

        # get_or_create is an atomic operation:
        #   - If a budget for this user/month/year exists, return it (created=False)
        #   - If not, create one with the given defaults (created=True)
        # This prevents race conditions better than doing get() then create() separately
        budget, created = Budget.objects.get_or_create(
            user=request.user,
            month=month,
            year=year,
            defaults={'amount': amount}
        )

        if not created:
            # Budget already existed — update it
            budget.amount = amount
            budget.save()

        return Response(
            BudgetSerializer(budget).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
        )
