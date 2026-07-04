# Phase 6: CI/CD Pipeline & Automation

## Overview

Phase 6 automates testing, building, and deployment workflows. After Phase 5's Docker containerization, Phase 6 ensures:

✅ **Automated Testing** - Run tests on every push  
✅ **Docker Image Build** - Build & push to registry on merge  
✅ **Environment Parity** - Deploy consistent images across dev/prod  
✅ **Quality Gates** - Block broken code from merging  

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│           GitHub / GitLab / Azure DevOps                 │
│                                                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │  CI/CD Pipeline (on push/PR)                       │ │
│  │                                                    │ │
│  │  1. Checkout code                                 │ │
│  │  2. Run linting (flake8, black)                   │ │
│  │  3. Run type checking (mypy)                      │ │
│  │  4. Run tests (pytest - 6/6 E2E + dashboard)      │ │
│  │  5. Build Docker image                            │ │
│  │  6. Scan image for vulnerabilities (Trivy)        │ │
│  │  7. Push to registry (on merge to main)           │ │
│  │  8. Deploy to staging (optional)                  │ │
│  │                                                    │ │
│  └────────────────────────────────────────────────────┘ │
│                           ↓                              │
│  ┌────────────────────────────────────────────────────┐ │
│  │  Container Registry (Docker Hub / ACR / ECR)      │ │
│  │                                                    │ │
│  │  pine-sales-ai-backend:latest                     │ │
│  │  pine-sales-ai-backend:v1.0.0                     │ │
│  │                                                    │ │
│  └────────────────────────────────────────────────────┘ │
│                           ↓                              │
│  ┌────────────────────────────────────────────────────┐ │
│  │  Deployment (Manual / Automated)                  │ │
│  │                                                    │ │
│  │  Staging → Production                             │ │
│  │  (Azure Container Instances / AKS / etc.)         │ │
│  │                                                    │ │
│  └────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

---

## Phase 6 Tasks

### 6.1: GitHub Actions Workflow (Recommended)

Create `.github/workflows/ci-cd.yml`:

```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}/backend

jobs:
  # ========== LINTING & TYPE CHECKING ==========
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
          cache: 'pip'
      
      - name: Install dependencies
        run: |
          pip install --upgrade pip
          pip install -r backend/requirements.txt
          pip install flake8 black mypy
      
      - name: Lint with flake8
        run: flake8 backend/ --count --select=E9,F63,F7,F82 --show-source --statistics
      
      - name: Check formatting with black
        run: black --check backend/
      
      - name: Type check with mypy
        run: mypy backend/ --ignore-missing-imports || true
  
  # ========== TESTING ==========
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15-alpine
        env:
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: pine_sales_ai_test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
          cache: 'pip'
      
      - name: Install dependencies
        run: |
          pip install --upgrade pip
          pip install -r backend/requirements.txt
      
      - name: Run pytest
        env:
          DATABASE_URL: postgresql+asyncpg://postgres:postgres@localhost:5432/pine_sales_ai_test
        run: |
          cd backend
          pytest tests/test_e2e_flows.py -v --tb=short
          pytest tests/test_dashboard.py -v --tb=short
  
  # ========== BUILD & PUSH DOCKER IMAGE ==========
  build-and-push:
    runs-on: ubuntu-latest
    needs: [lint, test]
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    permissions:
      contents: read
      packages: write
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2
      
      - name: Log in to Container Registry
        uses: docker/login-action@v2
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      
      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v4
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=ref,event=branch
            type=semver,pattern={{version}}
            type=sha,prefix={{branch}}-
            type=raw,value=latest,enable={{is_default_branch}}
      
      - name: Build and push Docker image
        uses: docker/build-push-action@v4
        with:
          context: ./backend
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=registry,ref=${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:buildcache
          cache-to: type=registry,ref=${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:buildcache,mode=max
  
  # ========== SECURITY SCANNING ==========
  security-scan:
    runs-on: ubuntu-latest
    needs: build-and-push
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    
    steps:
      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:latest
          format: 'sarif'
          output: 'trivy-results.sarif'
      
      - name: Upload Trivy results to GitHub Security tab
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: 'trivy-results.sarif'
```

