"""
Transactions App — Views
=========================
This is the most complex view set in the project. It handles full CRUD for
transactions AND a custom stats endpoint.

LEARNING — ModelViewSet:
  A ViewSet groups related views into one class. ModelViewSet auto-provides:
    list()           → GET    /transactions/        → returns list
    create()         → POST   /transactions/        → creates one
    retrieve()       → GET    /transactions/{id}/   → returns one
    update()         → PUT    /transactions/{id}/   → replaces one
    partial_update() → PATCH  /transactions/{id}/   → updates one
    destroy()        → DELETE /transactions/{id}/   → deletes one

  We override get_queryset() to filter by user and date,
  and perform_create() to automatically attach the user.

LEARNING — @action:
  The @action decorator adds custom endpoints beyond standard CRUD.
  Here we add /transactions/stats/ to return spending summaries.
"""
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum
from datetime import date

from .models import Transaction
from .serializers import TransactionSerializer


class TransactionViewSet(viewsets.ModelViewSet):
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Filter transactions to ONLY the current user's data.

        THIS IS SECURITY-CRITICAL. Without this filter, user A could
        call GET /api/transactions/ and see all of user B's transactions!

        We also support optional ?month=&year= query params for filtering.
        """
        user = self.request.user
        queryset = Transaction.objects.filter(user=user)

        month = self.request.query_params.get('month')
        year = self.request.query_params.get('year')

        if month:
            queryset = queryset.filter(date__month=month)
        if year:
            queryset = queryset.filter(date__year=year)

        return queryset

    def perform_create(self, serializer):
        """
        Called by DRF when creating a new transaction.
        We inject the current user so the frontend doesn't need to send user_id.

        LEARNING: This is called "request injection" — the API client only sends
        the transaction data, and the server figures out which user it belongs to
        by checking the JWT token.
        """
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'], url_path='monthly-stats')
    def monthly_stats(self, request):
        """
        GET /api/transactions/monthly-stats/?year=2026

        Returns total expenses for each of the 12 months in the given year.
        Used by the dashboard line graph.

        LEARNING — looping to build a list:
          Instead of 12 separate queries we loop months 1-12 and build a list.
          Each iteration runs one aggregation query, returns 0 if no data.
        """
        year = int(request.query_params.get('year', date.today().year))

        monthly = []
        for month in range(1, 13):
            total = Transaction.objects.filter(
                user=request.user,
                date__year=year,
                date__month=month,
            ).exclude(category='income').aggregate(total=Sum('amount'))['total'] or 0
            monthly.append({'month': month, 'total': float(total)})

        return Response({'year': year, 'monthly': monthly})

    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, request):
        """
        GET /api/transactions/stats/

        Returns spending statistics for a given month.
        Defaults to current month/year.

        LEARNING — Django ORM Aggregations:
          .aggregate(total=Sum('amount')) runs:
            SELECT SUM(amount) AS total FROM transactions WHERE ...
          It returns a dict: {'total': Decimal('832.50')}

        LEARNING — dict comprehension:
          { key: value for item in iterable if condition }
          Here we build the by_category dict in one line.
        """
        today = date.today()
        month = int(request.query_params.get('month', today.month))
        year = int(request.query_params.get('year', today.year))

        # Expenses only (exclude income from "spent" totals)
        expense_qs = Transaction.objects.filter(
            user=request.user,
            date__month=month,
            date__year=year,
        ).exclude(category='income')

        income_qs = Transaction.objects.filter(
            user=request.user,
            date__month=month,
            date__year=year,
            category='income'
        )

        total_spent = expense_qs.aggregate(total=Sum('amount'))['total'] or 0
        total_income = income_qs.aggregate(total=Sum('amount'))['total'] or 0

        # Build spending breakdown per category
        # Only include categories that have transactions
        by_category = {}
        for code, label in Transaction.CATEGORY_CHOICES:
            if code == 'income':
                continue
            amount = expense_qs.filter(category=code).aggregate(
                total=Sum('amount')
            )['total'] or 0
            if amount > 0:
                by_category[label] = float(amount)

        return Response({
            'month': month,
            'year': year,
            'total_spent': float(total_spent),
            'total_income': float(total_income),
            'by_category': by_category,
            'transaction_count': expense_qs.count(),
        })
