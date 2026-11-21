# Assignment 12 — FastAPI Calculator API

A FastAPI and PostgreSQL backend implementing **user registration, JWT-based login, and Calculation BREAD (Browse, Read, Edit, Add, Delete)**. The application uses Pydantic v2 for request/response validation, SQLAlchemy for persistence, a Calculation Factory for arithmetic operations, bcrypt password hashing, and GitHub Actions for tests, security scanning, and Docker Hub publishing.

This module completes the backend API in preparation for the Module 13 frontend.

## Features

- **Users:** register and log in using username or email; passwords are stored as bcrypt hashes rather than plaintext. Successful login returns a JWT bearer token.
- **Calculations:** create, list, retrieve, update, and delete stored calculations. Supported operations: `Add`, `Sub`, `Multiply`, and `Divide`. Results are recalculated server-side.
- **Validation:** Pydantic checks requests; duplicate registrations, invalid credentials, missing calculation IDs, invalid operation types, and division by zero return appropriate error responses.
- **Testing:** unit, API integration, database integration, and Playwright E2E tests against a separate PostgreSQL test database.
- **Delivery:** Docker/Compose, GitHub Actions, Trivy image scanning, and Docker Hub image publishing.

## API Endpoints

| Method | Endpoint | Purpose | Typical success status |
|---|---|---|---|
| `POST` | `/users/register` | Register a user | `201 Created` |
| `POST` | `/users/login` | Verify credentials and return JWT | `200 OK` |
| `POST` | `/calculations` | Add a stored calculation | `201 Created` |
| `GET` | `/calculations` | Browse calculations | `200 OK` |
| `GET` | `/calculations/{calculation_id}` | Read one calculation | `200 OK` |
| `PUT` | `/calculations/{calculation_id}` | Edit and recalculate | `200 OK` |
| `DELETE` | `/calculations/{calculation_id}` | Delete a calculation | `204 No Content` |
| `GET` | `/health` | Application health check | `200 OK` |

The original arithmetic endpoints (`/add`, `/subtract`, `/multiply`, `/divide`) are also retained.

## Technology Stack

- Python 3.14, FastAPI, Pydantic v2
- SQLAlchemy and PostgreSQL 16
- bcrypt password hashing, JWT authentication
- pytest, pytest-cov, Playwright
- Docker and Docker Compose
- GitHub Actions and Trivy
- Docker Hub

## Local Setup (Ubuntu / WSL)

### Prerequisites

Install Git, Python 3.14, Docker with Docker Compose, and a working Python virtual environment.

### Clone and install

```bash
git clone https://github.com/YOUR_GITHUB_USERNAME/YOUR_REPOSITORY.git
cd YOUR_REPOSITORY
git switch assignment12
python3.14 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m playwright install chromium
```

Replace the repository placeholders with the real GitHub URL and local directory. After Assignment 12 is merged into `main`, the branch switch is optional.

### Environment variables

Create a local `.env` file (never commit it). For development with the project’s Docker Compose file, a `SECRET_KEY` is required:

```bash
python -c 'import secrets; print("SECRET_KEY=" + secrets.token_urlsafe(48))' > .env
```

Other configuration defaults or Compose environment settings include `ALGORITHM=HS256` and `ACCESS_TOKEN_EXPIRE_MINUTES=30`. Inside Compose, FastAPI connects to PostgreSQL at `db:5432`; from the WSL host, PostgreSQL is exposed on `localhost:5433`.

### Start the application with Docker Compose

```bash
docker compose up -d --build
docker compose ps
docker compose logs web --tail=50
```

The web container initializes any missing application tables before launching Uvicorn. Database initialization uses `Base.metadata.create_all()`; it is **not** a replacement for schema migrations.

Service URLs:

- Health check: <http://localhost:8000/health>
- Swagger UI: <http://localhost:8000/docs>
- ReDoc: <http://localhost:8000/redoc>
- pgAdmin: <http://localhost:5050/>

Test the health endpoint:

```bash
curl -i http://localhost:8000/health
```

Expected HTTP status: `200 OK`.

Stop the application without removing stored PostgreSQL data:

```bash
docker compose down
```

**Warning:** Do not use `docker compose down -v` unless intentionally deleting the Compose-managed database volumes.

## Manual Testing Through OpenAPI (Swagger UI)

Open <http://localhost:8000/docs>, expand an endpoint, click **Try it out**, enter the JSON body or path parameter, and click **Execute**.

1. **Register** at `POST /users/register`:

   ```json
   {
     "first_name": "Jane",
     "last_name": "Doe",
     "email": "jane.assignment12@example.com",
     "username": "janeassignment12",
     "password": "SecurePass123"
   }
   ```

   Expected: `201 Created` and user information **without** a plaintext password or password hash. Repeating the same registration should return `409 Conflict`.

