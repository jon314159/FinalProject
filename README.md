# Calculator API

A FastAPI calculator with a browser interface, PostgreSQL persistence, JWT authentication, Alembic migrations, and Docker-based delivery.

## Features

- Registration and login with bcrypt password hashing
- Access and refresh JWTs with separate signing secrets
- User-scoped calculation history
- Addition, subtraction, multiplication, division, and modulus
- Create, list, view, update, and delete operations
- PostgreSQL in Docker and isolated SQLite tests by default
- Unit, integration, and Playwright end-to-end tests
- Dependency and container vulnerability checks in CI

## Quick start with Docker

Requirements: Docker Desktop or Docker Engine with Compose.

```bash
docker compose up --build
```

Once the services are healthy:

- App: <http://localhost:8000>
- Swagger UI: <http://localhost:8000/docs>
- ReDoc: <http://localhost:8000/redoc>
- pgAdmin: <http://localhost:5050>

The local pgAdmin login is `admin@example.com` / `admin`. These development credentials must not be used for a public deployment.

Stop the stack with:

```bash
docker compose down
```

Add `-v` only when you intentionally want to delete the local database volumes.

## Local development

Python 3.13 is used by CI and the production image.

```bash
python -m venv .venv
```

Activate the environment:

```bash
# macOS or Linux
source .venv/bin/activate

# Windows PowerShell
.venv\Scripts\Activate.ps1
```

Install the development dependencies:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
```

Set the application configuration. PowerShell uses `$env:NAME="value"`; the example below uses POSIX shell syntax.

```bash
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/fastapi_db"
export JWT_SECRET_KEY="replace-with-a-random-secret-at-least-32-characters"
export JWT_REFRESH_SECRET_KEY="replace-with-another-random-secret-at-least-32-characters"
```

Apply migrations and start the server:

```bash
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

## Tests

Unit and integration tests use an isolated in-memory SQLite database unless `TEST_DATABASE_URL` is explicitly set. They do not fall back to `DATABASE_URL`.

```bash
pytest tests/unit tests/integration
```

To run the same tests against PostgreSQL:

```bash
export TEST_DATABASE_URL="postgresql://postgres:postgres@localhost:5432/fastapi_test_db"
pytest tests/unit tests/integration
```

Install Chromium and run the end-to-end suite:

```bash
playwright install chromium
pytest tests/e2e --e2e
```

Audit the complete dependency set:

```bash
python -m pip_audit -r requirements-dev.txt
```

## API

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/auth/register` | Register an account |
| `POST` | `/auth/login` | Return access and refresh tokens |
| `POST` | `/auth/token` | OAuth2 form login |
| `POST` | `/auth/refresh` | Exchange a refresh token for a fresh pair |
| `GET` | `/auth/me` | Return the current database user |
| `POST` | `/calculations` | Create a calculation |
| `GET` | `/calculations` | List the current user's calculations |
| `GET` | `/calculations/{id}` | View one calculation |
| `PUT` | `/calculations/{id}` | Update a calculation's inputs |
| `DELETE` | `/calculations/{id}` | Delete a calculation |
| `GET` | `/health` | Process health check |
| `GET` | `/health/db` | Database health check |

Protected endpoints require `Authorization: Bearer <access-token>`. Resource queries are scoped to the authenticated user's database ID.

Example calculation request:

```json
{
  "type": "addition",
  "inputs": [10.5, 3, 2]
}
```

## Migrations

```bash
alembic upgrade head
alembic downgrade -1
alembic revision --autogenerate -m "describe the change"
alembic check
```

The Docker Compose `migrate` service applies migrations before the development web service starts. The production image also applies pending migrations before launching Uvicorn.

## Container image

The CI workflow publishes successful `main` builds to:

```text
jonathancapalbo1/finalproject:latest
jonathancapalbo1/finalproject:<git-sha>
```

For a standalone container, point `DATABASE_URL` to an accessible PostgreSQL server and supply unique JWT secrets:

```bash
docker run --rm -p 8000:8000 \
  -e DATABASE_URL="postgresql://postgres:postgres@host.docker.internal:5432/fastapi_db" \
  -e JWT_SECRET_KEY="replace-with-a-random-secret-at-least-32-characters" \
  -e JWT_REFRESH_SECRET_KEY="replace-with-another-random-secret-at-least-32-characters" \
  jonathancapalbo1/finalproject:latest
```

## Security notes

- Never commit `.env` or production secrets.
- Use separate, randomly generated access and refresh signing keys.
- Configure `CORS_ORIGINS` for the deployed frontend rather than allowing arbitrary origins.
- The bundled browser UI stores tokens in browser storage and is intended as a project interface. A public production frontend should use hardened cookie and CSRF controls.
