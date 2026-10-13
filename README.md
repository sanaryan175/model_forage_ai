# ModelForge AI

ModelForge AI is a web platform for managing machine-learning models and converting them for deployment. You upload a model, convert it to a target runtime format, benchmark the results, and compare the generated artifacts, all from one dashboard.

Source: <https://github.com/sanaryan175/model_forage_ai>

## Features

- **Model management**: upload models (ONNX and PyTorch exports) and browse their versions and metadata.
- **Conversion pipeline**: convert models to TFLite, Core ML and TensorRT through a pluggable converter registry. Jobs run in the background with live status and logs.
- **Benchmarks and comparison**: benchmark the original and converted models and compare them side by side.
- **Generated artifacts**: list and download the outputs of each conversion job.
- **Auth**: register and log in with JWT-based authentication. API keys are supported.
- **Dashboard and activity feed**: an overview of models, jobs and recent activity.
- **Local mock mode**: run everything locally with no AWS account. Storage goes to disk and the job queue runs in-process.

## Tech stack

| Layer | Technology |
| --- | --- |
| Backend | Python 3.12, FastAPI, SQLAlchemy 2, Alembic, Pydantic Settings, structlog |
| Auth | PyJWT, passlib (bcrypt) |
| ML tooling | ONNX, ONNX Runtime (base install); PyTorch, TensorFlow and coremltools (optional, see below) |
| Storage and queue | Local disk or S3; in-process queue or SQS (via boto3) |
| Frontend | Next.js 16 (App Router, Turbopack), React, TypeScript, Tailwind CSS, shadcn/ui, TanStack Query |
| Infra | Docker, Terraform, GitHub Actions |

## Project layout

```
backend/
  app/
    routes/        HTTP endpoints (auth, models, conversions, benchmarks, artifacts, dashboard, health)
    services/      business logic
    repositories/  database access
    models/        SQLAlchemy models
    schemas/       Pydantic request/response schemas
    converters/    TFLite, Core ML and TensorRT converters plus the registry
    benchmark/     benchmark engine
    workers/       conversion worker and job executor
    queue/         local and SQS queue providers
    storage/       local and S3 storage providers
    utils/         ONNX helpers, PyTorch export, security, logging
  migrations/      Alembic migrations
  tests/           pytest suite
frontend/
  src/             Next.js app (pages, components, API client, auth context)
infrastructure/    Terraform
ml/  workers/      ML and worker support code
.github/workflows/ CI
```

## Getting started

### Prerequisites

- Python 3.12
- Node.js 22 and npm
- Docker (optional, for the container builds)

### Backend

```bash
cd backend
python -m venv .venv
source .venv/Scripts/activate        # Windows (Git Bash). On Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file in `backend/`. The values below are for local development, so change `JWT_SECRET` for anything else:

```env
DATABASE_URL=sqlite:///./dev.db
AWS_MODE=mock
LOCAL_STORAGE_ROOT=./storage
JWT_SECRET=change-me
```

Apply the migrations and start the API:

```bash
alembic upgrade head
uvicorn app.main:app --reload
```

The API is served at <http://localhost:8000>. FastAPI's interactive docs are at `/docs`.

#### Optional: real conversions

The base `requirements.txt` is enough to run the API, upload and inspect models, and run the tests. Actual TFLite, Core ML and TensorRT conversions need heavier dependencies:

```bash
pip install -r requirements-ml.txt
```

Without them, a converter reports that the environment doesn't support that target instead of crashing. TensorRT additionally needs a supported NVIDIA environment.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The app runs at <http://localhost:3000> and talks to the backend at `http://localhost:8000` by default. The repo's `.npmrc` sets `legacy-peer-deps=true` to work around a peer-dependency range mismatch between `react-hook-form` and `@hookform/resolvers`.

## Testing and linting

```bash
# Backend (from backend/)
ruff check app
pytest --cov=app --cov-report=term-missing

# Frontend (from frontend/)
npx eslint .
npm run build
npx tsc --noEmit     # run after a build; it needs the route types Next.js generates
```

Ruff is configured in `backend/pyproject.toml`.

## Docker

```bash
docker build --build-arg INSTALL_ML_DEPS=false -t modelforge-backend ./backend
docker build -t modelforge-frontend ./frontend
```

`INSTALL_ML_DEPS=false` skips the heavy ML packages for a smaller, faster backend image. The frontend uses Next.js `standalone` output.

## Continuous integration

GitHub Actions (`.github/workflows/ci.yml`) runs on every push to `main` and on pull requests:

1. **backend**: `ruff check`, then `pytest` with coverage.
2. **frontend**: `eslint`, `next build`, then `tsc --noEmit`.
3. **docker-build**: builds both images once the first two jobs pass.

## Configuration reference

| Variable | Purpose |
| --- | --- |
| `DATABASE_URL` | SQLAlchemy database URL (SQLite for local use, PostgreSQL via `psycopg` otherwise) |
| `AWS_MODE` | `mock` for local disk storage and an in-process queue; otherwise S3 and SQS |
| `LOCAL_STORAGE_ROOT` | Where uploaded models and artifacts are written in mock mode |
| `JWT_SECRET` | Secret used to sign auth tokens |

## License

No license has been specified yet.
