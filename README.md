# GoRental – Vehicle Rental Management System

GoRental is a Django-based vehicle rental platform designed for the Nepali market. Users can browse vehicles, check availability, calculate rental costs, and make bookings online.

## Features

* User registration and login
* User profile management
* Vehicle browsing and filtering
* Vehicle details and availability
* Online vehicle booking
* Automatic rental price calculation
* Customer booking history
* Staff dashboard
* Django admin panel
* Vehicle, brand, destination, and booking management
* eSewa advance payment integration
* Password reset and change password
* Responsive design for desktop and mobile

## Tech Stack

* **Backend:** Django 6, Python
* **Frontend:** HTML, Tailwind CSS, JavaScript
* **Database:** SQLite (development), PostgreSQL (production)
* **Payment:** eSewa
* **Version Control:** Git & GitHub
* **Deployment:** Render

## Project Structure

```text
GoRental/
├── accounts/
├── core/
├── vehicles/
├── gorental_project/
├── templates/
├── static/
├── media/
├── manage.py
├── requirements.txt
└── README.md
```

## Installation

```bash
git clone YOUR_REPOSITORY_URL
cd GoRental

python -m venv venv
venv\Scripts\activate

pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open:

```text
http://127.0.0.1:8000/
```

## Environment Variables

Sensitive information such as passwords, secret keys, database credentials, and payment credentials should be stored in environment variables and **not committed to GitHub**.

## Deployment

The project is configured for deployment with Django, Gunicorn, PostgreSQL, and Render.
