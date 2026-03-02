"""
Plaid Integration — Views
==========================
Handles the full Plaid bank connection flow:

  1. create_link_token  — Frontend calls this to get a token that initializes
                          the Plaid Link popup.

  2. exchange_token     — After user connects their bank, Plaid gives the
                          frontend a one-time public_token. This endpoint
                          exchanges it for a permanent access_token (stored
                          securely on the server).

  3. list_items         — Returns all connected banks for the current user
                          (without access_token — that stays on the server).

  4. remove_item        — Disconnects a bank (deletes the PlaidItem).

  5. sync_transactions  — Pulls the latest transactions from Plaid and saves
                          them to the Transaction table. Uses cursor-based
                          pagination so only NEW transactions are fetched
                          on each sync.

LEARNING — Plaid's transactions/sync endpoint:
  Unlike a simple "get all transactions", Plaid's sync endpoint uses a
  cursor. On first call (no cursor): returns ALL historical transactions.
  On subsequent calls: returns only what changed since the last call.
  This is much more efficient — you only process new data each time.

LEARNING — Plaid amount sign convention:
  Positive amount = money OUT (expense/debit from your account)
  Negative amount = money IN (income/credit to your account)
  This is the opposite of what you might expect! We handle this in
  _map_plaid_transaction().
"""
import plaid
from plaid.api import plaid_api
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.products import Products
from plaid.model.country_code import CountryCode
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.model.transactions_sync_request import TransactionsSyncRequest
from plaid.model.accounts_get_request import AccountsGetRequest

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from django.conf import settings
from django.utils import timezone

from .models import PlaidItem
from .serializers import PlaidItemSerializer
from transactions.models import Transaction


# ---------------------------------------------------------------------------
# Category mapping: Plaid's categories → our app's categories
# ---------------------------------------------------------------------------
# Plaid uses personal_finance_category.primary (newer) or category list (older).
# We map both to our 8-category system.
PLAID_CATEGORY_MAP = {
    # personal_finance_category.primary values (uppercase enums)
    'FOOD_AND_DRINK': 'food',
    'TRAVEL': 'travel',
    'TRANSPORTATION': 'travel',
    'ENTERTAINMENT': 'entertainment',
    'GENERAL_MERCHANDISE': 'shopping',
    'PERSONAL_CARE': 'other',
    'HOME_IMPROVEMENT': 'other',
    'UTILITIES_AND_PHONE_SERVICES': 'utilities',
    'RENT_AND_UTILITIES': 'utilities',
    'MEDICAL': 'other',
    'INCOME': 'income',
    'TRANSFER_IN': 'income',
    'TRANSFER_OUT': 'other',
    'LOAN_PAYMENTS': 'utilities',
    'GOVERNMENT_AND_NON_PROFIT': 'other',
    'GENERAL_SERVICES': 'other',
    # Legacy category list values (normalized to uppercase with underscores)
    'FOOD_AND_DINING': 'food',
    'RESTAURANTS': 'food',
    'COFFEE_SHOP': 'food',
    'FAST_FOOD': 'food',
    'AIRLINES_AND_AVIATION_SERVICES': 'travel',
    'CAR_SERVICE': 'travel',
    'TAXI': 'travel',
    'ARTS_AND_ENTERTAINMENT': 'entertainment',
    'MOVIES_AND_DVDS': 'entertainment',
    'GYMS_AND_FITNESS_CENTERS': 'fitness',
    'SPORTS': 'fitness',
    'SHOPPING': 'shopping',
    'CLOTHING_AND_ACCESSORIES': 'shopping',
    'ELECTRONICS': 'shopping',
    'UTILITIES': 'utilities',
    'PAYROLL': 'income',
    'DEPOSIT': 'income',
}


