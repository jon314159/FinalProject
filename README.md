

---

````markdown
# 📐 Calculator API

A FastAPI-based calculator service with **user authentication**, **PostgreSQL** database, and **JWT token-based security**.  
It supports basic arithmetic and advanced calculations, securely stores user history, and provides a modern developer experience with CI/CD, Docker, and Alembic migrations.

---

## ✨ Features

- User registration & login (JWT authentication)
- Secure password hashing with bcrypt
- Access & refresh token system
- CRUD operations on calculation history
- Supported calculation types:
  - addition
  - subtraction
  - multiplication
  - division
  - modulus
- PostgreSQL database with Alembic migrations
- Fully containerized with Docker & Docker Compose
- pgAdmin for DB management
- CI/CD pipeline with tests, security scans, and Docker Hub deployments

---

## 📡 API Endpoints

When running locally:

- Swagger UI → http://localhost:8000/docs  
- ReDoc → http://localhost:8000/redoc  

---

## 📄 API Usage Examples

### 1. Register a User

**Request**
```http
POST /auth/register
Content-Type: application/json
````

```json
{
  "first_name": "John",
  "last_name": "Doe",
  "email": "john.doe@example.com",
  "username": "johndoe",
  "password": "SecurePass123!",
  "confirm_password": "SecurePass123!"
}
```

**Response**

```http
201 Created
```

```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "username": "johndoe",
  "email": "john.doe@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "is_active": true,
  "is_verified": false,
  "created_at": "2025-01-01T00:00:00",
  "updated_at": "2025-01-01T00:00:00"
}
```

---

### 2. Login

**Request**

```http
POST /auth/login
Content-Type: application/json
```

```json
{
  "username": "johndoe",
  "password": "SecurePass123!"
}
```

**Response**

```http
200 OK
```

```json
{
  "access_token": "<JWT_ACCESS_TOKEN>",
  "refresh_token": "<JWT_REFRESH_TOKEN>",
  "token_type": "bearer",
  "expires_at": "2025-01-01T00:00:00",
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "username": "johndoe",
  "email": "john.doe@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "is_active": true,
  "is_verified": false
}
```

---

### 3. Create a Calculation

**Request**

```http
POST /calculations
Authorization: Bearer <JWT_ACCESS_TOKEN>
Content-Type: application/json
```

```json
{
  "type": "addition",
  "inputs": [10.5, 3, 2]
}
```

**Response**

```http
201 Created
```

```json
{
  "id": "123e4567-e89b-12d3-a456-426614174999",
  "type": "addition",
  "inputs": [10.5, 3, 2],
  "result": 15.5,
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "created_at": "2025-01-01T00:00:00",
  "updated_at": "2025-01-01T00:00:00"
}
```

---

### 4. List Calculations

**Request**

```http
GET /calculations
Authorization: Bearer <JWT_ACCESS_TOKEN>
```

**Response**

```http
200 OK
```

```json
[
  {
    "id": "123e4567-e89b-12d3-a456-426614174999",
    "type": "addition",
    "inputs": [10.5, 3, 2],
    "result": 15.5,
    "user_id": "123e4567-e89b-12d3-a456-426614174000",
    "created_at": "2025-01-01T00:00:00",
    "updated_at": "2025-01-01T00:00:00"
  }
]
```

---

### 5. Update a Calculation

**Request**

```http
PUT /calculations/123e4567-e89b-12d3-a456-426614174999
Authorization: Bearer <JWT_ACCESS_TOKEN>
Content-Type: application/json
```

```json
{
  "inputs": [42, 7]
}
```

**Response**

```http
200 OK
```

```json
{
  "id": "123e4567-e89b-12d3-a456-426614174999",
  "type": "addition",
  "inputs": [42, 7],
  "result": 49,
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "created_at": "2025-01-01T00:00:00",
  "updated_at": "2025-01-02T00:00:00"
}
```

---

### 6. Delete a Calculation

**Request**

```http
DELETE /calculations/123e4567-e89b-12d3-a456-426614174999
Authorization: Bearer <JWT_ACCESS_TOKEN>
```

**Response**

```http
204 No Content
```

---

## 🚀 Run with Docker Compose

**Requirements:**

* Docker
* Docker Compose

```
docker compose up --build
```

Services:

* API → [http://localhost:8000](http://localhost:8000)
* Swagger UI → [http://localhost:8000/docs](http://localhost:8000/docs)
* ReDoc → [http://localhost:8000/redoc](http://localhost:8000/redoc)
* pgAdmin → [http://localhost:5050](http://localhost:5050) (email: `admin@example.com`, password: `admin`)

Stop and remove:

```
docker compose down
docker compose down -v
```

---

## 🖥 Run without Docker

**1. Start PostgreSQL** and create:

* `fastapi_db`
* `fastapi_test_db`

**2. Set environment variables:**

```
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/fastapi_db"
export TEST_DATABASE_URL="postgresql://postgres:postgres@localhost:5432/fastapi_test_db"
export JWT_SECRET_KEY="replace-with-32-chars-min"
export JWT_REFRESH_SECRET_KEY="replace-with-32-chars-min"
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
uvicorn app.main:app --reload --port 8000
```

---

## 🧪 Run Tests

**Inside Docker**

```
docker compose up -d
docker compose exec web pytest -q
```

**With coverage**

```
docker compose exec web coverage run -m pytest
docker compose exec web coverage report -m
```

**On Host**

```
export TEST_DATABASE_URL="postgresql://postgres:postgres@localhost:5432/fastapi_test_db"
pytest -q
```

**Playwright setup (for e2e tests)**

```
playwright install
pytest tests/e2e/
```

---

## 📦 Docker Hub

**[jonathancapalbo1/finalproject](https://hub.docker.com/r/jonathancapalbo1/finalproject)**

**Pull & run**

```
docker pull jonathancapalbo1/finalproject:latest
docker run -p 8000:8000 \
  -e DATABASE_URL="postgresql://postgres:postgres@host.docker.internal:5432/fastapi_db" \
  -e JWT_SECRET_KEY="replace-with-32-chars-min" \
  -e JWT_REFRESH_SECRET_KEY="replace-with-32-chars-min" \
  jonathancapalbo1/finalproject:latest
```

---

## 🔧 Common Commands

**Apply migrations**

```
docker compose run --rm migrate
```

**Shell inside container**

```
docker compose exec web bash
```

**Logs**

```
docker compose logs -f web
docker compose logs -f db
```

**Create Alembic migration**

```
alembic revision --autogenerate -m "describe changes"
alembic upgrade head
```

---

## ⚠ Security Notes

* Use strong 32+ character secrets for JWT keys
* Never commit secrets — use env vars or GitHub Secrets
* Run a local Trivy scan:

```
docker build -t app:test .
trivy image --severity HIGH,CRITICAL --exit-code 1 app:test
```