2. **Log in** at `POST /users/login`:

   ```json
   {
     "username": "janeassignment12",
     "password": "SecurePass123"
   }
   ```

   Expected: `200 OK`, a nonempty `access_token`, and `token_type: "bearer"`. A wrong password should return `401 Unauthorized`. Do not share real access tokens in screenshots.

3. **Add** a calculation at `POST /calculations`:

   ```json
   {
     "a": 10.0,
     "b": 5.0,
     "type": "Add"
   }
   ```

   Expected: `201 Created`, a generated `id`, and `result: 15.0`. Save the returned ID for the next steps.

4. **Browse** using `GET /calculations`. Expected: `200 OK` and a JSON list containing the saved calculation.
5. **Read** using `GET /calculations/{calculation_id}` and your saved ID. Expected: `200 OK` and the corresponding record.
6. **Edit** using `PUT /calculations/{calculation_id}` with:

   ```json
   {
     "a": 20.0,
     "b": 4.0,
     "type": "Divide"
   }
   ```

   Expected: `200 OK`, the same ID, and `result: 5.0`.
7. **Delete** using `DELETE /calculations/{calculation_id}`. Expected: `204 No Content`. Reading that ID afterward should return `404 Not Found`.
8. **Validation checks:** division by zero and unsupported operations should return `400 Bad Request`. This application uses a custom validation handler that returns HTTP `400` rather than FastAPI’s default `422`.

## Integration Tests and Coverage

Tests use a **separate** PostgreSQL database named `fastapi_test_db`. Existing fixtures may drop/recreate tables; **never point tests at a development or production database containing important data**.

### 1. Start PostgreSQL

```bash
docker compose up -d db
```

If needed, create the test database once:

```bash
docker compose exec db psql -U postgres -d postgres -c "CREATE DATABASE fastapi_test_db;"
```

Skip this command if the database already exists.

### 2. Configure the test database

For local WSL testing:

```bash
export TEST_DATABASE_URL="postgresql://postgres:postgres@localhost:5433/fastapi_test_db"
```

Ensure the application's database configuration and test fixtures are pointed at the isolated test database when running tests.

### 3. Run focused API integration tests

```bash
python -m pytest tests/integration/test_user_api.py -v
python -m pytest tests/integration/test_calculation_api.py -v
```

The user API tests cover registration, authentication, invalid credentials, duplicate registration, password hashing, JWT issuance, and database persistence. The calculation API tests cover all five BREAD operations, arithmetic correctness, missing IDs, invalid requests, and persistence.

### 4. Run the full suite with coverage enforcement

The E2E tests require a running FastAPI server. Start the Compose web service or run Uvicorn locally with a valid database configuration and `SECRET_KEY`.

```bash
python -m pytest --run-slow -v \
  --cov=app \
  --cov-report=term-missing \
  --cov-report=html \
  --cov-fail-under=100
```

The HTML report is written to `htmlcov/index.html`.

**Verified local result (November 21, 2026): 139 passed, 100.00% coverage (329 statements, 0 missed).** The run reported one non-fatal `runpy` warning in the database initialization entrypoint test.

## CI/CD with GitHub Actions

The workflow lives at `.github/workflows/test.yml` and is configured to run on pushes to `main`, `assignment12`, and `feature/**` branches and on pull requests targeting `main` or `assignment12`.

1. **Test job:** start PostgreSQL 16, install Python dependencies and Playwright, start FastAPI, run pytest including slow tests, and enforce 100% coverage.
2. **Security job:** build the Docker image and scan it with Trivy for configured HIGH/CRITICAL findings.
3. **Deploy job:** after successful preceding jobs, publish Docker images for allowed branch pushes. Pull requests and feature branches do not publish images.

Configure GitHub repository **Settings → Secrets and variables → Actions**:

| Type | Name | Description |
|---|---|---|
| Variable | `DOCKERHUB_USERNAME` | Docker Hub username |
| Secret | `DOCKERHUB_TOKEN` | Docker Hub access token with permission to push |

Image tagging strategy:

- Push to `assignment12`: `YOUR_DOCKERHUB_USERNAME/assignment12:assignment12` and a commit-SHA tag.
- Push to `main`: `YOUR_DOCKERHUB_USERNAME/assignment12:latest` and a commit-SHA tag.

The deploy job runs only when prior tests and the security scan succeed. Review the actual GitHub Actions run to confirm deployment status; local test success alone does not prove the remote workflow passed.

## Docker Hub

**Docker Hub repository:** [aby3989/assignment12](https://hub.docker.com/r/aby3989/assignment12)


After a successful `assignment12` deployment, pull the branch-tagged image:

```bash
docker pull aby3989/assignment12:assignment12
```

After the final merge to `main` and successful deployment:

```bash
docker pull aby3989/assignment12:latest
```