def _get_plaid_client():
    """
    Create and return a configured Plaid API client.

    LEARNING — Why a helper function?
      The client setup is 5 lines of boilerplate. Extracting it means each
      view just calls _get_plaid_client() instead of repeating the setup.
      This also makes it easy to swap sandbox → production in one place.
    """
    env_str = getattr(settings, 'PLAID_ENV', 'sandbox')
    host = plaid.Environment.Production if env_str == 'production' else plaid.Environment.Sandbox

    configuration = plaid.Configuration(
        host=host,
        api_key={
            'clientId': settings.PLAID_CLIENT_ID,
            'secret': settings.PLAID_SECRET,
        }
    )
    api_client = plaid.ApiClient(configuration)
    return plaid_api.PlaidApi(api_client)


def _map_category(txn):
    """
    Map a Plaid transaction object to one of our app's category codes.

    Tries personal_finance_category.primary first (newer Plaid API),
    then falls back to the legacy category list.
    """
    # Try newer personal_finance_category first
    pfc = getattr(txn, 'personal_finance_category', None)
    if pfc:
        primary = getattr(pfc, 'primary', '').upper()
        if primary in PLAID_CATEGORY_MAP:
            return PLAID_CATEGORY_MAP[primary]

    # Fall back to legacy category list
    legacy_cats = getattr(txn, 'category', None) or []
    for cat in legacy_cats:
        normalized = cat.upper().replace(' ', '_').replace('&', 'AND').replace(',', '')
        if normalized in PLAID_CATEGORY_MAP:
            return PLAID_CATEGORY_MAP[normalized]

    return 'other'


