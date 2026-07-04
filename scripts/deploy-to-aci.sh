#!/bin/bash
# Deploy to Azure Container Instances
# Usage: ./deploy-to-aci.sh <resource-group> <container-name> <image-url> <database-url>

set -e

# Configuration
RESOURCE_GROUP="${1:-pine-sales-rg}"
CONTAINER_NAME="${2:-pine-sales-ai}"
IMAGE_URL="${3:-ghcr.io/your-username/pine-sales-ai/backend:latest}"
DATABASE_URL="${4:-postgresql+asyncpg://user:pass@host:5432/db}"
REGISTRY_USERNAME="${5:-your-username}"
REGISTRY_PASSWORD="${6:-your-token}"

echo "🚀 Deploying to Azure Container Instances"
echo "=========================================="
echo "Resource Group: $RESOURCE_GROUP"
echo "Container Name: $CONTAINER_NAME"
echo "Image: $IMAGE_URL"
echo "Region: eastus (default)"
echo "Memory: 1GB"
echo "CPU: 1"
echo ""

# Create resource group if not exists
az group create \
  --name "$RESOURCE_GROUP" \
  --location eastus \
  --verbose

echo ""
echo "📦 Creating container instance..."

# Deploy container
az container create \
  --resource-group "$RESOURCE_GROUP" \
  --name "$CONTAINER_NAME" \
  --image "$IMAGE_URL" \
  --cpu 1 \
  --memory 1 \
  --registry-login-server "$(echo $IMAGE_URL | cut -d'/' -f1)" \
  --registry-username "$REGISTRY_USERNAME" \
  --registry-password "$REGISTRY_PASSWORD" \
  --environment-variables \
    DATABASE_URL="$DATABASE_URL" \
    ENV="production" \
    PYTHONUNBUFFERED="1" \
  --ports 8000 \
  --protocol TCP \
  --dns-name-label "pine-sales-ai" \
  --restart-policy OnFailure \
  --verbose

echo ""
echo "✅ Container deployed successfully!"
echo ""

# Get container details
FQDN=$(az container show \
  --resource-group "$RESOURCE_GROUP" \
  --name "$CONTAINER_NAME" \
  --query ipAddress.fqdn \
  --output tsv)

IP=$(az container show \
  --resource-group "$RESOURCE_GROUP" \
  --name "$CONTAINER_NAME" \
  --query ipAddress.ip \
  --output tsv)

echo "📍 Access your app:"
echo "   URL: http://$FQDN:8000"
echo "   IP:  http://$IP:8000"
echo ""
echo "🏥 Health check:"
echo "   curl http://$FQDN:8000/health"
echo ""
echo "📋 View logs:"
echo "   az container logs --resource-group $RESOURCE_GROUP --name $CONTAINER_NAME --follow"
echo ""
echo "🛑 Delete container:"
echo "   az container delete --resource-group $RESOURCE_GROUP --name $CONTAINER_NAME --yes"
