# ModelForge AI

ModelForge AI is a cloud-based platform that converts a trained deep-learning model into
deployment formats and benchmarks every version. Upload a PyTorch or ONNX model, convert it
to **TensorFlow Lite** and **TensorRT**, and compare size, latency and fidelity against the
original, all from one dashboard.

Source: <https://github.com/sanaryan175/model_forage_ai>

```
PyTorch (.pt)  ──►  ONNX  ──►  TFLite (FP32 / FP16)      CPU, mobile, edge
                         └──►  TensorRT (FP32 / FP16)    NVIDIA GPU
                         └──►  Core ML                   macOS only (reported as unsupported elsewhere)
```

## Features

- **Model upload and validation**: ONNX models or TorchScript `.pt` files. Every upload is
  checked (graph validity, input/output shapes) and run once through ONNX Runtime.
- **Conversion pipelines**: TFLite via onnx2tf + TensorFlow, TensorRT engines built on an
  NVIDIA GPU, in FP32 or FP16. Jobs run in the background with live status and logs, can be
  cancelled and retried. INT8 is not supported yet (it needs calibration data).
- **ONNX baseline**: every model is also benchmarked unchanged under ONNX Runtime, the
  reference all converted formats are compared against.
- **Benchmarks**: model size, latency (mean / median / p95), throughput, and **fidelity**: the
  share of test inputs where the converted model predicts the same class as the original.
  Anything that can't be measured on a machine is shown as N/A, never invented.
- **Compare and download**: side-by-side comparison with recommendations (fastest, smallest,
  most faithful), and downloads of every generated model.
- **Two run modes**: fully local (no AWS account), or on AWS with S3, SQS, ECS Fargate and RDS.
- **Auth**: register / log in with JWT; passwords hashed with bcrypt.

### Results with the project's ResNet-18 (CIFAR-10, 224×224 input)

| Format | Device | Latency | Size | Fidelity |
| --- | --- | --- | --- | --- |
| ONNX baseline | CPU | 7.9 ms | 44.7 MB | reference |
| TFLite FP32 | CPU | 33.6 ms | 44.7 MB | 100% |
| TFLite FP16 | CPU | 35.6 ms | 22.4 MB | 100% |
| TensorRT FP32 | RTX 2050 | 2.7 ms | 59.6 MB | 100% |
| TensorRT FP16 | RTX 2050 | 1.2 ms | 23.2 MB | 100% |

On the 10,000 labelled CIFAR-10 test images (`ml/Comparison.ipynb`), the TFLite model scores
the same accuracy, precision, recall and F1 as the original PyTorch model: the conversion
loses nothing.

## Architecture (AWS mode)

```
Laptop                                      AWS (ap-south-1)
───────────────────────────────            ─────────────────────────────────────────
Frontend (Next.js :3000)                    S3 bucket       uploaded + converted models
   │                                        SQS modelforge-cpu      ──►  ECS Fargate CPU worker
FastAPI (:8000) ── upload/download ──►         (+ DLQ)                    TFLite + ONNX baseline
   │            ── job_id ───────────►     SQS modelforge-tensorrt ──┐
   │            ── status/results ───►     RDS PostgreSQL            │   (+ DLQ)
TensorRT worker (RTX GPU) ◄──────────────────────────────────────────┘
```

1. The frontend talks only to the API. The API stores uploads in S3 and records them in RDS.
2. Starting a conversion creates one job row per format in RDS and sends `{"job_id": ...}`
   to SQS: TensorRT jobs to `modelforge-tensorrt`, everything else to `modelforge-cpu`.
3. A worker takes the message, downloads the model from S3, then runs
   validate → convert → optimize → benchmark, uploads the result to S3 and writes status,
   logs and benchmarks to RDS. Each worker runs one job at a time so latencies are fair.
4. A message that fails 3 times moves to its dead-letter queue. Cancelling marks the job in
   RDS; workers check that before every stage.

TensorRT runs on a laptop GPU instead of a cloud GPU: an engine only runs on the GPU model it
was built for, and a cloud GPU instance would exceed the project's $100 AWS budget. More detail
and costs: [`infrastructure/aws/README.md`](infrastructure/aws/README.md).

## Tech stack

| Technology | Used in | What it does |
| --- | --- | --- |
| PyTorch | Training, `.pt` uploads | Trains the ResNet-18; exports TorchScript models to ONNX |
| ONNX, ONNX Runtime | API and all workers | Common model format; upload validation; baseline benchmark |
| onnx2tf, TensorFlow Lite | CPU worker | ONNX → `.tflite` (FP32 / FP16) |
| TensorRT, cuda-python | GPU worker | ONNX → GPU-optimized `.engine` (FP32 / FP16) |
| FastAPI, SQLAlchemy 2, Alembic | Backend | REST API, database models, migrations |
| PyJWT, passlib (bcrypt) | Backend | Authentication |
| Next.js 16, React, TypeScript, Tailwind CSS, shadcn/ui, TanStack Query | Frontend | Dashboard |
| Amazon S3 | AWS | Model and artifact storage |
| Amazon SQS (+ DLQ) | AWS | Job queues |
| Amazon ECS Fargate, Amazon ECR | AWS | Runs the CPU worker container / stores its image |
| Amazon RDS PostgreSQL | AWS | Shared database for the API and workers |
| AWS IAM, CloudWatch Logs | AWS | Least-privilege roles; worker logs |
| Docker, Terraform, GitHub Actions | Tooling | Worker image; infrastructure as code; CI |

