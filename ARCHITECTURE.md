# Architecture Documentation

## Table of Contents

- [Overview](#overview)
- [Architecture Pattern](#architecture-pattern)
- [Layer Descriptions](#layer-descriptions)
- [Cross-Cutting Concerns](#cross-cutting-concerns)
- [Data Flow](#data-flow)
- [SOLID Principles](#solid-principles)
- [Dependency Injection](#dependency-injection)
- [Testing Strategy](#testing-strategy)
- [Migration Guide](#migration-guide)

---

## Overview

This API follows a **3-layer architecture** (Three-Layer Architecture) to separate responsibilities and facilitate maintenance, testing, and evolution of the codebase.

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Client (HTTP)                             │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              API Layer (Presentation)                        │
│  • app/api/routes/users.py                                   │
│  • app/api/schemas/user.py                                   │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│  Responsibilities:                                           │
│  • HTTP request/response handling                            │
│  • Input/output validation (Pydantic)                        │
│  • Exception → HTTP status code mapping                      │
│  • Dependency injection orchestration                        │
└──────────────────────┬──────────────────────────────────────┘
                       │ depends on ↓
┌──────────────────────▼──────────────────────────────────────┐
│              Service Layer (Business Logic)                  │
│  • app/services/user_service.py                              │
│  • app/services/activation.py                                │
│  • app/services/mailer.py                                    │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│  Responsibilities:                                           │
│  • Business rules enforcement                                │
│  • Operation orchestration                                   │
│  • Transaction coordination                                  │
│  • Domain exception handling                                 │
└──────────────────────┬──────────────────────────────────────┘
                       │ depends on ↓
┌──────────────────────▼──────────────────────────────────────┐
│              Data Layer (Persistence)                        │
│  • app/data/repositories/user_repository.py                  │
│  • app/data/models/user.py                                   │
│  • app/data/db.py                                            │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│  Responsibilities:                                           │
│  • Database access                                           │
│  • SQL query execution                                       │
│  • DB ↔ Domain model mapping                                 │
│  • Constraint violation handling                             │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              PostgreSQL Database                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Architecture Pattern

### 3-Layer Architecture

This application uses a **layered architecture** where each layer has specific responsibilities and can only depend on layers below it.

**Dependency Flow:** API → Services → Data → Database

**Benefits:**
- ✅ **Separation of Concerns**: Each layer has one responsibility
- ✅ **Testability**: Layers can be tested independently
- ✅ **Maintainability**: Changes are localized
- ✅ **Reusability**: Business logic can be used outside HTTP context
- ✅ **Scalability**: Easy to split into microservices

---

## Layer Descriptions

### 1. API Layer (`app/api/`)

**Responsibility**: Handle HTTP communication

**Components**:
- **Routes** (`app/api/routes/users.py`): FastAPI endpoints
- **Schemas** (`app/api/schemas/user.py`): Pydantic models for validation

**Rules**:
- ✅ Validates HTTP requests and responses
- ✅ Maps business exceptions to HTTP status codes
- ✅ Manages dependency injection
- ❌ Contains NO business logic
- ❌ Does NOT access database directly

**Example**:
```python
@router.post("/register", response_model=MessageResponse)
async def register(
    user_data: UserRegistration,
    service: Annotated[UserService, Depends(get_user_service)],
):
    try:
        await service.register_user(user_data.email, user_data.password)
        return MessageResponse(message="User created")
    except UserAlreadyExistsError:
        raise HTTPException(status_code=400, detail="Email already exists")
```

---

### 2. Service Layer (`app/services/`)

**Responsibility**: Implement business logic

**Components**:
- **UserService** (`user_service.py`): User operations orchestration
- **Activation** (`activation.py`): Code generation
- **Mailer** (`mailer.py`): Email service abstraction

**Rules**:
- ✅ Implements business rules
- ✅ Orchestrates complex operations
- ✅ Raises domain-specific exceptions
- ✅ Coordinates multiple repositories
- ❌ Does NOT know about HTTP/FastAPI
- ❌ Does NOT execute SQL queries

**Example**:
```python
async def register_user(self, email: str, password: str) -> None:
    # Hash password
    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    
    # Generate activation code
    code = generate_code()
    expires_at = expiration_time()
    
    # Create user via repository
    try:
        user = await self.repository.create(email, password_hash, code, expires_at)
    except ValueError as e:
        raise UserAlreadyExistsError(str(e))
    
    # Send activation email
    send_activation_email(user.email, code)
```

---

### 3. Data Layer (`app/data/`)

**Responsibility**: Manage data persistence

**Components**:
- **Repositories** (`repositories/user_repository.py`): Data access
- **Models** (`models/user.py`): Domain entities
- **Database** (`db.py`): Connection management

**Rules**:
- ✅ Executes SQL queries
- ✅ Maps database rows to domain models
- ✅ Handles database constraints
- ❌ Contains NO business logic
- ❌ Does NOT know about HTTP

**Example**:
```python
async def create(
    self,
    email: str,
    password_hash: bytes,
    activation_code: str,
    expires_at: datetime,
) -> User:
    user_id = uuid.uuid4()
    
    try:
        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO users (id, email, password_hash, 
                                     activation_code, activation_expires_at)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (str(user_id), email, password_hash, activation_code, expires_at),
                )
    except UniqueViolation:
        raise ValueError(f"User with email {email} already exists")
    
    return User(
        id=user_id,
        email=email,
        password_hash=password_hash,
        is_active=False,
        activation_code=activation_code,
        activation_expires_at=expires_at,
    )
```

---

## Cross-Cutting Concerns

### Configuration (`app/core/config.py`)

**Purpose**: Centralize application settings

```python
class Settings(BaseSettings):
    db_host: str
    db_port: int
    db_name: str
    activation_code_expiry_minutes: int = 1
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

# Global settings instance
settings = Settings()
```

### Security (`app/core/security.py`)

**Purpose**: Security utilities

```python
def verify_password(password: str, stored_hash: bytes) -> bool:
    """Verify password against bcrypt hash."""
    return bcrypt.checkpw(password.encode(), stored_hash)
```

### Domain Models (`app/data/models/user.py`)

**Purpose**: Pure domain entities with business logic

```python
@dataclass
class User:
    id: UUID
    email: str
    password_hash: bytes
    is_active: bool
    activation_code: str | None
    activation_expires_at: datetime | None
    
    def is_activation_code_expired(self, current_time: datetime) -> bool:
        """Check if activation code is expired."""
        if not self.activation_expires_at:
            return True
        return current_time > self.activation_expires_at
    
    def can_activate(self, code: str, current_time: datetime) -> bool:
        """Check if user can be activated with given code."""
        if self.is_active:
            return False
        if self.is_activation_code_expired(current_time):
            return False
        return code == self.activation_code
```

### API Schemas (`app/api/schemas/`)

**Purpose**: Request/response validation

```python
class UserRegistration(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=100)

class UserActivation(BaseModel):
    code: str = Field(min_length=4, max_length=4, pattern=r"^\d{4}$")

class MessageResponse(BaseModel):
    message: str
```

---

## Data Flow

### Example: User Registration

```
┌────────────────────────────────────────────────────────────┐
│ 1. Client                                                   │
│    POST /register                                           │
│    {"email": "user@test.com", "password": "secret123"}     │
└──────────────────────┬─────────────────────────────────────┘
                       │
                       ▼
┌────────────────────────────────────────────────────────────┐
│ 2. API Layer (app/api/routes/users.py)                     │
│    • Validate with UserRegistration schema                 │
│    • Inject UserService via Depends()                      │
│    • Call service.register_user()                          │
└──────────────────────┬─────────────────────────────────────┘
                       │
                       ▼
┌────────────────────────────────────────────────────────────┐
│ 3. Service Layer (app/services/user_service.py)            │
│    • Hash password with bcrypt                             │
│    • Generate 4-digit activation code                      │
│    • Calculate expiration time (1 minute)                  │
│    • Call repository.create()                              │
│    • Send activation email                                 │
└──────────────────────┬─────────────────────────────────────┘
                       │
                       ▼
┌────────────────────────────────────────────────────────────┐
│ 4. Data Layer (app/data/repositories/user_repository.py)   │
│    • Execute INSERT query                                  │
│    • Handle UniqueViolation constraint                     │
│    • Map row to User model                                 │
│    • Return User instance                                  │
└──────────────────────┬─────────────────────────────────────┘
                       │
                       ▼
┌────────────────────────────────────────────────────────────┐
│ 5. Database                                                 │
│    • Store user record                                     │
└──────────────────────┬─────────────────────────────────────┘
                       │
                       ▼ (response flows back)
┌────────────────────────────────────────────────────────────┐
│ 6. Client                                                   │
│    {"message": "User created"}                             │
└────────────────────────────────────────────────────────────┘
```

---

## SOLID Principles

### Single Responsibility Principle (SRP)

Each class has one reason to change:
- **API Layer**: HTTP communication only
- **Service Layer**: Business logic only
- **Data Layer**: Database access only

### Open/Closed Principle (OCP)

Open for extension, closed for modification:
```python
# Easy to add new services without modifying existing ones
class UserService:
    def __init__(self, repository: UserRepository):
        self.repository = repository
    
    async def register_user(self, email: str, password: str) -> None:
        # Implementation
```

### Liskov Substitution Principle (LSP)

Subtypes can replace base types without breaking functionality.

### Interface Segregation Principle (ISP)

Clients depend only on methods they use:
```python
# Repository has focused interface
class UserRepository:
    async def create(...) -> User: ...
    async def find_by_email(email: str) -> User | None: ...
    async def activate(email: str) -> None: ...
```

### Dependency Inversion Principle (DIP)

High-level modules depend on abstractions:
```python
# Service depends on repository interface, not implementation
class UserService:
    def __init__(self, repository: UserRepository):
        self.repository = repository  # Abstraction, not concrete class
```

---

## Dependency Injection

FastAPI's `Depends()` manages dependency injection:

```python
# Dependency providers
def get_user_repository() -> UserRepository:
    pool = get_pool()
    return UserRepository(pool)

def get_user_service(
    repository: Annotated[UserRepository, Depends(get_user_repository)]
) -> UserService:
    return UserService(repository)

# Automatic injection in routes
@router.post("/register")
async def register(
    service: Annotated[UserService, Depends(get_user_service)],
):
    # service is automatically injected with all dependencies
    await service.register_user(...)
```

**Benefits**:
- ✅ Loose coupling between layers
- ✅ Easy to swap implementations
- ✅ Simple to mock for testing

---

## Testing Strategy

### Unit Tests (Service Layer)

Test business logic without database or HTTP:

```python
@pytest.fixture
def mock_repository():
    """Mock repository for service testing."""
    return Mock(spec=UserRepository)

@pytest.fixture
def user_service(mock_repository):
    """Service with mocked dependencies."""
    return UserService(mock_repository)

@pytest.mark.asyncio
async def test_register_user_success(user_service, mock_repository):
    # Arrange
    mock_repository.create = AsyncMock(return_value=User(...))
    
    # Act
    await user_service.register_user("test@test.com", "password")
    
    # Assert
    mock_repository.create.assert_called_once()
```

### Integration Tests (API Layer)

Test HTTP endpoints with test database:

```python
async def test_register_endpoint(client):
    response = await client.post(
        "/register",
        json={"email": "test@test.com", "password": "password123"}
    )
    assert response.status_code == 201
    assert response.json() == {"message": "User created"}
```

### Repository Tests (Data Layer)

Test database operations with test database:

```python
async def test_create_user(repository, db):
    user = await repository.create(
        email="test@test.com",
        password_hash=b"hashed",
        activation_code="1234",
        expires_at=datetime.now(UTC) + timedelta(minutes=1)
    )
    assert user.email == "test@test.com"
    assert not user.is_active
```

---

## Best Practices

### DO ✅

- Keep layers independent
- Use dependency injection
- Write tests for each layer
- Use domain-specific exceptions
- Document complex business rules
- Keep models rich with business logic

### DON'T ❌

- Mix HTTP concerns with business logic
- Put business logic in routes or repositories
- Access database directly from services
- Use generic exceptions
- Skip testing
- Create anemic models (data bags)

---

## Conclusion

This 3-layer architecture provides:
- **Separation of concerns** for better maintainability
- **Testability** at every level
- **Flexibility** to change implementations
- **Scalability** for future growth
- **SOLID principles** for clean code

The architecture is production-ready and follows industry best practices.
