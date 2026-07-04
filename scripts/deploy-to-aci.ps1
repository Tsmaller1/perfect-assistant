# Deploy to Azure Container Instances (PowerShell)
# Usage: .\deploy-to-aci.ps1 -ResourceGroup "pine-sales-rg" -ContainerName "pine-sales-ai" `
#        -ImageUrl "ghcr.io/your-username/pine-sales-ai/backend:latest" `
#        -DatabaseUrl "postgresql+asyncpg://user:pass@host:5432/db"

param(
    [string]$ResourceGroup = "pine-sales-rg",
    [string]$ContainerName = "pine-sales-ai",
    [string]$ImageUrl = "ghcr.io/your-username/pine-sales-ai/backend:latest",
    [string]$DatabaseUrl = "postgresql+asyncpg://user:pass@host:5432/db",
    [string]$RegistryUsername = "your-username",
    [string]$RegistryPassword = "your-token",
    [string]$Region = "eastus"
)

Write-Host "🚀 Deploying to Azure Container Instances" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host "Resource Group: $ResourceGroup"
Write-Host "Container Name: $ContainerName"
Write-Host "Image: $ImageUrl"
Write-Host "Region: $Region"
Write-Host "Memory: 1GB, CPU: 1"
Write-Host ""

# Create resource group if not exists
Write-Host "📁 Creating resource group..." -ForegroundColor Blue
az group create `
    --name $ResourceGroup `
    --location $Region `
    --verbose

Write-Host ""
Write-Host "📦 Creating container instance..." -ForegroundColor Blue

# Extract registry from image URL
$RegistryServer = $ImageUrl.Split('/')[0]

# Deploy container
az container create `
    --resource-group $ResourceGroup `
    --name $ContainerName `
    --image $ImageUrl `
    --cpu 1 `
    --memory 1 `
    --registry-login-server $RegistryServer `
    --registry-username $RegistryUsername `
    --registry-password $RegistryPassword `
    --environment-variables `
        DATABASE_URL=$DatabaseUrl `
        ENV="production" `
        PYTHONUNBUFFERED="1" `
    --ports 8000 `
    --protocol TCP `
    --dns-name-label "pine-sales-ai" `
    --restart-policy OnFailure `
    --verbose

Write-Host ""
Write-Host "✅ Container deployed successfully!" -ForegroundColor Green
Write-Host ""

# Get container details
Write-Host "📊 Retrieving container details..." -ForegroundColor Blue
$FQDN = az container show `
    --resource-group $ResourceGroup `
    --name $ContainerName `
    --query ipAddress.fqdn `
    --output tsv

$IP = az container show `
    --resource-group $ResourceGroup `
    --name $ContainerName `
    --query ipAddress.ip `
    --output tsv

Write-Host ""
Write-Host "📍 Access your app:" -ForegroundColor Green
Write-Host "   URL: http://$FQDN`:8000"
Write-Host "   IP:  http://$IP`:8000"
Write-Host ""
Write-Host "🏥 Health check:" -ForegroundColor Green
Write-Host "   curl http://$FQDN`:8000/health"
Write-Host ""
Write-Host "📋 View logs:" -ForegroundColor Blue
Write-Host "   az container logs --resource-group $ResourceGroup --name $ContainerName --follow"
Write-Host ""
Write-Host "🛑 Delete container:" -ForegroundColor Yellow
Write-Host "   az container delete --resource-group $ResourceGroup --name $ContainerName --yes"
