# AIToday Deployment Guide

This guide explains how to deploy the AIToday application using Docker and Docker Compose.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) installed on your server.
- [Docker Compose](https://docs.docker.com/compose/install/) installed.

## Quick Start

1.  **Clone the repository** (if not already done):
    ```bash
    git clone <your-repo-url>
    cd AIToday
    ```

2.  **Configure Environment Variables**:
    The `docker-compose.yaml` uses default values, but for production, you should set them. You can create a `.env` file in the root directory:
    ```env
    POSTGRES_USER=your_db_user
    POSTGRES_PASSWORD=your_db_password
    POSTGRES_DB=aitoday
    # Add your API keys here if needed by the backend
    OPENAI_API_KEY=sk-...
    ```

3.  **Build and Start**:
    ```bash
    docker compose up -d --build
    ```

4.  **Verify Deployment**:
    - Frontend: http://localhost:3000
    - Backend API: http://localhost:8000/docs

## Configuration Details

### Backend
- **Port**: 8000
- **CORS**: By default, it allows `http://localhost:3000`. To change this, set `BACKEND_CORS_ORIGINS` in `docker-compose.yaml` or `.env`.
  ```yaml
  environment:
    - BACKEND_CORS_ORIGINS=["https://your-domain.com"]
  ```

### Frontend
- **Port**: 3000
- **API URL**: The frontend connects to the backend via `NEXT_PUBLIC_API_URL`. In `docker-compose.yaml`, it is set to `http://localhost:8000/api/v1`. If you are deploying to a remote server, update this to your server's public IP or domain.

## Troubleshooting

- **Logs**: Check logs for any service:
  ```bash
  docker compose logs -f backend
  docker compose logs -f frontend
  ```
- **Rebuild**: If you make code changes, rebuild the containers:
  ```bash
  docker compose up -d --build
  ```
