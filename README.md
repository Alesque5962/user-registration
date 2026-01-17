# User Registration API

## Overview

This project implements a **User Registration and Activation API**.

A user can:
1. Register with an email and a password
2. Receive a **4-digit activation code** by email
3. Activate their account using this code and **HTTP Basic Authentication**
4. The activation code is valid for **1 minute only**

---

## Features

- User registration (`/register`)
- Account activation with a 4-digit code (`/activate`)
- Code expiration after 1 minute
- HTTP Basic Authentication for activation
- PostgreSQL database (SQL only, no ORM)
- SMTP service treated as an external dependency (mocked)
- Automatic database and table initialization at startup
- **3-layer architecture** (API, Service, Data)
- Fully dockerized application
- Pytest test suite

---

## Tech Stack

- **Python 3.13**
- **FastAPI** (routing and dependency injection)
- **PostgreSQL 18**
- **psycopg (v3)** — SQL queries only
- **Docker & Docker Compose**
- **Pytest**

---

## Architecture

### 3-Layer Architecture

```
┌──────────────────────────────────┐
│   API Layer (routes, schemas)    │  ← HTTP requests/responses
└──────────────┬───────────────────┘
               │
┌──────────────▼───────────────────┐
│   Service Layer (business logic) │  ← Orchestration, rules
└──────────────┬───────────────────┘
               │
┌──────────────▼───────────────────┐
│   Data Layer (repositories, DB)  │  ← Database access
└──────────────────────────────────┘
```

**Benefits:**
- **Separation of concerns**: Each layer has a single responsibility
- **Testability**: Services can be tested without database or HTTP
- **Maintainability**: Changes are localized to specific layers
- **Reusability**: Business logic can be used in CLI, workers, etc.

---

## Project Structure

```
user-registration/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── api/                        # API layer (routes) 
│   │   ├── __init__.py
│   │   ├── routes/ 
│   │   │   ├── __init__.py
│   │   │   └── users.py
│   │   └── schemas/ 
│   │       ├── __init__.py
│   │       ├── common.py
│   │       └── user.py
│   ├── core/                       # Configuration and utils
│   │   ├── __init__.py
│   │   ├── config.py     
│   │   ├── security.py      
│   │   └── utils.py             
│   ├── data/                       # Data Access Layer 
│   │   ├── __init__.py
│   │   ├── db.py                   
│   │   ├── models/ 
│   │   │   ├── __init__.py
│   │   │   └── user.py
│   │   └── repositories/ 
│   │       ├── __init__.py
│   │       └── user_repository.py
│   └── services/                   # Service layer (business logic)
│       ├── __init__.py
│       ├── activation.py           
│       ├── mailer.py               
│       └── user_service.py         
├── docker/                          
│   ├── docker-compose.yml
│   └── Dockerfile
├── tests/                          
│   ├── conftest.py
│   └── test_user_service.py          
├── .gitignore
├── pyproject.toml              
├── README.md
├── user_registration_api.md
└── uv.lock
```

---

## Database Initialization

At application startup:

1. The API waits for PostgreSQL to be available
2. The database is created if it does not exist
3. A database connection pool is initialized
4. The `users` table is created if it does not exist

Table definition:

```sql
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    password_hash BYTEA NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT FALSE,
    activation_code TEXT,
    activation_expires_at TIMESTAMPTZ
);
```

---

## Running the Application

### With Docker (Recommended)

```bash
docker-compose -f docker/docker-compose.yml up --build
```

The API will be available at:
- **API**: http://localhost:8000
- **Swagger UI**: http://localhost:8000/docs

---

### Local Development with uv

**Prerequisites:**
- Python 3.13+
- PostgreSQL 18
- [uv](https://github.com/astral-sh/uv) package manager

**Setup:**

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync

# Configure environment variables
cat > .env << EOF
DB_HOST=localhost
DB_PORT=5432
DB_NAME=users
DB_USER=postgres
DB_PASSWORD=postgres
EOF

# Run the application
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## API Usage

### Register a user

```bash
curl -X POST "http://localhost:8000/register" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "secret123"}'
```

Response:
```json
{"message": "User created"}
```

The activation code will be printed in the logs:
```
[SMTP] Code d'activation pour user@example.com: 1234
```

---

### Activate the account

```bash
curl -X POST "http://localhost:8000/activate" \
  -H "Content-Type: application/json" \
  -u "user@example.com:secret123" \
  -d '{"code": "1234"}'
```

Response:
```json
{"message": "Account activated"}
```

**Authentication:**
- **Username**: user email
- **Password**: user password

Swagger UI will automatically prompt for credentials using **HTTP Basic Auth**.

---

## Test Suite

The application includes comprehensive test coverage:

### Service Layer Tests (`tests/test_user_service.py`)

**Registration Tests:**
- Successful user registration
- Duplicate email handling

**Activation Tests:**
- Successful activation with valid credentials
- User not found
- Wrong password
- Already activated account
- Expired activation code
- Invalid activation code

### Running Tests

**With Docker:**
```bash
docker-compose -f docker/docker-compose.yml run api pytest # Run the full test suite
docker-compose -f docker/docker-compose.yml run api pytest -v # Run with verbose output
docker-compose -f docker/docker-compose.yml run api pytest tests/test_user_service.py # Run a specific file
docker-compose -f docker/docker-compose.yml run api pytest tests/test_activation.py::test_activate_success # Run a specific test
```

**With uv:**
```bash
uv run pytest # Run the full test suite
uv run pytest -v # Run with verbose output
uv run pytest tests/test_user_service.py # Run a specific file
uv run pytest tests/test_user_service.py::test_register_user_success # Run a specific test
```

---

## Architecture Details

For detailed architecture documentation, see [ARCHITECTURE.md](ARCHITECTURE.md).

**Key principles:**
- **SOLID principles** applied throughout
- **Dependency injection** via FastAPI
- **Domain-driven design** with domain models
- **Clean separation** between layers
- **Exception-driven** flow control
