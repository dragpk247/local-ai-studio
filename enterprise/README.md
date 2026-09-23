# Local AI Studio - Enterprise Edition

This directory contains the Docker configuration needed to deploy **Local AI Studio** as a centralized, multi-tenant web application on a Linux server, virtual machine, or cloud cluster.

## Prerequisites
- Docker
- Docker Compose

## How to Deploy
1. Ensure your centralized AI inference server (e.g., an enterprise Ollama server, or vLLM) is running and accessible over the network.
2. In the `docker-compose.yml` file, configure `OLLAMA_BASE_URL` to point to your centralized inference server. By default, it uses `http://host.docker.internal:11434` which attempts to connect to an Ollama daemon running on the host machine.
3. Run the following command from the `enterprise/` directory:
```bash
docker-compose up -d --build
```
4. Access the web interface at `http://your-server-ip:8501`.

## Future Enterprise Enhancements (Next Steps)
- **Authentication**: Add an Identity-Aware Proxy (IAP) or OAuth2-Proxy container to the `docker-compose.yml` to secure the dashboard behind Single Sign-On (Okta/Microsoft Entra).
- **PostgreSQL**: Swap the local DuckDB volume for a dedicated PostgreSQL container to support robust concurrent SQL access.
- **Inference Cluster**: Swap the `OLLAMA_BASE_URL` from a local daemon to an enterprise-grade scalable endpoint (like a vLLM deployment).
