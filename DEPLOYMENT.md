# Deployment Guide

This guide covers deploying Company Intelligence Tracker to production environments.

## Table of Contents

1. [Local Docker Deployment](#local-docker-deployment)
2. [Cloud Deployment](#cloud-deployment)
3. [Environment Configuration](#environment-configuration)
4. [Scaling & Performance](#scaling--performance)
5. [Monitoring & Logging](#monitoring--logging)
6. [Backup & Recovery](#backup--recovery)

## Local Docker Deployment

### Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- 2GB RAM minimum (4GB recommended)

### Step 1: Configure Environment

```bash
cp backend/.env.example backend/.env
```

Edit `backend/.env`:
```bash
TAVILY_API_KEY=your_key_here
FIRECRAWL_API_KEY=your_key_here
CORS_ORIGINS=http://localhost:3000
```

### Step 2: Build & Run

```bash
# Build images
docker compose build

# Run services
docker compose up -d

# Verify services
docker compose ps

# Check logs
docker compose logs -f frontend
docker compose logs -f backend
```

### Step 3: Verify Deployment

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

```bash
# Health check
curl http://localhost:8000/api/health
```

### Step 4: Shutdown

```bash
docker compose down
```

## Cloud Deployment

### Azure Container Apps

Prerequisites: Azure CLI, subscription

```bash
# Set variables
export RESOURCE_GROUP="scrapeflow-rg"
export LOCATION="eastus"
export REGISTRY_NAME="scrapeflowregistry"

# Create resource group
az group create \
  --name $RESOURCE_GROUP \
  --location $LOCATION

# Create container registry
az acr create \
  --resource-group $RESOURCE_GROUP \
  --name $REGISTRY_NAME \
  --sku Basic

# Build and push images
az acr build \
  --registry $REGISTRY_NAME \
  --image scrapeflow-backend:latest \
  ./backend

az acr build \
  --registry $REGISTRY_NAME \
  --image scrapeflow-frontend:latest \
  ./frontend

# Create Container Apps environment
az containerapp env create \
  --name scrapeflow-env \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION

# Deploy backend
az containerapp create \
  --name scrapeflow-backend \
  --resource-group $RESOURCE_GROUP \
  --environment scrapeflow-env \
  --image $REGISTRY_NAME.azurecr.io/scrapeflow-backend:latest \
  --target-port 8000 \
  --ingress external \
  --registry-server $REGISTRY_NAME.azurecr.io \
  --env-vars \
    TAVILY_API_KEY=@tavily-key \
    FIRECRAWL_API_KEY=@firecrawl-key \
    CORS_ORIGINS="https://scrapeflow-frontend.azurecontainerapps.io"

# Deploy frontend
az containerapp create \
  --name scrapeflow-frontend \
  --resource-group $RESOURCE_GROUP \
  --environment scrapeflow-env \
  --image $REGISTRY_NAME.azurecr.io/scrapeflow-frontend:latest \
  --target-port 3000 \
  --ingress external \
  --registry-server $REGISTRY_NAME.azurecr.io \
  --env-vars \
    NEXT_PUBLIC_API_URL="https://scrapeflow-backend.azurecontainerapps.io"
```

### AWS (ECS/Fargate)

Prerequisites: AWS CLI, ECR repository

```bash
# Build and push to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin [account].dkr.ecr.us-east-1.amazonaws.com

docker build -t scrapeflow-backend:latest ./backend
docker tag scrapeflow-backend:latest [account].dkr.ecr.us-east-1.amazonaws.com/scrapeflow-backend:latest
docker push [account].dkr.ecr.us-east-1.amazonaws.com/scrapeflow-backend:latest

# Similar for frontend
```

### Vercel (Frontend Only)

```bash
cd frontend
npm install -g vercel
vercel deploy --prod

# Set environment variables in Vercel dashboard
# NEXT_PUBLIC_API_URL=https://api.yourdomain.com
```

## Environment Configuration

### Production Environment Variables

**Backend:**
```bash
TAVILY_API_KEY=<production-key>
FIRECRAWL_API_KEY=<production-key>
CORS_ORIGINS=https://yourdomain.com
LOG_LEVEL=info
```

**Frontend:**
```bash
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
NEXT_PUBLIC_DEBUG=false
NEXT_PUBLIC_API_TIMEOUT=30000
```

### Secrets Management

Use cloud provider's secret management:

**Azure Key Vault:**
```bash
az keyvault secret set \
  --vault-name scrapeflow-kv \
  --name TAVILY-API-KEY \
  --value your-key
```

**AWS Secrets Manager:**
```bash
aws secretsmanager create-secret \
  --name scrapeflow/tavily-api-key \
  --secret-string your-key
```

## Scaling & Performance

### Horizontal Scaling

```yaml
# docker-compose.yml - add replicas
services:
  backend:
    deploy:
      replicas: 3
  frontend:
    deploy:
      replicas: 2
```

### Load Balancing

Use nginx or cloud provider's load balancer:

```bash
# nginx example
docker run -d \
  -p 80:80 \
  -v $(pwd)/nginx.conf:/etc/nginx/nginx.conf \
  nginx:latest
```

### Caching Strategy

Implement Redis for performance:

```yaml
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
```

## Monitoring & Logging

### Logs

View logs from running services:

```bash
# Docker
docker compose logs -f --tail 100 backend

# Kubernetes
kubectl logs deployment/scrapeflow-backend -f

# Cloud provider
az monitor log-analytics query \
  --workspace scrapeflow-logs \
  --analytics-query "AppServiceHTTPLogs | limit 100"
```

### Metrics

Monitor key metrics:

- Response time
- Error rate
- CPU/Memory usage
- API quota usage

### Health Checks

Implemented in docker-compose.yml:

```bash
curl http://localhost:8000/api/health
curl http://localhost:3000/
```

### Alerting

Set up alerts for:

- Service down
- High error rate (>5%)
- High latency (>5s)
- API quota warnings

## Backup & Recovery

### Database Backup (if using)

```bash
# Regular backups (cron job)
0 2 * * * /scripts/backup.sh

# Manual backup
docker exec scrapeflow-backend \
  pg_dump scrapeflow_db > backup.sql
```

### Configuration Backup

```bash
# Backup secrets
az keyvault backup create \
  --vault-name scrapeflow-kv \
  --file backup.blob

# Backup environment files
tar czf config-backup.tar.gz backend/.env frontend/.env.local
```

### Disaster Recovery Plan

1. **RTO Target**: 1 hour
2. **RPO Target**: 15 minutes
3. **Failover**: Automated to backup region
4. **Restore Process**: Documented and tested monthly

## Troubleshooting

### Service Won't Start

```bash
# Check logs
docker compose logs backend frontend

# Validate configuration
docker compose config

# Rebuild services
docker compose build --no-cache
```

### High Memory Usage

```bash
# Monitor
docker stats

# Reduce replicas
docker compose down backend
docker compose up -d --scale backend=1
```

### API Errors

```bash
# Check backend logs
docker compose logs backend | grep ERROR

# Test endpoint
curl -v http://localhost:8000/api/health

# Check env vars
docker compose exec backend env | grep -i key
```

## Production Checklist

- [ ] Environment variables configured
- [ ] API keys secured (using secrets manager)
- [ ] HTTPS enabled
- [ ] Health checks passing
- [ ] Backups tested
- [ ] Monitoring alerts set up
- [ ] Team has access to logs
- [ ] Disaster recovery plan documented
- [ ] Load testing completed
- [ ] Security scan passed
