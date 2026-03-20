# DARET – Rotating Savings Circle (Django REST API)

## Setup & Run

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/auth/register/ | Register new user |
| POST | /api/auth/login/ | Login (get JWT tokens) |
| POST | /api/auth/refresh/ | Refresh access token |
| GET | /api/auth/me/ | My profile |
| GET/POST | /api/circles/ | List / create circles |
| GET/PUT/DELETE | /api/circles/{id}/ | Circle detail |
| POST | /api/circles/{id}/join/ | Request to join |
| POST | /api/invite/{token}/ | Join via invite link |
| POST | /api/circles/{id}/approve/{user_id}/ | Approve member |
| POST | /api/circles/{id}/reject/{user_id}/ | Reject member |
| POST | /api/circles/{id}/start/ | Start the circle |
| POST | /api/circles/{id}/next_round/ | Advance to next round |
| GET | /api/circles/{id}/dashboard/ | Circle dashboard |
| GET | /api/circles/{id}/schedule/ | Payout schedule |
| GET | /api/circles/{id}/history/ | Full contribution history |
| POST | /api/circles/{id}/set-payout-order/{user_id}/{order}/ | Set manual payout order |
| GET/POST | /api/circles/{circle_id}/contributions/ | List / create contributions |
| POST | /api/circles/{circle_id}/contributions/{id}/mark_paid/ | Mark contribution paid |
| POST | /api/circles/{circle_id}/contributions/{id}/mark_late/ | Mark contribution late |
| GET/POST | /api/circles/{circle_id}/disputes/ | List / raise disputes |
| POST | /api/circles/{circle_id}/disputes/{id}/resolve/ | Resolve dispute |
| GET | /api/my/circles/ | My circles |
| GET | /api/my/contributions/ | My contributions |
| GET | /api/my/payouts/ | My payouts |
| GET/POST | /api/ratings/ | Trust ratings |
| Admin | /admin/ | Django admin panel |

## Circle Lifecycle

1. **Forming** – Organizer creates circle, members join and get approved
2. **Active** – Organizer starts the circle; contributions and payouts are generated per round
3. **Next Round** – Organizer advances rounds after each payout
4. **Completed** – All members have received their payout

## Payout Order Methods

- `lottery` – Random order assigned at start
- `seniority` – Order by join date (earliest first)
- `manual` – Organizer sets each member's payout order manually before starting

## Authentication

All endpoints require JWT Bearer token. Get it via `/api/auth/login/` with `username` and `password`.
