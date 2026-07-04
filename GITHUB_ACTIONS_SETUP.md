# GitHub Actions Secrets Setup

## 📋 Configuration Guide for Phase 6 CI/CD

### Step 1: Navigate to GitHub Repository Settings

1. Go to your GitHub repository
2. Click **Settings** (gear icon, top right)
3. Click **Secrets and variables** → **Actions** (left sidebar)

---

## 🔐 Secrets to Configure

### Option A: GitHub Container Registry (RECOMMENDED - No additional setup needed)

**Why**: Uses built-in `GITHUB_TOKEN` (auto-configured)

```
GitHub automatically provides:
- GITHUB_TOKEN (auto-provided)
- Registry: ghcr.io
- Username: github.actor (your username)
- Password: GITHUB_TOKEN (already set)

✅ No manual secrets needed!
```

**Images will push to**:
```
ghcr.io/your-username/pine-sales-ai/backend:latest
ghcr.io/your-username/pine-sales-ai/backend:main-sha-abcd1234
```

---

### Option B: Docker Hub (Optional - if you prefer Docker Hub)

**Create Docker Hub credentials**:

1. Go to [Docker Hub](https://hub.docker.com)
2. Create account if needed
3. Generate Personal Access Token:
   - Profile → Account Settings → Security
   - Create Access Token (copy & save)

**Add to GitHub Secrets**:

| Secret Name | Value |
|---|---|
| `DOCKER_USERNAME` | Your Docker Hub username |
| `DOCKER_PASSWORD` | Your Personal Access Token (NOT password) |

**Update workflow**: Change registry to `docker.io` in workflow file

---

### Option C: Azure Container Registry (For production)

**Prerequisites**: Azure subscription + Azure CLI

**Create ACR**:
```bash
az acr create \
  --resource-group mygroup \
  --name myregistry \
  --sku Basic
```

**Get credentials**:
```bash
az acr credential show \
  --resource-group mygroup \
  --name myregistry
```

**Add to GitHub Secrets**:

| Secret Name | Value |
|---|---|
| `ACR_LOGIN_SERVER` | `myregistry.azurecr.io` |
| `ACR_USERNAME` | Username from credential show |
| `ACR_PASSWORD` | Password from credential show |

**Update workflow**: 
```yaml
registry: ${{ secrets.ACR_LOGIN_SERVER }}
username: ${{ secrets.ACR_USERNAME }}
password: ${{ secrets.ACR_PASSWORD }}
```

---

## ✅ Quick Setup (Recommended Path)

### Using GitHub Container Registry (No extra steps!)

1. ✅ **Your `.github/workflows/ci-cd.yml` is ready to use**
2. ✅ **GITHUB_TOKEN is auto-configured**
3. ✅ **Push to main branch**
4. ✅ **Watch Actions run** (Settings → Actions)

**Result**: Image appears at `ghcr.io/your-username/pine-sales-ai/backend:latest`

---

## 🧪 Test the Workflow

### 1. Create a test branch
```bash
git checkout -b test/ci-cd
git push origin test/ci-cd
```

### 2. Create a Pull Request
```
Create PR from test/ci-cd → main
GitHub Actions will:
  - Run linting (flake8, black)
  - Run tests (6/6 E2E + 7/7 Dashboard)
  - Show results in PR
```

### 3. Merge to main (after tests pass)
```bash
# After PR approved
git merge test/ci-cd main
git push origin main
```

### 4. Watch build & push
```
GitHub Actions will:
  - Build Docker image (multi-stage)
  - Push to ghcr.io
  - Scan for vulnerabilities
  - Send summary
```

---

## 🔍 Verify Image Push

### Check GitHub Container Registry

1. Go to your GitHub profile
2. Click **Packages** (top navigation)
3. Find **backend** package
4. View image tags and details

### Pull image locally (when Docker available)

```bash
docker login ghcr.io -u your-username -p your-github-token

docker pull ghcr.io/your-username/pine-sales-ai/backend:latest

docker run -p 8000:8000 ghcr.io/your-username/pine-sales-ai/backend:latest
```

---

## 📊 GitHub Actions Dashboard

### View Workflow Runs

1. Go to repository
2. Click **Actions** (top navigation)
3. See all workflow runs
4. Click run to see:
   - ✅ Job status
   - 📋 Logs for each step
   - 🐛 Errors if any

### Common Workflow Views

```
✅ All checks passed
🟡 In progress
❌ Failed
⏭️ Skipped (didn't meet conditions)
```

---

## 🚀 Environment Variables

**Available in workflow** (no secrets needed):

```yaml
REGISTRY: ghcr.io
IMAGE_NAME: ${{ github.repository }}/backend
```

**Available from GitHub context**:
```yaml
github.actor         # Your username
github.ref           # Branch name (refs/heads/main)
github.sha           # Commit SHA
github.repository    # owner/repo
```

---

## 🔒 Security Best Practices

1. ✅ **Never commit secrets** to git
2. ✅ **Use GitHub Secrets** for all credentials
3. ✅ **Rotate tokens regularly** (every 30-90 days)
4. ✅ **Use read-only tokens** when possible
5. ✅ **Audit secret usage** in Actions logs
6. ✅ **Enable secret masking** in logs (auto-done by GitHub)

---

## ⚙️ Workflow Triggers

Current workflow runs on:

| Event | Branch | Trigger |
|---|---|---|
| **Push** | main | Runs all jobs (lint, test, build, push, scan) |
| **Push** | develop | Runs lint, test, build only (no push to registry) |
| **Pull Request** | → main | Runs lint, test only (no build/push) |

**To customize triggers**, edit `.github/workflows/ci-cd.yml`:

```yaml
on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 2 * * *'  # Daily scan at 2 AM UTC
```

---

## 🐛 Troubleshooting

### Workflow not running
- ✅ Check branch name (must be exactly `main` or `develop`)
- ✅ Verify `.github/workflows/ci-cd.yml` committed
- ✅ Check repository settings → Actions enabled

### Tests failing in CI
- ✅ Run locally: `pytest tests/ -v`
- ✅ Check database connection in workflow
- ✅ Verify all dependencies in `requirements.txt`

### Image push failing
- ✅ Verify GITHUB_TOKEN has `packages:write` permission (auto-configured)
- ✅ Check image name format (must include registry)
- ✅ Verify not exceeding storage quota

### Secrets not accessible
- ✅ Verify secret name matches `${{ secrets.SECRET_NAME }}`
- ✅ Check secret exists in Settings → Secrets
- ✅ Confirm repository has access to secret (org-level secrets)

---

## 📞 Next Steps

### After Workflow Runs Successfully

1. ✅ Verify image in GitHub Container Registry
2. ✅ Pull image locally (when Docker available)
3. ✅ Test deployment to Azure Container Instances
4. ✅ Set up monitoring and alerting
5. ✅ Configure auto-deployment to production

### Phase 6 Completion Checklist

- [ ] GitHub Actions workflow implemented
- [ ] Secrets configured (or using auto GITHUB_TOKEN)
- [ ] First workflow run successful
- [ ] Image pushed to registry
- [ ] Security scan completed
- [ ] Branch protection enabled
- [ ] Status checks required on PRs

---

## 🎓 Learning Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Docker Build and Push Action](https://github.com/docker/build-push-action)
- [Container Registry Setup](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)
- [Trivy Vulnerability Scanner](https://github.com/aquasecurity/trivy-action)

---

**Status**: ✅ **READY TO TEST**

Workflow file: `.github/workflows/ci-cd.yml`  
Secrets needed: ✅ None (GITHUB_TOKEN auto-configured)  
Next: Push to main branch and watch it build! 🚀
