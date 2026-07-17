# Hosting GoRental — Step by Step (Render.com)

This guide deploys your site to the internet with a real, persistent PostgreSQL database — for
free, using [Render](https://render.com). The project already contains everything Render needs
(`Procfile`, `requirements.txt`, `runtime.txt`).

You do **not** need to touch any code to deploy — just follow these steps.

---

## 1. Put your project on GitHub

Render deploys from a GitHub repository.

1. Create a free GitHub account if you don't have one: https://github.com/signup
2. Create a new repository (e.g. `gorental`).
3. Upload this whole `gorental` folder to it. Easiest way if you're not comfortable with git commands:
   - Go to your new repo → **Add file → Upload files** → drag in everything inside the `gorental` folder.
   - Make sure `db.sqlite3` and `media/` are **not** uploaded (they're already in `.gitignore` if you use git directly — if uploading manually, just skip those two).

---

## 2. Create a Render account

Go to https://render.com and sign up (you can sign up with your GitHub account directly — this
also makes connecting your repo automatic).

---

## 3. Create the PostgreSQL database first

1. In the Render dashboard, click **New → PostgreSQL**.
2. Give it a name, e.g. `gorental-db`. Choose the **Free** plan.
3. Click **Create Database**.
4. Once it's ready, open it and copy the **Internal Database URL** (starts with `postgres://...`).
   Keep this tab open — you'll paste this in step 5.

---

## 4. Create the Web Service

1. In the Render dashboard, click **New → Web Service**.
2. Connect your GitHub account and select your `gorental` repository.
3. Fill in:
   - **Name:** `gorental` (this becomes part of your URL: `gorental.onrender.com`)
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt && python manage.py collectstatic --noinput`
   - **Start Command:** `gunicorn gorental_project.wsgi`
   - **Plan:** Free

Don't click "Create" yet — first add the environment variables in the next step.

---

## 5. Add environment variables

Still on the Web Service setup page, scroll to **Environment Variables** and add:

| Key | Value |
|---|---|
| `SECRET_KEY` | any long random string — e.g. generate one at https://djecrety.ir |
| `DEBUG` | `False` |
| `ALLOWED_HOSTS` | `gorental.onrender.com` (use the exact name you picked in step 4) |
| `CSRF_TRUSTED_ORIGINS` | `https://gorental.onrender.com` |
| `DATABASE_URL` | paste the **Internal Database URL** you copied in step 3 |

Now click **Create Web Service**. Render will install dependencies, run the release command
(`python manage.py migrate` — this is already set in the `Procfile`), and start the app.

This first deploy takes a few minutes. Watch the **Logs** tab — when you see
`Starting gunicorn`, your site is live at `https://gorental.onrender.com`.

---

## 6. Create your admin account on the live site

Locally, `createsuperuser` needs terminal access — Render's free plan doesn't give you an
interactive shell by default, so use Render's **Shell** tab (under your Web Service) instead:

```bash
python manage.py createsuperuser
```

Then also seed the sample data if you want the demo vehicles/brands to show up immediately:

```bash
python manage.py seed_data
```

---

## 7. Add real vehicle photos

Log in at `https://gorental.onrender.com/admin/` with the superuser you just created, and either:

- Upload real images per vehicle (stored in `/media/` — note: on Render's **free** plan, uploaded
  files are wiped on every redeploy, since the free tier has no persistent disk). For real vehicle
  photos that need to survive redeploys, either:
  - Upgrade to a Render paid plan with a **persistent disk**, or
  - Use image URLs instead (paste a link in the vehicle image's **Image URL** field) hosted on a
    free image host or your own cloud storage (e.g. Cloudinary, AWS S3, ImgBB).

---

## 8. Point your own domain (optional)

If you buy a domain (e.g. from a Nepali registrar or Namecheap):

1. In Render, go to your Web Service → **Settings → Custom Domain** → add your domain.
2. Render gives you a CNAME/A record to add at your domain registrar's DNS settings.
3. Once DNS propagates (can take a few hours), update `ALLOWED_HOSTS` and
   `CSRF_TRUSTED_ORIGINS` environment variables to include your new domain, and redeploy.

---

## Alternative: Railway.app

If Render's free tier sleeps your app when idle and that bothers you, [Railway](https://railway.app)
works almost identically — same `Procfile`, same `DATABASE_URL` pattern, same environment
variables. Steps are nearly identical: create a PostgreSQL plugin, create a service from your
GitHub repo, add the same environment variables, deploy.

---

## Checking it worked

- Visit your live URL — homepage should load with vehicles, images, and the color theme.
- Register a new account, log in, book a vehicle.
- Log into `/admin/` (or `/vehicles/dashboard/` for the staff report) — the booking you just made
  should already be there. No extra step needed: the admin panel always reads live from whatever
  database `DATABASE_URL` points to, so anything saved on the live site appears in the admin panel
  immediately.
