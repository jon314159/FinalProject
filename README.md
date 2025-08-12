```markdown
# 📐 Calculator API

A FastAPI-based calculator service with **user authentication**, **PostgreSQL** database, and **JWT token-based security**.  
It supports basic and advanced calculations, securely stores user history, and provides a modern developer experience with CI/CD, Docker, and Alembic migrations.

---

## ✨ Features

- **User registration & login** (JWT authentication)
- **Secure password hashing** with bcrypt
- **Access & refresh token system**
- **Create, read, update, and delete** calculation history
- **Supports multiple calculation types** (basic arithmetic, advanced operations, etc.)
- **Search & filter** past calculations
- **PostgreSQL** database with Alembic migrations
- **Fully containerized** with Docker & Docker Compose
- **pgAdmin** for easy DB management
- **CI/CD pipeline** with tests, vulnerability scans, and Docker Hub deployments

---

## 📡 API Endpoints

When running locally, the API documentation is available at:  
**Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)  
**ReDoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)

**Example Routes:**
- `POST /auth/register` → Create a new user
- `POST /auth/login` → Get access & refresh tokens
- `POST /calculations` → Perform a calculation and store the result
- `GET /calculations` → Retrieve authenticated user's calculations
- `GET /calculations/{id}` → Get a specific calculation
- `DELETE /calculations/{id}` → Remove a calculation

---

## 🚀 Run with Docker Compose

**Requirements:**
- Docker
- Docker Compose

```

docker compose up --build

```

**Services:**
- **API:** http://localhost:8000  
- **Swagger UI:** http://localhost:8000/docs  
- **ReDoc:** http://localhost:8000/redoc  
- **pgAdmin:** http://localhost:5050 (email: `admin@example.com`, password: `admin`)  

**Stop and remove:**
```

docker compose down
docker compose down -v   # also remove DB data

```

---

## 🖥 Run without Docker

**1. Start PostgreSQL** and create:
- `fastapi_db`
- `fastapi_test_db`

**2. Set environment variables:**
```

export DATABASE\_URL="postgresql://postgres\:postgres\@localhost:5432/fastapi\_db"
export TEST\_DATABASE\_URL="postgresql://postgres\:postgres\@localhost:5432/fastapi\_test\_db"
export JWT\_SECRET\_KEY="replace-with-32-chars-min"
export JWT\_REFRESH\_SECRET\_KEY="replace-with-32-chars-min"

```

**3. Install dependencies:**
```

python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt

```

**4. Run Alembic migrations:**
```

alembic upgrade head

```

**5. Start the API:**
```

uvicorn app.main\:app --reload --port 8000

```

---

## 🧪 Run Tests

### Inside Docker
```

docker compose up -d
docker compose exec web pytest -q

```

**With coverage:**
```

docker compose exec web coverage run -m pytest
docker compose exec web coverage report -m

```

### On Host
```

export TEST\_DATABASE\_URL="postgresql://postgres\:postgres\@localhost:5432/fastapi\_test\_db"
pytest -q

```

**Playwright setup (for e2e tests):**
```

playwright install
pytest tests/e2e/

```

---

## 🔄 CI/CD Pipeline

- Spins up PostgreSQL in GitHub Actions
- Installs Python dependencies and Playwright
- Runs:
  - Unit tests (`tests/unit/`)
  - Integration tests (`tests/integration/`)
  - E2E tests (`tests/e2e/`)
- Builds Docker image
- Scans with **Trivy** (fails on HIGH/CRITICAL vulnerabilities)
- Pushes multi-arch image to Docker Hub on `main` branch

---

## 📦 Docker Hub Repository

**[jonathancapalbo1/finalproject](https://hub.docker.com/r/jonathancapalbo1/finalproject)**

**Pull & Run:**
```

docker pull jonathancapalbo1/finalproject\:latest
docker run -p 8000:8000&#x20;
-e DATABASE\_URL="postgresql://postgres\:postgres\@host.docker.internal:5432/fastapi\_db"&#x20;
-e JWT\_SECRET\_KEY="replace-with-32-chars-min"&#x20;
-e JWT\_REFRESH\_SECRET\_KEY="replace-with-32-chars-min"&#x20;
jonathancapalbo1/finalproject\:latest

```

---

## 🔧 Common Commands

```

# Apply migrations

docker compose run --rm migrate

# Shell inside container

docker compose exec web bash

# Logs

docker compose logs -f web
docker compose logs -f db

# Create Alembic migration

alembic revision --autogenerate -m "describe changes"
alembic upgrade head

```

---

## ⚠ Security Notes

- Use **strong 32+ character secrets** for JWT keys
- Never commit secrets to GitHub — use env vars or GitHub Secrets
- Run a local Trivy scan:
```

docker build -t app\:test .
trivy image --severity HIGH,CRITICAL --exit-code 1 app\:test

```
```
