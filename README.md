# GoRental — Travel Vehicle Management System (TVMS)

A full vehicle rental web platform built for the Nepali market: browse vehicles by brand, check
real-time availability, calculate trip cost instantly based on days and destination, and book online
after registering an account. Includes a staff-only dashboard for tracking every booking and flagging
regular vs. new customers.

## Tech Stack

- **Backend:** Django 6 (Python)
- **Frontend:** HTML, Tailwind CSS (via CDN), vanilla JavaScript
- **Database:** SQLite (default — swap to PostgreSQL/MySQL for production, see below)
- **Auth:** Django's built-in authentication, extended with a `Profile` model for phone numbers

## Color Palette (as specified)

| Use                      | Color      | Hex       |
|---------------------------|------------|-----------|
| Primary buttons, header   | Deep Blue  | `#1D4ED8` |
| Accent buttons, highlights| Teal       | `#0D9488` |
| Background                | Soft White | `#F8FAFC` |
| Cards, sections            | Light Blue | `#E0F2FE` |
| Text                      | Dark Gray  | `#111827` |

These are wired into `static/css/custom.css` as CSS variables and into Tailwind's config in `templates/base.html`.

---

## Project Structure

```
gorental/
├── manage.py
├── gorental_project/        # Django settings, root urls
├── core/                    # Home, About (with policies), Contact pages
├── accounts/                 # Register, Login, Logout, Profile (phone number)
├── vehicles/                 # Brands, Vehicles, Images, Destinations, Bookings, Admin Dashboard
├── templates/                # All HTML templates (Tailwind CSS classes)
├── static/
│   ├── css/custom.css         # Brand colors + component styles
│   └── js/main.js             # Mobile nav, image carousels, price calculator
└── media/                     # Uploaded vehicle photos (if you upload real files instead of URLs)
```

---

## Features Implemented

### Public Site
- **Home page** — hero section, featured vehicle cards (image carousel with left/right arrows,
  available/booked badge, price per day), "how it works" section.
- **Vehicle Category page** — filter by brand (BYD, Toyota, Hyundai, Suzuki, Tata, Mahindra, Kia,
  Honda, Ford, Nissan seeded as examples), same card + carousel pattern.
- **Vehicle Detail page** — large image carousel (front/side/rear/interior angles), full specs,
  Book Now button.
- **About page** — company mission and full rental policies.
- **Contact page** — working contact form, submissions saved to the database and visible in
  Django admin.

### Accounts
- **Register / Login / Logout** using Django auth, extended with a phone number field.
- Booking is **login-gated**: clicking "Book Now" while logged out redirects to login, then
  back to the booking page after successful login.

### Booking Flow
- Booking form collects **name, phone, email, pickup date, return date, destination**.
- A **live JavaScript price calculator** updates as soon as dates/destination are chosen:
  `total = (vehicle price/day + destination adjustment) × number of days`.
- Destinations can **increase or decrease** the price (e.g. Nagarkot is seeded with a discount,
  Pokhara/Lumbini with a surcharge) — configurable from the admin.
- On submit, the booking is saved with the calculated total and a confirmation page is shown.
- **My Bookings** page lets a logged-in customer see their own booking history.

### Staff-Only Admin Dashboard (`/vehicles/dashboard/`)
Exactly what you asked for — visible only to staff accounts:
- Every booking with full details: customer, phone, email, vehicle, destination, dates, total
  price, advance paid, status, verification state, and booked-on timestamp.
- Each customer is automatically flagged **"Regular Customer"** (2+ bookings) or **"New Customer"**
  (their first booking), with first/last booking dates and a full expandable booking history.
- Search by name, username, email or phone.
- A "Dashboard" link appears in the navbar automatically for any user with `is_staff = True`.
- A **"Verify Bookings in Admin"** button links straight to the enhanced Django admin.

### Admin Panel — Full Access + Booking Verification
The standard Django admin panel (`/admin/`) has been extended specifically for this:
- **Superusers and staff have full add/change/delete access** to every model — vehicles, images,
  brands, destinations, bookings, and payments — with no extra configuration needed.
- The Booking list shows every field an admin needs at a glance: customer, phone, email, vehicle,
  destination, dates, total price, 5% advance amount, eSewa payment status, booking status,
  verification state, and whether the customer is Regular or New.
- **Bulk actions** on the Booking list: *Verify selected bookings* (marks verified + confirmed,
  records who verified it and when), *Remove verification*, *Mark as Confirmed*, *Mark as
  Cancelled*.
- The `status` field is editable directly from the list view (no need to open each booking).
- Each Booking's detail page shows its linked Payment record inline (transaction ID, amount,
  status, eSewa reference code) — read-only, since payment data should only ever be written by
  the payment callback, never edited by hand.

