# AquaWise first deployment: Render + Supabase

This guide deploys the React/Vite frontend to a Render Static Site, the Flask API to a Render Web Service, and a **new, empty** PostgreSQL database to Supabase Free. It does not copy accounts or assessment history from `database/aquawise.db`.

Do not put passwords, database URLs, API keys, or Flask secrets in Git, `render.yaml`, or any `VITE_` variable. Enter secret values only in the relevant Render environment settings or in the hidden PowerShell prompts below.

## Free-plan behavior to expect

- Render Free web services sleep after 15 minutes without requests. The first request after sleep can take about a minute. Their local filesystem is temporary, so AquaWise uses Supabase—not a local SQLite file—for hosted data. Free Render web services have no dashboard shell, SSH, or one-off jobs. [Render Free limitations](https://render.com/docs/free) [Render shell support](https://render.com/docs/ssh)
- Supabase Free can pause a project after a week of low database activity. You may need to restore it before the app can use it again. [Supabase pausing policy](https://supabase.com/docs/guides/platform/free-project-pausing)

These free plans are suitable for a first demo, but they do not provide production-grade uptime or backups.

## 1. Create an empty Supabase database

1. Create a new Supabase project and choose a region reasonably close to your Render service.
2. Set a new database password and keep it private. This is separate from your AquaWise account password.
3. In the Supabase project, open **Connect**, choose **Session pooler**, and copy its URI. The shared session pooler is the IPv4-compatible option available on the Free plan; use the exact host, port, and username Supabase supplies rather than constructing them yourself. [Supabase connection guide](https://supabase.com/docs/guides/database/connecting-to-postgres)
4. The SQLAlchemy driver added for AquaWise is Psycopg 3. Use this form for `DATABASE_URL` (the values in angle brackets are placeholders):

   ```text
   postgresql+psycopg://postgres.<project-ref>:<encoded-password>@<session-pooler-host>:5432/postgres?sslmode=require
   ```

   Supabase's copied URI may begin with `postgresql://`; change only that prefix to `postgresql+psycopg://`. Ensure the URL includes `sslmode=require` (add `?sslmode=require` if it has no query string, or `&sslmode=require` if it already has one). If the password contains reserved URL characters such as `@`, `:`, `/`, `?`, or `#`, URL-encode the password before inserting it. Treat the complete URL as a secret.

Do not run any import or copy command for the local SQLite database. The initialization below creates the schema and initial achievement rows in this new Supabase project only.

## 2. Create the Render Static Site first

The checked-in [`render.yaml`](render.yaml) configures the frontend build, publish directory, and React Router fallback. It defines only the static site; create the API Web Service separately in the next section.

1. In Render, choose **New → Blueprint**, connect the AquaWise repository, and select the branch to deploy. Render reads `render.yaml` and creates the static frontend.
2. When prompted for `VITE_API_URL`, enter a temporary value such as `https://api-not-created.invalid/api`. The frontend can build with this value; replace it with the real backend URL after creating the backend. This variable is public in the built JavaScript bundle, so it must contain only the API URL, never a credential.
3. Note the exact frontend URL Render assigns, for example `https://<your-static-site>.onrender.com`. You will use this exact origin for CORS.

The file's `/*` → `/index.html` rewrite lets direct visits and refreshes of `/dashboard`, `/assessment`, and other React Router paths load the app correctly. Render serves real files such as JavaScript bundles and `robots.txt` directly before applying the rewrite. [Render rewrites](https://render.com/docs/redirects-rewrites)

## 3. Create the Flask Web Service

In Render, choose **New → Web Service**, connect the same repository, and use these settings:

- **Root Directory:** leave blank (the repository root)
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `gunicorn --bind 0.0.0.0:$PORT "app:create_app('production')"`
- **Health Check Path:** `/api/health`
- **Plan:** Free, if you are staying within the free plan

Add these environment variables under the Web Service's settings. Do not add the secret values to `render.yaml` or Git.

| Variable | Value / where it comes from | Required? |
| --- | --- | --- |
| `FLASK_ENV` | `production` | Yes |
| `SECRET_KEY` | A newly generated random secret of at least 32 characters with at least 16 distinct characters, entered in Render's secret environment settings | Yes |
| `DATABASE_URL` | The Supabase session-pooler URL from Step 1, using `postgresql+psycopg://` and `sslmode=require` | Yes |
| `CORS_ALLOWED_ORIGINS` | The exact frontend origin from Step 2, e.g. `https://<your-static-site>.onrender.com`; no path and no trailing slash | Yes |
| `SESSION_COOKIE_SAMESITE` | `None` for separate default Render frontend/backend domains | Yes |
| `AI_API_KEY` or `GEMINI_API_KEY` | Optional AI provider key; keep it only on the backend | No |
| `AI_MODEL` | Optional model name; defaults to `gemini-2.5-flash` | No |
| `PORT` | Supplied by Render; do not set it yourself | No |

The production factory rejects a missing/weak `SECRET_KEY`, missing CORS origin, non-HTTPS origins, and an invalid cookie policy. Keep the origin exact; the backend does not reflect arbitrary browser origins.

## 4. Initialize the fresh database once

The backend health check can pass before tables exist because it tests the database connection with `SELECT 1`. The API's database-backed pages will not work until the schema is initialized.

Render Free does not provide a service shell or one-off commands. Run the existing `init-db` command once from your Windows computer, pointed explicitly at the new Supabase database. This command creates the current model tables and seeds achievements. It does not read or modify the local SQLite records. Do **not** run the V2 migration command for this brand-new database; its current models already include the V2 columns.

Open PowerShell in the AquaWise repository root. Use a Python environment for this repository; create one if you do not already have one, then install the updated requirements:

```powershell
if (-not (Test-Path .venv)) { python -m venv .venv }
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

The following PowerShell block asks for the database URL and the **same** `SECRET_KEY` you entered in Render without echoing either secret. It also checks that the URL is a Supabase session-pooler PostgreSQL URL before calling Flask, so a local SQLite URL is rejected. Set the CORS value to your exact Render frontend URL.

```powershell
function Set-AquaWiseSecret {
    param([string]$Name, [string]$Prompt)
    $secret = Read-Host $Prompt -AsSecureString
    $pointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secret)
    try {
        [Environment]::SetEnvironmentVariable(
            $Name,
            [Runtime.InteropServices.Marshal]::PtrToStringBSTR($pointer),
            'Process'
        )
    } finally {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($pointer)
    }
}

Set-AquaWiseSecret 'DATABASE_URL' 'Paste the Supabase session-pooler URL'
Set-AquaWiseSecret 'SECRET_KEY' 'Paste the production SECRET_KEY from Render'
$env:FLASK_ENV = 'production'
$env:CORS_ALLOWED_ORIGINS = 'https://YOUR-STATIC-SITE.onrender.com'
$env:SESSION_COOKIE_SAMESITE = 'None'

try {
    $databaseUri = [Uri]$env:DATABASE_URL
    if ($databaseUri.Scheme -ne 'postgresql+psycopg' -or -not $databaseUri.Host.EndsWith('.pooler.supabase.com')) {
        throw 'DATABASE_URL must be the Supabase session-pooler PostgreSQL URL. No database was initialized.'
    }
    python -m flask --app 'app:create_app("production")' init-db
} finally {
    Remove-Item Env:DATABASE_URL, Env:SECRET_KEY, Env:FLASK_ENV, Env:CORS_ALLOWED_ORIGINS, Env:SESSION_COOKIE_SAMESITE -ErrorAction SilentlyContinue
}
```

Replace `YOUR-STATIC-SITE` before running the block. Keep the pooler URL's username/host exactly as copied from Supabase; only change the URI scheme as described above. A successful run prints that the database was initialized. If it fails, do not retry against a different database until you have checked the URL host in Supabase's **Connect** panel.

## 5. Point the frontend at the API

After the Web Service is deployed, copy its actual HTTPS URL from Render. In the **Static Site** environment settings, change `VITE_API_URL` to:

```text
https://YOUR-BACKEND.onrender.com/api
```

Save the setting and manually deploy the static site again so Vite builds the URL into the bundle. Keep the `/api` suffix. Local development remains unchanged: if `VITE_API_URL` is unset, the frontend continues to use `http://localhost:5000/api`.

## 6. Cookies, CORS, CSRF, and sign-in

- Flask-Login continues to use a signed session cookie. Production cookies are `Secure` and `HttpOnly`; no frontend token or password gate is added.
- Separate Render domains are different origins. The frontend Axios client already sends credentials and obtains a session-bound CSRF token before state-changing requests. Production CORS must list only the exact frontend origin and must allow credentials and the `X-CSRF-Token` header; the existing Flask configuration does this.
- For the separate Render domains, set `SESSION_COOKIE_SAMESITE=None`. Production already requires HTTPS and sets the Secure flag. `HttpOnly` remains enabled. Do not disable CSRF. Some browsers restrict cross-site cookies; if sign-in does not persist in a particular browser, using custom frontend/API subdomains under a domain you own can provide a same-site topology, where `Lax` may be appropriate. Reconfigure both CORS and cookie settings to match the actual domains.

## 7. Noindex behavior

The page includes `noindex, nofollow` metadata. `frontend/public/robots.txt` allows crawlers to fetch the page so they can read that metadata; robots.txt itself has no standard noindex directive. This discourages indexing but is not access control: anyone with the URL can still open the public frontend. The API's existing login and authorization requirements continue to protect household data.

## 8. Verify the deployment

1. Open `https://YOUR-BACKEND.onrender.com/api/health`. A healthy response reports `"status": "healthy"` and `"database": "connected"`. If PostgreSQL is unavailable, the endpoint now returns HTTP 503 and Render marks the service unhealthy.
2. Open the frontend URL and refresh `/login`, `/dashboard`, and `/assessment`; each should load through the SPA rewrite.
3. Register or log in with a test household account, submit a test assessment, and confirm the dashboard, recommendation history, assistant, and profile load. The database starts empty, so it will not contain your local users or assessments.
4. Keep a separate backup/export plan for data you create online. The free hosting plans can pause or sleep and have service limitations; check the linked provider documentation before relying on them for continuous public use.

The health check verifies the PostgreSQL connection, not that all application tables exist. Initialize the database once before using the app. Do not run `migrate-household-assessment-v2` against the fresh database.