# ---------------------------------------------------------------------------
# Views
# ---------------------------------------------------------------------------

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_link_token(request):
    """
    POST /api/plaid/create-link-token/

    Creates a short-lived Plaid link_token that the frontend uses to
    initialize the Plaid Link popup. The token is tied to this user's ID
    so Plaid knows which user is connecting.

    LEARNING — Why does this need a server call?
      The link_token is created server-side so we can attach the user's ID
      to it. Plaid uses this to associate the bank connection with the right
      user in their system. Creating it from the frontend would expose your
      Plaid secret key.
    """
    try:
        client = _get_plaid_client()
        plaid_request = LinkTokenCreateRequest(
            products=[Products('transactions')],
            client_name='Budget Tracker',
            country_codes=[CountryCode('US')],
            language='en',
            user=LinkTokenCreateRequestUser(client_user_id=str(request.user.id))
        )
        response = client.link_token_create(plaid_request)
        return Response({'link_token': response['link_token']})
    except Exception as e:
        print(f'[Plaid create_link_token error] {type(e).__name__}: {e}')
        return Response({'error': 'Failed to create link token.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def exchange_token(request):
    """
    POST /api/plaid/exchange-token/
    Body: { public_token, institution_name }

    Exchanges the one-time public_token (from Plaid Link) for a permanent
    access_token. Stores the access_token in PlaidItem — the frontend
    never sees it.

    Also fetches account details (name, last 4 digits, type) to display.

    LEARNING — Why exchange? Why not use public_token directly?
      The public_token is temporary (30 min expiry) and only meant for
      this exchange step. The access_token is permanent and is what you
      use to pull transactions. The exchange step is a security handoff —
      your server gets the permanent credential, not the browser.
    """
    public_token = request.data.get('public_token')
    institution_name = request.data.get('institution_name', '')

    if not public_token:
        return Response({'error': 'public_token required.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        client = _get_plaid_client()

        # Exchange public_token → access_token
        exchange_request = ItemPublicTokenExchangeRequest(public_token=public_token)
        exchange_response = client.item_public_token_exchange(exchange_request)
        access_token = exchange_response['access_token']
        item_id = exchange_response['item_id']

        # Fetch account details to display in the UI
        accounts_request = AccountsGetRequest(access_token=access_token)
        accounts_response = client.accounts_get(accounts_request)
        accounts = [
            {
                'account_id': a['account_id'],
                'name': a['name'],
                'mask': a['mask'],
                'type': str(a['type']),
            }
            for a in accounts_response['accounts']
        ]

        # Save (or update if re-linking the same bank)
        item, created = PlaidItem.objects.update_or_create(
            item_id=item_id,
            defaults={
                'user': request.user,
                'access_token': access_token,
                'institution_name': institution_name,
                'accounts': accounts,
                'cursor': '',  # Reset cursor on re-link
            }
        )

        serializer = PlaidItemSerializer(item)
        http_status = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response(serializer.data, status=http_status)

    except Exception as e:
        print(f'[Plaid exchange_token error] {type(e).__name__}: {e}')
        return Response({'error': 'Failed to connect bank account.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_items(request):
    """
    GET /api/plaid/items/

    Returns all connected bank accounts for the current user.
    Does NOT include access_token (excluded by serializer).
    """
    items = PlaidItem.objects.filter(user=request.user)
    serializer = PlaidItemSerializer(items, many=True)
    return Response(serializer.data)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def remove_item(request, item_pk):
    """
    DELETE /api/plaid/items/<id>/remove/

    Disconnects a bank account. Deletes the PlaidItem (and thus the
    access_token). Does NOT delete already-synced transactions.
    """
    try:
        item = PlaidItem.objects.get(pk=item_pk, user=request.user)
    except PlaidItem.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    item.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def sync_transactions(request):
    """
    POST /api/plaid/sync/
    Body: { item_id: <int> }  (optional — omit to sync ALL connected banks)

    Pulls new/modified transactions from Plaid and saves them to the
    Transaction table. Already-imported transactions are skipped
    (identified by plaid_transaction_id).

    Returns: { synced: <count>, message: "..." }

    LEARNING — Cursor-based pagination:
      Plaid's transactions/sync uses a cursor. Each call returns only
      changes since the last cursor. We store the new cursor in PlaidItem
      so the next sync only fetches what's new. Very efficient!
    """
    item_pk = request.data.get('item_id')

    if item_pk:
        items = PlaidItem.objects.filter(pk=item_pk, user=request.user)
    else:
        items = PlaidItem.objects.filter(user=request.user)

    if not items.exists():
        return Response({'error': 'No connected banks found.'}, status=status.HTTP_404_NOT_FOUND)

    try:
        client = _get_plaid_client()
        total_added = 0

        for item in items:
            added_count = _sync_item(client, item, request.user)
            total_added += added_count

        msg = f'Synced {total_added} new transaction{"s" if total_added != 1 else ""}.'
        return Response({'synced': total_added, 'message': msg})

    except Exception as e:
        print(f'[Plaid sync error] {type(e).__name__}: {e}')
        return Response({'error': 'Sync failed. Please try again.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def _sync_item(client, item, user):
    """
    Fetches all new transactions for one PlaidItem and saves them.

    LEARNING — Pagination with has_more:
      Plaid may not return all transactions in a single response.
      We keep calling until has_more is False. Each iteration advances
      the cursor. At the end we save the final cursor for next time.
    """
    added_txns = []
    cursor = item.cursor

    # Paginate through all new transactions
    while True:
        kwargs = {'access_token': item.access_token}
        if cursor:
            kwargs['cursor'] = cursor
        sync_request = TransactionsSyncRequest(**kwargs)
        response = client.transactions_sync(sync_request)

        added_txns.extend(response['added'])
        cursor = response['next_cursor']

        if not response['has_more']:
            break

    # Save new transactions to the database
    count = 0
    for txn in added_txns:
        plaid_id = txn['transaction_id']

        # Skip if already imported (idempotent sync)
        if Transaction.objects.filter(plaid_transaction_id=plaid_id).exists():
            continue

        amount = float(txn['amount'])

        # Plaid sign convention: positive = debit (expense), negative = credit (income)
        if amount < 0:
            category = 'income'
            amount = abs(amount)
        else:
            category = _map_category(txn)

        Transaction.objects.create(
            user=user,
            title=txn['name'],
            amount=round(amount, 2),
            category=category,
            date=txn['date'],
            description='Imported from bank',
            plaid_transaction_id=plaid_id,
        )
        count += 1

    # Save the updated cursor so the next sync only fetches new data
    item.cursor = cursor
    item.last_synced = timezone.now()
    item.save(update_fields=['cursor', 'last_synced'])

    return count
