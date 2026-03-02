# Budget Tracker — Learning Project

A full-stack web application for tracking monthly budgets, logging transactions, and getting personalized recommendations based on your interests and remaining budget.

**Tech stack:** Django · Django REST Framework · JWT Auth · SQLite · React 18 · Vite · React Router · Recharts

---

## What You'll Learn

| Concept | Where It Appears |
|---|---|
| Django ORM — models, fields, migrations | `backend/*/models.py` |
| REST API design | `backend/*/views.py` and `urls.py` |
| Serializers — validation and data transformation | `backend/*/serializers.py` |
| JWT Authentication | `config/settings.py`, `api/axios.js` |
| CORS | `config/settings.py` |
| React Hooks (useState, useEffect) | All frontend pages |
| Context API (global state) | `context/AuthContext.jsx` |
| Axios Interceptors | `api/axios.js` |
| React Router v6 | `App.jsx` |
| Recharts | `pages/Dashboard.jsx` |
| Protected routes | `App.jsx` |

---

## Project Structure

```
budget-tracker/
├── backend/                  ← Django project
│   ├── manage.py
│   ├── requirements.txt
│   ├── db.sqlite3            ← Created on first migrate
│   ├── config/               ← Project settings & root URLs
│   │   ├── settings.py       ← Main configuration (READ THIS FIRST)
│   │   └── urls.py           ← Root URL router
│   ├── users/                ← User accounts & auth
│   │   ├── models.py         ← Custom User with interests field
│   │   ├── serializers.py    ← Register & profile serializers
│   │   └── views.py          ← Register & profile endpoints
│   ├── budgets/              ← Monthly budget amounts
│   │   ├── models.py
│   │   └── views.py          ← GET/POST current budget
│   ├── transactions/         ← Expense/income tracking
│   │   ├── models.py
│   │   └── views.py          ← CRUD + stats endpoint
│   └── recommendations/      ← Recommendation engine
│       ├── engine.py         ← Pure business logic (no HTTP)
│       └── views.py          ← Calls engine, returns JSON
│
└── frontend/                 ← React + Vite project
    ├── package.json
    ├── vite.config.js        ← Dev server + proxy to Django
    ├── src/
    │   ├── api/
    │   │   └── axios.js      ← Axios instance with JWT interceptor
    │   ├── context/
    │   │   └── AuthContext.jsx ← Global auth state
    │   ├── pages/
    │   │   ├── Login.jsx
    │   │   ├── Register.jsx
    │   │   ├── Dashboard.jsx    ← Budget + chart + recent txs
    │   │   ├── Transactions.jsx ← Add/delete transactions
    │   │   └── Recommendations.jsx ← Personalized suggestions
    │   ├── components/
    │   │   └── Navbar.jsx
    │   ├── App.jsx           ← Router + protected routes
    │   ├── main.jsx          ← Entry point
    │   └── index.css         ← Global styles + CSS variables
```

---

## Setup & Running

### Prerequisites
- Python 3.10+
- Node.js 18+
- pip and npm

---

### Backend Setup

```bash
# 1. Navigate to the backend folder
cd budget-tracker/backend

# 2. Create a virtual environment (isolates Python dependencies)
python -m venv venv

# 3. Activate it
# On Mac/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Create the database tables
#    Django reads your models.py files and generates SQL to create tables.
#    makemigrations creates the migration files; migrate applies them.
python manage.py makemigrations
python manage.py migrate

# 6. (Optional) Create a superuser to access the admin panel at /admin/
python manage.py createsuperuser

# 7. Start the development server (runs on port 8000)
python manage.py runserver
```

The API is now running at `http://localhost:8000`

---

### Frontend Setup

Open a **second terminal**:

```bash
# 1. Navigate to the frontend folder
cd budget-tracker/frontend

# 2. Install Node dependencies
npm install

# 3. Start the development server (runs on port 5173)
npm run dev
```

Open your browser to `http://localhost:5173`

---

## API Endpoints

| Method | URL | Auth? | Description |
|--------|-----|-------|-------------|
| POST | `/api/users/register/` | No | Create account |
| POST | `/api/token/` | No | Login (returns JWT tokens) |
| POST | `/api/token/refresh/` | No | Refresh access token |
| GET | `/api/users/profile/` | Yes | Get user profile |
| PATCH | `/api/users/profile/` | Yes | Update profile (interests) |
| GET | `/api/budgets/current/` | Yes | Get current month budget |
| POST | `/api/budgets/current/` | Yes | Set current month budget |
| GET | `/api/transactions/` | Yes | List transactions |
| POST | `/api/transactions/` | Yes | Add transaction |
| DELETE | `/api/transactions/{id}/` | Yes | Delete transaction |
| GET | `/api/transactions/stats/` | Yes | Spending stats by category |
| GET | `/api/recommendations/` | Yes | Personalized recommendations |

---

## Key Concepts Explained

### How JWT Authentication Works

```
1. POST /api/token/  { username, password }
   ← { access: "eyJ...", refresh: "eyJ..." }

2. Every subsequent request:
   GET /api/transactions/
   Authorization: Bearer eyJ...

3. After 1 hour, access token expires:
   ← 401 Unauthorized

4. Axios interceptor automatically:
   POST /api/token/refresh/  { refresh: "eyJ..." }
   ← { access: "new_eyJ..." }
   → Retries the original request with new token

5. If refresh also fails → logout
```

### Django ORM Basics

```python
# CREATE
Transaction.objects.create(user=user, title="Lunch", amount=15.50)

# READ (all)
Transaction.objects.all()

# READ (filtered)
Transaction.objects.filter(user=user, date__month=3)

# READ (single)
Transaction.objects.get(id=5)  # Raises DoesNotExist if not found

# UPDATE
tx = Transaction.objects.get(id=5)
tx.amount = 20.00
tx.save()

# DELETE
Transaction.objects.filter(id=5).delete()

# AGGREGATE
Transaction.objects.filter(user=user).aggregate(total=Sum('amount'))
# → { 'total': Decimal('834.50') }
```

### React Data Fetching Pattern

```jsx
const [data, setData] = useState(null)
const [loading, setLoading] = useState(true)
const [error, setError] = useState('')

useEffect(() => {
  api.get('/some-endpoint/')
    .then(({ data }) => setData(data))
    .catch(() => setError('Something went wrong'))
    .finally(() => setLoading(false))
}, [])  // [] = run once on mount
```

---

## Extending This Project

Once comfortable, try adding:

1. **Edit transactions** — Add a PUT endpoint and an edit form in the UI
2. **Multiple months chart** — Show a bar chart of spending across 6 months
3. **Budget categories** — Set separate budgets per category (food, entertainment, etc.)
4. **Export to CSV** — Add a Django view that returns a CSV file download
5. **PostgreSQL** — Swap SQLite for PostgreSQL (change the `DATABASES` setting)
6. **Deployment** — Deploy Django on Railway/Render and React on Vercel