## Project layout

```
backend/
  app/
    routes/        HTTP endpoints (auth, models, conversions, benchmarks, artifacts, dashboard, health)
    services/      business logic
    repositories/  database access
    models/        SQLAlchemy models
    schemas/       Pydantic request/response schemas
    converters/    TFLite, TensorRT, Core ML and ONNX-baseline converters plus the registry
    benchmark/     size / latency / fidelity measurement
    workers/       conversion pipeline and job executors (local thread or SQS)
    queue/         local and SQS queue providers
    storage/       local disk and S3 storage providers
    utils/         ONNX helpers, PyTorch export, security, logging
  migrations/      Alembic migrations
  tests/           pytest suite
  requirements.txt       API + tests
  requirements-ml.txt    CPU conversion (TensorFlow, onnx2tf, PyTorch)
  requirements-gpu.txt   TensorRT (NVIDIA GPU machines only)
frontend/src/      Next.js app (pages, components, API client, auth context)
workers/           cpu_worker.py (ECS), tensorrt_worker.py (GPU laptop)
ml/
  checkpoints/     trained ResNet-18 (.pth) and its ONNX export
  export_resnet18_onnx.py   .pth weights → .onnx
  Comparison.ipynb          accuracy of PyTorch vs TFLite on CIFAR-10
infrastructure/
  terraform/       all AWS resources
  docker/          cpu-worker.Dockerfile
  aws/README.md    AWS architecture, costs, commands
```

## Setup

### Prerequisites

- Python 3.11 or 3.12, Node.js 22 + npm, Git
- For TensorRT: an NVIDIA GPU with a recent driver (no CUDA Toolkit needed, the pip wheels bundle it)
- For AWS mode only: AWS CLI v2, Terraform ≥ 1.6, Docker Desktop

### 1. Clone and create the Python environment

All commands below are PowerShell on Windows; the virtual environment lives in the repo root.

```powershell
git clone https://github.com/sanaryan175/model_forage_ai.git
cd model_forage_ai
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r backend\requirements.txt -r backend\requirements-ml.txt
# Only on a machine with an NVIDIA GPU:
.venv\Scripts\python.exe -m pip install -r backend\requirements-gpu.txt
```

`requirements.txt` alone is enough to run the API and the tests; without the ML packages a
converter reports "not installed" instead of crashing.

### 2. Frontend dependencies

```powershell
cd frontend
npm install
cd ..
```

The repo's `.npmrc` sets `legacy-peer-deps=true` for a peer-dependency mismatch between
`react-hook-form` and `@hookform/resolvers`.

## Run locally (no AWS)

Files are stored on disk, jobs run in background threads, the database is SQLite.

Create `backend/.env`:

```env
AWS_MODE=mock
DATABASE_URL=sqlite:///./modelforge.db
LOCAL_STORAGE_ROOT=./storage
JWT_SECRET=replace-with-a-long-random-string
CORS_ORIGINS=http://localhost:3000
```

Then, in two terminals:

```powershell
# Terminal 1: API (first time: create the tables)
cd backend
..\.venv\Scripts\python.exe -m alembic upgrade head
..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000

# Terminal 2: frontend
cd frontend
npm run dev
```

Open <http://localhost:3000>, register, upload `ml/checkpoints/resnet18_cifar10.onnx` and
convert it. API docs: <http://localhost:8000/docs>.

## Run on AWS

Only one team member should manage the infrastructure: Terraform's state
(`terraform.tfstate`) lives on that machine and is not in git.

### 1. AWS access

Each team member uses their **own** IAM user and access key (never share keys):

```powershell
aws configure --profile modelforge     # region: ap-south-1
aws sts get-caller-identity --profile modelforge
```

### 2. Create the infrastructure (infrastructure owner)

```powershell
cd infrastructure\terraform
copy terraform.tfvars.example terraform.tfvars   # set db_password, my_ip_cidr; cpu_worker_count = 0 for now
terraform init
terraform plan -out=tfplan                       # review
terraform apply tfplan
```

This creates the S3 bucket, both SQS queues with DLQs, RDS PostgreSQL, the ECR repository,
the ECS cluster and worker service, IAM roles and the CloudWatch log group.

### 3. Build and push the CPU worker image, then start it

```powershell
cd <repo root>
docker build -f infrastructure\docker\cpu-worker.Dockerfile -t modelforge-cpu-worker .
$REPO = terraform -chdir=infrastructure\terraform output -raw ecr_cpu_worker_url
aws ecr get-login-password --profile modelforge --region ap-south-1 | docker login --username AWS --password-stdin $REPO.Split('/')[0]
docker tag modelforge-cpu-worker:latest "${REPO}:latest"
docker push "${REPO}:latest"
```

