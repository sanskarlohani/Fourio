# 🐳 Docker Setup

This guide explains how to run **Fourio** using Docker and Docker Compose.

---

# ✔ Prerequisites

Install the following:

- Docker
- Docker Compose

Verify installation:

```bash
docker --version
docker compose version
```

---

# 📁 Docker Files

| File | Purpose |
|------|----------|
| `Dockerfile` | Docker image definition |
| `docker-compose.yml` | Default application setup |
| `docker-compose-mongo.yml` | MongoDB-only setup |
| `docker-compose-hybrid.yml` | Mongo + Redis environment setup |
| `Makefile` | Helper commands for Docker workflows |

---

# 🚀 Quick Start

## 1. Clone Repository

```bash
git clone https://github.com/RudraNarayan94/Fourio.git
cd fourio
```

---

## 2. Configure Environment Variables

Create a `.env` file in the project root.

Use `.env.example` as reference.

Example:

```env
SPOTIFY_CLIENT_ID=your-client-id
SPOTIFY_CLIENT_SECRET=your-client-secret
DATABASE_URL=your-db-url
```

---

# ⚡ Makefile Commands

The project includes helper Makefile commands for easier Docker management.

## ▶ Start Default Environment

```bash
make up
```

---

## 🧪 Run Mongo Environment

```bash
make up-mongo
```

---
## 🧪 Run Hybrid Environment (Mongo + Redis)

```bash
make up-hybrid
```

---

## 🛑 Stop Containers

```bash
make down
```

---

# 🐳 Manual Docker Commands

## Build and Start Containers

```bash
docker compose up --build
```

Detached mode:

```bash
docker compose up -d --build
```

---

## Stop Containers

```bash
docker compose down
```

---

## View Logs

```bash
docker compose logs -f
```

---

# 🔌 API Access

Once running:

| Service | URL |
|---------|-----|
| FastAPI | http://localhost:8000 |
| Swagger Docs | http://localhost:8000/docs |

---

# 🧹 Cleanup

Remove containers, networks, and volumes:

```bash
docker compose down -v
```

---

# 📚 Notes

- Docker setup includes all required runtime dependencies.
- FFmpeg is already installed inside the container.
- Recommended for development and deployment.