### Advance Payment via eSewa (5%)
After a customer fills in the booking form and the price is calculated, they're required to pay
**5% of the total price upfront** to secure the booking, via **eSewa** (Nepal's digital wallet) —
exactly as requested:

1. Customer submits the booking form → total price is calculated as before.
2. They're shown a summary (total price, 5% advance due now, remaining due on pickup) and
   automatically redirected to eSewa's payment page.
3. After paying, eSewa redirects back to the site with a signed response.
4. The backend verifies the payment two ways before trusting it:
   - Recomputes the **HMAC-SHA256 signature** eSewa sent back and compares it.
   - Independently calls **eSewa's server-side transaction-status API** to confirm the payment
     really went through (protects against a tampered/replayed redirect URL).
5. Once both checks pass, the booking moves from "Awaiting Advance Payment" to "Pending" —
   ready for an admin to **Verify** it in the admin panel.

This project ships with **eSewa's official public sandbox/test credentials** (merchant code
`EPAYTEST`) so you can test the entire flow immediately without a real merchant account. To go
live:
1. Register as a merchant at https://merchant.esewa.com.np to get your real merchant code and
   secret key.
2. Set `ESEWA_MERCHANT_CODE`, `ESEWA_SECRET_KEY`, `ESEWA_PAYMENT_URL`, and
   `ESEWA_STATUS_CHECK_URL` as environment variables (see `.env.example`) — eSewa will give you
   the production URLs when your merchant account is approved.
3. No code changes needed — the integration reads these from environment variables automatically.

---

## Getting Started

```bash
cd gorental
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

python manage.py migrate
python manage.py seed_data      # populates sample brands, 10 vehicles, 30 images, 5 destinations
python manage.py createsuperuser
python manage.py runserver
```

Visit `http://127.0.0.1:8000/`.

### Demo Login Included

This project ships with a working superuser and two demo customers already set up in `db.sqlite3`
so you can see the dashboard populated immediately:

| Role       | Username     | Password     |
|------------|--------------|--------------|
| Staff/Admin| `admin`      | `admin12345` |
| Customer   | `ram_sharma` | *(no bookings login needed — view via dashboard)* |
| Customer   | `sita_gurung`| *(same as above)* |

**Change the admin password before going live**, and delete the demo bookings from
`/admin/vehicles/booking/` once you're ready to launch with real customers.

---

## Replacing Placeholder Images with Real Photos

All seeded vehicle images use `placehold.co` as visual placeholders so the carousel and layout can
be demonstrated immediately. To use your real photos:

1. Go to `/admin/vehicles/vehicle/`, open a vehicle, and under its image inline rows either:
   - Upload a real file in the **Image** field (recommended — stored in `/media/vehicles/`), or
   - Paste a direct image URL in the **Image url** field.
2. Add as many angle rows as you like (Front, Side, Rear, Interior) — the carousel automatically
   picks up every image attached to that vehicle, in the given order.
3. The homepage shows 2 images per featured vehicle by default (first 2 in the carousel); the
   category and detail pages show all images for that vehicle.

To reach your target of 20 images on the homepage and 30 overall, keep 10 featured vehicles with
3 images each (front/side/rear) exactly as seeded — or adjust `VEHICLES` in
`vehicles/management/commands/seed_data.py` to add more.

---

## Adding/Editing Vehicles, Brands & Destinations

Everything is manageable from Django admin (`/admin/`) — no code changes needed:
- **Brands** — add a new brand (e.g. a new car maker) any time; it appears automatically as a
  filter tab on the Vehicle Category page.
- **Vehicles** — set price per day, seats, transmission, fuel type, and toggle **Is available**
  to instantly show "Booked" on the site.
- **Destinations** — set a name and an extra charge per day (use a negative number for a
  discount). These populate the destination dropdown on every booking form automatically.

---

## Going to Production

See **`HOSTING.md`** in this project for a full step-by-step guide to deploying this on Render.com
with a real PostgreSQL database — no code changes needed, everything is already wired up:

- `requirements.txt`, `Procfile`, and `runtime.txt` are ready for deployment.
- The database switches automatically: it uses SQLite locally (no setup needed), and switches to
  PostgreSQL the moment a `DATABASE_URL` environment variable is present (which hosting platforms
  like Render/Railway set automatically when you attach a database).
- `DEBUG`, `SECRET_KEY`, `ALLOWED_HOSTS`, and `CSRF_TRUSTED_ORIGINS` are all read from environment
  variables — copy `.env.example` to `.env` and fill in real values for your deployment.
- Static files are served via WhiteNoise, so no separate static file server is required.

Quick checklist before going live:
1. Set a real `SECRET_KEY` and `DEBUG=False`.
2. Set `ALLOWED_HOSTS` to your real domain.
3. Attach a PostgreSQL database and set `DATABASE_URL`.
4. Run `python manage.py migrate` and `python manage.py createsuperuser` on the live server.
5. Set up email backend (SMTP) if you want contact form / booking confirmations sent by email.

---

## Notes

- All prices are shown in NPR (Nepali Rupees).
- The site is fully responsive — tested down to mobile widths with a collapsible hamburger menu.
- No external icon/image packages are required beyond inline SVGs and the Tailwind CDN.
