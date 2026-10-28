# 📝 Notes App — CI/CD Demo

A simple FastAPI notes application used to demonstrate CI/CD with GitHub Actions,
Docker, and automated testing.

## Features

- Add and delete notes via web UI
- Input validation & sanitization
- Health check endpoint (`/health`)
- SQLite database
- Dockerized with non-root user
- CI: lint, type check, security scan, tests, Docker build
- CD: build, push to Docker Hub, deploy via SSH

## Quick Start

### Local Development

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open http://localhost:8000

### Run Tests

```bash
pytest
```

### Run with Docker (Local)

```bash
docker compose up --build
```

Open http://localhost:8000

### Deploy with Specific Image Tag

`docker-compose.yml` menggunakan environment variable `DOCKER_IMAGE` agar fleksibel
untuk local maupun production:

```bash
# Local build
DOCKER_IMAGE=notes-app:latest docker compose up --build

# Production deploy with SHA tag (otomatis di CD)
DOCKER_IMAGE=yourdockerhubusername/notes-app:<commit-sha> docker compose pull
DOCKER_IMAGE=yourdockerhubusername/notes-app:<commit-sha> docker compose up -d
```

Lihat `.env.example` untuk contoh pengaturan.

## CI/CD Pipelines

### CI (`ci.yml`)

Triggered on pull requests to `main` (e.g., MR `staging` → `main`):

1. **Lint** — `ruff check` + `ruff format --check`
2. **Type Check** — `mypy app`
3. **Security Scan** — `bandit -r app`
4. **Unit Tests** — `pytest` with coverage
5. **Docker Build Check** — builds image without pushing

### CD (`cd.yml`)

Triggered on push to `main` (after MR merged):

1. Build and push Docker image with **commit SHA tag only** (no `latest`)
2. Copy `docker-compose.yml` to server via SCP
3. Deploy dengan `docker compose` menggunakan image SHA tag
4. Post-deploy health check ke `/health`

Menggunakan SHA tag memastikan server selalu menjalankan image exact yang baru di-push,
tanpa risiko cache `latest` yang stale.

## Required Secrets & Variables

### Secrets (Settings → Secrets and variables → Actions)

- `DOCKERHUB_USERNAME`
- `DOCKERHUB_TOKEN`
- `SSH_HOST`
- `SSH_USER`
- `SSH_KEY`

### Variables (Settings → Secrets and variables → Actions → Variables tab)

| Variable | Default | Keterangan |
|----------|---------|------------|
| `IMAGE_NAME` | `notes-app` | Nama repository image di Docker Hub |
| `DEPLOY_PORT` | `80` | Port host yang dipublish di server |
| `DEPLOY_DIR` | `~/notes-app` | Direktori di server tempat `docker-compose.yml` dicopy |

Variables bersifat non-sensitive dan memudahkan konfigurasi tanpa mengubah code.

### GitHub Environment (opsional)

Kalau mau, kamu bisa tambahkan `environment: production` di job `deploy` untuk
melihat deployment history di GitHub. Protection rules seperti manual approval
disini sengaja tidak digunakan karena deploy harus berjalan otomatis.

## Demo Failure Scenarios

Untuk melihat bagaimana CI pipeline menangkap kesalahan, coba scenario berikut:

### Scenario 1: Linter gagal

Tambahkan unused import di `app/main.py`:

```python
import os
```

Lalu jalankan:

```bash
ruff check app tests
```

Output yang muncul:

```text
app/main.py:3:8: F401 [*] `os` imported but unused
Found 1 error.
```

Di GitHub Actions, job **Lint & Format** akan fail dan MR tidak bisa di-merge
(jika branch protection diaktifkan).

### Scenario 2: Test gagal

Ubah expected value di `tests/test_main.py`:

```python
assert response.json() == {"status": "unhealthy"}
```

Lalu jalankan:

```bash
pytest tests/test_main.py::test_health_check -v
```

Output yang muncul:

```text
AssertionError: assert {'status': 'healthy'} == {'status': 'unhealthy'}
```

Di GitHub Actions, job **Unit Tests** akan fail.

### Scenario 3: Docker build gagal

Contoh: syntax error di `Dockerfile` atau missing dependency. Job **Docker Build Check**
akan fail sebelum image di-push ke Docker Hub.

### Kesimpulan

Dengan pipeline ini, kesalahan akan tertangkap di CI sebelum code sampai ke server.
CD (deploy) hanya berjalan kalau semua job CI berhasil.
