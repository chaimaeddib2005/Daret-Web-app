# DARET — Rotating Savings Circle

A web application that digitalizes the traditional Moroccan *daret*. Members contribute a fixed amount each round, and one member receives the full pot. The app handles everything — member management, contribution tracking, payout scheduling, and dispute resolution.

---

## Getting Started

```bash
pip install django
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open your browser at `http://127.0.0.1:8000`

---

## Pages

| URL | Description |
|-----|-------------|
| `/` | Dashboard — your circles and recent activity |
| `/circles/` | All your circles |
| `/circles/new/` | Create a new circle |
| `/circles/<id>/` | Circle detail — members, contributions, schedule, disputes |
| `/finances/` | Your contributions and payouts history |
| `/profile/` | Edit your profile |
| `/admin/` | Admin panel (superuser only) |

---

## How a Circle Works

**1. Forming**
The organizer creates the circle and sets the contribution amount, frequency, max members, and payout order method. Members join via invite token or direct request. The organizer approves or rejects each request.

**2. Starting**
Once members are ready, the organizer clicks "Start Circle". Contributions and a payout are automatically created for round 1. If the payout order is set to *lottery*, it's randomized at this point.

**3. Active**
Each round, all members contribute. The designated recipient receives the full pot. The organizer marks contributions as paid or late, then advances to the next round when ready.

**4. Completed**
After every member has received their payout, the circle is marked as completed.

---

## Payout Order Methods

| Method | How it works |
|--------|--------------|
| Manual | Organizer assigns a position number to each member before starting |
| Lottery | Order is randomized when the circle starts |
| Seniority | Members are ordered by who joined first |

---

## Authentication

Standard Django session authentication. Register at `/register/`, log in at `/login/`. No tokens or API keys needed — the browser handles the session automatically.

---

## Admin Panel

Go to `/admin/` and log in with your superuser credentials. From there you can manage all circles, members, contributions, payouts, disputes, and trust ratings directly.
## Live Demo

[Access the deployed app here](https://daret-app.azurewebsites.net/)