### 6.2: Container Registry Setup

**Option 1: Docker Hub** (Free, Public)
```bash
docker login
docker tag pine-sales-ai-backend:latest <username>/pine-sales-ai-backend:latest
docker push <username>/pine-sales-ai-backend:latest
```

**Option 2: GitHub Container Registry** (Free with GitHub)
```bash
docker login ghcr.io
docker tag pine-sales-ai-backend:latest ghcr.io/<org>/pine-sales-ai-backend:latest
docker push ghcr.io/<org>/pine-sales-ai-backend:latest
```

**Option 3: Azure Container Registry** (Production)
```bash
az acr create --resource-group mygroup --name myregistry --sku Basic
az acr build --registry myregistry --image pine-sales-ai-backend:latest .
```

### 6.3: Deployment Automation

#### Deploy to Azure Container Instances
```bash
az container create \
  --resource-group mygroup \
  --name pine-sales-ai \
  --image myregistry.azurecr.io/pine-sales-ai-backend:latest \
  --environment-variables \
    DATABASE_URL="postgresql+asyncpg://..." \
    ENV=production \
  --ports 8000 \
  --memory 1
```

#### Deploy to Kubernetes (AKS)
```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: pine-sales-ai-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: pine-sales-ai
  template:
    metadata:
      labels:
        app: pine-sales-ai
    spec:
      containers:
      - name: backend
        image: myregistry.azurecr.io/pine-sales-ai-backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: connection-string
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

---

## Phase 6 Deliverables

### Files to Create:
- ✅ `.github/workflows/ci-cd.yml` - GitHub Actions workflow
- ✅ `.dockerignore` - Already created in Phase 5
- ✅ `Dockerfile` - Already created in Phase 5
- ✅ `requirements.txt` - Already exists
- ✅ `pytest.ini` - Already exists

### Secrets to Configure:
- `DOCKER_HUB_TOKEN` - Docker Hub authentication (if using DockerHub)
- `REGISTRY_PASSWORD` - ACR password (if using Azure)
- `GITHUB_TOKEN` - Auto-provided by GitHub

### Quality Gates to Enable:
- ✅ Branch protection: Require PR reviews
- ✅ Status checks: Pass linting, tests, build
- ✅ Auto-merge: Merge after checks pass

---

## Phase 6 Success Criteria

- [ ] **Linting Pass**: flake8 + black check all Python files
- [ ] **Type Check Pass**: mypy validation with <5% ignored errors
- [ ] **All Tests Pass**: 6/6 E2E tests + 7/7 dashboard tests in CI
- [ ] **Docker Build**: Image builds in <5 min, size <600MB
- [ ] **Security Scan**: Zero critical vulnerabilities
- [ ] **Image Push**: Auto-push to registry on merge to main
- [ ] **Deployment**: One-command deploy to staging/production

---

## Phase 6 Timeline

| Task | Duration | Dependencies |
|------|----------|--------------|
| Set up GitHub Actions | 30 min | Phase 5 complete |
| Configure container registry | 15 min | GitHub Actions ready |
| Write deployment scripts | 45 min | Registry configured |
| Test full pipeline (dry-run) | 30 min | Deployment scripts ready |
| Enable branch protection | 15 min | All tests green |
| **Total Phase 6** | **~2.5 hours** | - |

---

## Next Steps After Phase 6

### Phase 7: Production Deployment
1. Deploy to Azure Container Instances or AKS
2. Configure SSL/TLS certificates
3. Set up monitoring & alerting
4. Configure auto-scaling
5. Enable health checks and recovery

### Continuous Improvement
1. Add performance benchmarks to CI
2. Add integration tests for Supabase
3. Add E2E tests for frontend (Playwright/Cypress)
4. Set up observability (Application Insights, Datadog)
5. Implement feature flags and canary deployments

---

## Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Azure Container Registry](https://docs.microsoft.com/azure/container-registry/)
- [Kubernetes Deployment Guide](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/)

---

**Phase 6 Status**: 📋 **READY FOR IMPLEMENTATION** (after Phase 5)

All Phase 5 artifacts complete. Docker containerization ready.  
Next: Implement CI/CD automation workflow.
