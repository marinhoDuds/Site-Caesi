# Site Caesi

This README explains how to setup project bases.

## Project Structure

Current repository layout:

```text
.
├── infra/
│   └── garage/
│       ├── Dockerfile
│       ├── entrypoint.sh
│       └── garage.toml.template
├── src/
│   ├── routes/
│   │   ├── calendar/
│   │   ├── home/
│   │   ├── informations/
│   │   ├── journal/
│   │   ├── map/
│   │   ├── portal/
│   │   ├── ticket/
│   │   └── webadmin/
│   └── service/
│       ├── authentication/
│       ├── calendar-management/
│       ├── home-management/
│       ├── informations-management/
│       ├── journal-management/
│       ├── map-management/
│       ├── portal-management/
│       ├── ticket-management/
│       ├── webadmin-management/
│       ├── crypto.py
│       ├── database.py
│       └── s3.py
├── tests/
│   ├── integration/
│   └── unit/
├── docker-compose.yml
├── pyproject.toml
├── uv.lock
└── CONTRIBUTING.md
```

## Setup Environment
This project uses an environment file for manage sensitive information. An example is avaliable on [.env.example](.env.example)

Create your local environment file:
```bash
cp .env.example .env
```

---

This project uses [uv](https://docs.astral.sh/uv/) to manage the Python environment and dependencies.

If you do not have `uv` installed yet, set it up first:

```bash
pip install uv
```

Create the virtual environment in the project root:

```bash
uv venv site_caesi
```

Activate the environment:

```bash
# Linux / macOS
source site_caesi/bin/activate

# Windows
site_caesi\Scripts\activate.bat
```

Install the project dependencies:

```bash
uv sync
```

To run a specific file without activating the environment manually, use:

```bash
uv run python path/to/file.py
```

For development, activating the environment is strongly recommended so your editor and terminal use the same interpreter.

## Development Commands

Useful local commands:

```bash
# Run tests
uv run pytest

# Run tests with coverage details
uv run pytest --cov=src --cov-report=term-missing

# Lint and style checks
uv run ruff check .
```

## Docker
This project uses [Docker](https://docs.docker.com/) to run the local MySQL database and Garage S3 bucket.
If Docker is already installed, you can jump directly to [Database](README.md#database) or [Bucket](README.md#bucket).

**Linux (Ubuntu/Debian)**
```bash
sudo apt update
sudo apt install -y docker.io docker-compose-plugin
sudo systemctl enable --now docker
```

**Linux (Fedora)**
```bash
sudo dnf install -y docker docker-compose
sudo systemctl enable --now docker
```

**macOS**
```bash
brew install --cask docker
```

**Windows**

Download and follow the installer instructions on [Docker Desktop](https://www.docker.com/products/docker-desktop/).

After installation, confirm everything is available:

```bash
docker --version
docker compose version
docker info
```

If this is your first time using Docker, these commands are useful:

```bash
# Test your installation
docker run --rm hello-world

# List running containers
docker ps

# List all containers (including stopped)
docker ps -a

# List local images
docker images

# Show container logs
docker logs <container_name_or_id>

# Open a shell inside a running container
docker exec -it <container_name_or_id> sh

# Stop and remove a container
docker stop <container_name_or_id>
docker rm <container_name_or_id>

# Start services from compose file in background
docker compose up -d

# Stop and remove compose services
docker compose down
```

## Database
This project uses [MySQL](https://dev.mysql.com/doc/) as the database. The schema is available in [database.sql](database.sql).

```bash
docker run --name site-caesi-mysql \
	-e MYSQL_DATABASE=site_caesi_db \
	-e MYSQL_USER=site_caesi \
	-e MYSQL_PASSWORD=pwd \
  	-e MYSQL_RANDOM_ROOT_PASSWORD=yes \
	-p 3306:3306 \
	-d mysql:latest
```

Import the schema with the dedicated user:

```bash
docker exec -i site-caesi-mysql mysql -usite_caesi -ppwd site_caesi_db < database.sql
```

## Bucket
This project uses [Garage](https://garagehq.deuxfleurs.fr/) as a local S3-compatible server, managed via Docker Compose.

Make sure your user has permission to access the Docker socket:

```bash
sudo usermod -aG docker $USER && newgrp docker
```

Build the image (required on first run or after changes to `infra/garage/Dockerfile`):

```bash
docker compose build
```

Start the service:

```bash
docker compose up -d garage
```

The service is ready when the logs show:

```
S3 API server listening on http://[::]:3900
```

Verify with a health check:

```bash
source .env
curl -s -H "Authorization: Bearer $ADMIN_TOKEN" http://localhost:3903/v1/health
```

The following environment variables control both the Garage server and the Python S3 client:

| Variable | Description |
|---|---|
| `GARAGE_DEFAULT_ACCESS_KEY` | Access key created by Garage on first boot, used by boto3 |
| `GARAGE_DEFAULT_SECRET_KEY` | Secret key created by Garage on first boot, used by boto3 |
| `GARAGE_DEFAULT_BUCKET` | Bucket created automatically on first boot |
| `AWS_ENDPOINT_URL` | S3 endpoint (`http://localhost:3900` in development) |
| `AWS_REGION` | Region configured in Garage (`garage`) |
| `RPC_SECRET` | Internal cluster secret (not exposed to the app) |
| `ADMIN_TOKEN` | Garage admin API token (port 3903) |
| `METRICS_TOKEN` | Garage metrics token |

To stop without losing data:

```bash
docker compose stop garage
```

To reset all stored objects:

```bash
docker compose down && rm -rf infra/garage/meta/* infra/garage/data/*
```

## Patterns

Project conventions and contribution standards are documented in [CONTRIBUTING.md](CONTRIBUTING.md).