Set `cpu_worker_count = 1` in `terraform.tfvars`, then `terraform plan -out=tfplan` and
`terraform apply tfplan`.

### 4. Configure the backend for AWS

Copy `backend/.env.aws.example` to `backend/.env.aws` and fill it in from
`terraform output` (`s3_bucket`, the queue names, and `terraform output -raw database_url`).
This file holds the database password: it is git-ignored, share it only privately.

Create the tables in RDS once:

```powershell
cd backend
$env:ENV_FILE=".env.aws"
..\.venv\Scripts\python.exe -m alembic upgrade head
```

### 5. Run (three terminals)

```powershell
# Terminal 1: API in AWS mode
cd backend
$env:ENV_FILE=".env.aws"
..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000

# Terminal 2: TensorRT GPU worker (NVIDIA GPU machine)
cd backend
$env:ENV_FILE=".env.aws"
..\.venv\Scripts\python.exe ..\workers\tensorrt_worker.py

# Terminal 3: frontend
cd frontend
npm run dev
```

The CPU worker runs on ECS by itself. Watch its logs with:

```powershell
aws logs tail /ecs/modelforge/cpu-worker --profile modelforge --region ap-south-1 --follow
```

`$env:ENV_FILE` applies only to the current terminal; without it the app runs in local mode.

### Costs and shutting down

| State | Approx. cost |
| --- | --- |
| Everything running (worker on) | ~$16 / week |
| `cpu_worker_count = 0` (data kept, conversions queue up until the worker is back) | ~$5 / week |
| `terraform destroy` (deletes the database, all S3 files and the image) | $0 |

Set a monthly budget alert in AWS Billing → Budgets.

### Troubleshooting

- **API or GPU worker: database connection timeout.** Your public IP changed (new Wi-Fi /
  hotspot). Check it with `curl https://checkip.amazonaws.com`, update `my_ip_cidr` in
  `terraform.tfvars`, then plan and apply.
- **TFLite / baseline jobs stay "queued".** The ECS worker is off (`cpu_worker_count = 0`) or
  still starting; check with
  `aws ecs describe-services --profile modelforge --region ap-south-1 --cluster modelforge --services modelforge-cpu-worker`.
- **Sign-up returns 422.** Use a normal email address (`name@gmail.com`); reserved domains
  such as `.local` or `localhost` are rejected.
- **A `.pt` upload is "Invalid".** Only TorchScript files are accepted (`torch.jit.save`).
  Weights-only checkpoints (`state_dict`, `.pth`) need the model class: export them to ONNX
  first, as `ml/export_resnet18_onnx.py` does for the ResNet-18.

## The ML model

- `ml/checkpoints/best_resnet18_cifar10.pth`: ResNet-18 fine-tuned on CIFAR-10 (10 classes,
  224×224 input), trained by the team in Colab.
- `ml/export_resnet18_onnx.py` rebuilds the network with torchvision, loads the weights and
  exports `ml/checkpoints/resnet18_cifar10.onnx`, the file uploaded to the platform.
- `ml/Comparison.ipynb` scores the original PyTorch model and the converted TFLite model on the
  10,000 CIFAR-10 test images (accuracy, precision, recall, F1, confusion matrix).

## Testing and linting

```powershell
# Backend (from backend/)
..\.venv\Scripts\python.exe -m pytest
ruff check app

# Frontend (from frontend/)
npx eslint .
npm run build
npx tsc --noEmit     # after a build; it needs the route types Next.js generates
```

Tests that need TensorFlow or an NVIDIA GPU are skipped automatically on machines without them.

## Continuous integration

GitHub Actions (`.github/workflows/ci.yml`) runs on every push to `main` and on pull requests:

1. **backend**: `ruff check`, then `pytest` with coverage.
2. **frontend**: `eslint`, `next build`, then `tsc --noEmit`.
3. **docker-build**: builds the backend and frontend images once both pass.

## Configuration reference

| Variable | Purpose |
| --- | --- |
| `ENV_FILE` | Which settings file the backend reads (`.env` by default, `.env.aws` for AWS mode) |
| `AWS_MODE` | `mock`: local disk + in-process jobs. `aws`: S3 + SQS |
| `DATABASE_URL` | SQLite locally, RDS PostgreSQL (`postgresql+psycopg://...`) in AWS mode |
| `JWT_SECRET` | Secret used to sign login tokens |
| `LOCAL_STORAGE_ROOT` | Where files are stored in mock mode |
| `AWS_PROFILE`, `AWS_REGION` | AWS CLI profile and region the laptop uses (empty profile on ECS: the task role is used) |
| `S3_BUCKET`, `SQS_CPU_QUEUE`, `SQS_TENSORRT_QUEUE` | AWS resource names, from `terraform output` |
| `CORS_ORIGINS` | Frontend URL(s) allowed to call the API |

## License

No license has been specified yet.
