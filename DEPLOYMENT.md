# AquaWise production deployment notes

This repository does not select a hosting provider. Configure the provider's secrets, persistent disk, HTTPS, port, and static-site routing using the notes below before deployment.

## Backend process

Install the backend dependencies from `requirements.txt`, then start the Flask application factory with a production WSGI server:

```sh
gunicorn --bind 0.0.0.0:$PORT "app:create_app('production')"
```

The platform must provide `PORT`. Gunicorn is a POSIX server; use a Linux production runtime. Do not use Flask's development server in production.

## Required backend settings

- `SECRET_KEY`: generate a unique random secret of at least 32 characters with at least 16 distinct characters. Never use the development or example value. For example, generate one with Python's `secrets.token_hex(32)` and enter it in the hosting provider's secret manager.
- `CORS_ALLOWED_ORIGINS`: comma-separated exact origins, including scheme and port, such as `https://app.example.com`. Do not include a path or trailing slash. Only origins controlled by the deployment should be listed.
- `SESSION_COOKIE_SAMESITE`: choose `Lax` (recommended for same-site deployments such as `app.example.com` and `api.example.com`) or `None` for cross-site domains. `None` requires HTTPS and Secure cookies, which production enables. `Strict` is also accepted but can interfere with external navigation flows.
- `DATABASE_URL`: optional for the default database path; see SQLite storage below.
- `AI_API_KEY` or `GEMINI_API_KEY`: optional server-only AI credentials. These must never be exposed through a `VITE_` variable.
- `AI_MODEL`: optional model selection.

The session and remember cookies are HttpOnly. Production sets their Secure flags. For cross-site `SameSite=None` deployments, retain the CSRF token protection; the React Axios client retrieves a session-bound token from `/api/auth/csrf` and attaches it to state-changing API calls.

## Frontend build and API endpoint

Build from `frontend/` with `npm run build`. The static output is `frontend/dist`. Set `VITE_API_URL` at build time to the backend API prefix, for example `https://api.example.com/api`. The frontend default remains `http://localhost:5000/api` for local development. Vite variables are public in the generated bundle; never put secrets in them.

The frontend uses browser history routing. Configure the chosen static host to rewrite unknown page paths to `/index.html` while still serving existing assets normally. No host-specific fallback file has been added because no hosting platform has been selected.

## SQLite persistence and initialization

SQLite remains supported. The default database is `database/aquawise.db`, a repository-relative path that may not be included in deployment artifacts and is not durable on ephemeral filesystems. Attach a persistent writable disk and set `DATABASE_URL` to a SQLite URI on that disk. For a Linux disk mounted at `/var/lib/aquawise`, for example:

```text
DATABASE_URL=sqlite:////var/lib/aquawise/aquawise.db
```

Create the mount directory with permissions for the app process. Keep SQLite on a single durable disk and avoid horizontally scaling multiple independent application instances against it. Back up the database before schema operations.

Tables are not created automatically at application startup. After setting the production environment, initialize a new database with:

```sh
flask --app 'app:create_app("production")' init-db
```

For an existing database, run this only if its schema predates household assessment V2:

```sh
flask --app 'app:create_app("production")' migrate-household-assessment-v2
```

The migration adds nullable metadata columns and does not remove rows. Confirm the backup and target database path before running it. These commands should be run as a deployment step, not on every server start.

## Hosting decisions still required

Choose the frontend and backend providers/domains, enter exact frontend origin(s), decide whether the domains are same-site or cross-site and set SameSite accordingly, provision HTTPS and a persistent SQLite disk, configure the static SPA rewrite, and establish a backup/restore procedure. Prefer same-site subdomains where practical; browsers or privacy settings may block third-party cookies for truly cross-site deployments even with `SameSite=None`. The repository changes do not deploy the app or verify provider-specific behavior.
