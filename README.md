````md
## Reset Docker

```bash
docker compose down
docker compose down -v   # also remove DB data
````

## Set Environment Variables (host)

```bash
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/fastapi_db"
export TEST_DATABASE_URL="postgresql://postgres:postgres@localhost:5432/fastapi_test_db"
export JWT_SECRET_KEY="replace-with-32-chars-min"
export JWT_REFRESH_SECRET_KEY="replace-with-32-chars-min"
```

## Create and Activate Virtualenv

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

## Apply Alembic Migrations

```bash
alembic upgrade head
```

## Run FastAPI Locally

```bash
uvicorn app.main:app --reload --port 8000
```

## Start Docker Stack

```bash
docker compose up -d
```

## Run Tests in Docker

```bash
docker compose exec web pytest -q
```

## Run Coverage in Docker

```bash
docker compose exec web coverage run -m pytest
docker compose exec web coverage report -m
```

## Run Tests on Host

```bash
export TEST_DATABASE_URL="postgresql://postgres:postgres@localhost:5432/fastapi_test_db"
pytest -q
```

## Install Playwright (for e2e)

```bash
playwright install
pytest tests/e2e/
```

## Pull Image From Docker Hub

```bash
docker pull jonathancapalol/finalproject:latest
```

## Run Image From Docker Hub

```bash
docker run -p 8000:8000 \
  -e DATABASE_URL="postgresql://postgres:postgres@host.docker.internal:5432/fastapi_db" \
  -e JWT_SECRET_KEY="replace-with-32-chars-min" \
  -e JWT_REFRESH_SECRET_KEY="replace-with-32-chars-min" \
  jonathancapalol/finalproject:latest
```

## Open Shell Inside Container

```bash
docker compose exec web bash
```

## View Logs

```bash
docker compose logs -f web
docker compose logs -f db
```

## Create New Alembic Revision

```bash
alembic revision --autogenerate -m "describe change"
```

## Upgrade Database to Head

```bash
alembic upgrade head
```

## Build Image Locally

```bash
docker build -t finalproject:latest .
```

## Run Local Image

```bash
docker run -p 8000:8000 finalproject:latest
```

## Security Notes (copy, then edit)

```bash
# Use strong 32+ char secrets
# Never commit .env files
# Avoid echoing secrets in CI logs
```

```
```
