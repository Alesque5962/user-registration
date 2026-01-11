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
- Fully dockerized application
- Pytest test suite

---

## Tech Stack

- **Python 3.13**
- **FastAPI** (routing and dependency injection only)
- **PostgreSQL**
- **psycopg (v3)** – SQL queries only
- **Docker & Docker Compose**
- **Pytest**

---

## Architecture

```
Client (Browser / API Client)
        |
        | HTTP
        v
FastAPI Application
        |
        | SQL (psycopg)
        v
PostgreSQL Database
        |
        | SMTP (external service)
        v
SMTP Service (mocked)
```

The SMTP service is considered as **third-party service**.  
For simplicity, the activation code is printed in the application logs.

---

## Project Structure

```
.
├── app/
│   ├── services/
│   │   ├── activation.py      # Activation code generation & expiration logic
│   │   ├── mailer.py          # SMTP service abstraction (mocked)
│   ├── db.py                  # Database connection & SQL queries
│   ├── main.py                # FastAPI app & routes
│   └── security.py            # HTTP Basic Auth verification
├── tests/
│   ├── test_registration.py   # Registration tests
│   └── test_activation.py     # Activation tests
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
├── README.md
├── user_registration_api.md
├── uv.lock
```

---

## Database Initialization

At application startup:

1. The API waits for PostgreSQL to be available
2. The database is created if it does not exist
3. The `users` table is created if it does not exist

Table definition:

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT FALSE,
    activation_code TEXT,
    activation_expires_at TIMESTAMPTZ
);
```

---

## Running the Application

### Prerequisites

⚠️ **Only Docker and Docker Compose are required**  
No local Python installation is needed.

- Docker
- Docker Compose

---

### Start the application

From the project root:

```bash
docker-compose up --build
```

The API will be available at:

- **API**: http://localhost:8000
- **Swagger UI**: http://localhost:8000/docs

---

## API Usage

### Register a user

```
POST /register?email=user@example.com&password=secret
```

Response:

```json
{
  "message": "User created"
}
```

The activation code will be printed in the logs:

```
[SMTP] Activation code for user@example.com: 1234
```

---

### Activate the account

```
POST /activate?code=1234
```

Authentication:
- **Username**: user email
- **Password**: user password

Swagger UI will automatically prompt for credentials using **HTTP Basic Auth**.

Successful response:

```json
{
  "message": "Account activated"
}
```

---

## Test Suite

The application includes comprehensive test coverage:

### Registration Tests (`tests/test_registration.py`)
- **Successful user registration** - Verifies user creation with hashed password and activation code
- **Duplicate email handling** - Ensures unique email constraint returns HTTP 400
- **Activation code format** - Validates 4-digit numeric code generation

### Activation Tests (`tests/test_activation.py`)
- **Successful activation** - Valid code and credentials activate the account
- **Invalid activation code** - Wrong code returns HTTP 400
- **Expired activation code** - Code older than 1 minute returns HTTP 400
- **Wrong password** - Incorrect credentials return HTTP 401
- **User not found** - Unknown email returns HTTP 404
- **Already activated account** - Attempting to reactivate returns HTTP 400

### Running Tests

Run the full test suite:
```bash
docker-compose run api pytest
```

Run with verbose output:
```bash
docker-compose run api pytest -v
```

Run specific test file:
```bash
docker-compose run api pytest tests/test_activation.py
```

Run specific test:
```bash
docker-compose run api pytest tests/test_activation.py::test_activate_success
```