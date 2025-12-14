#!/usr/bin/env bash
# Deploy Azure Cosmos DB Infrastructure - GitOps 2.0 Healthcare Intelligence Platform
# Production deployment with HIPAA compliance
#
# Prerequisites:
#   - Azure CLI installed (az --version)
#   - Logged in to Azure (az login)
#   - Subscription selected (az account set --subscription <id>)
#   - Contributor role on target subscription
#
# Usage:
#   ./deploy_cosmos_db.sh [environment] [region]
#   ./deploy_cosmos_db.sh prod eastus
#   ./deploy_cosmos_db.sh staging westus2

set -euo pipefail

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT="${1:-prod}"
PRIMARY_REGION="${2:-eastus}"
FAILOVER_REGION="${3:-westeurope}"
RESOURCE_GROUP="gitops-healthcare-${ENVIRONMENT}-rg"
BICEP_FILE="infra/azure-cosmos-db.bicep"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Azure Cosmos DB Deployment${NC}"
echo -e "${BLUE}GitOps 2.0 Healthcare Intelligence${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Step 1: Validate Azure CLI
echo -e "${BLUE}[1/7] Validating Azure CLI...${NC}"
if ! command -v az &> /dev/null; then
    echo -e "${RED}❌ Azure CLI not found. Install from: https://aka.ms/install-azure-cli${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Azure CLI installed ($(az version --query '"azure-cli"' -o tsv))${NC}"

# Step 2: Check authentication
echo -e "\n${BLUE}[2/7] Checking Azure authentication...${NC}"
if ! az account show &> /dev/null; then
    echo -e "${RED}❌ Not logged in to Azure. Run: az login${NC}"
    exit 1
fi

SUBSCRIPTION_NAME=$(az account show --query name -o tsv)
SUBSCRIPTION_ID=$(az account show --query id -o tsv)
echo -e "${GREEN}✅ Logged in to Azure${NC}"
echo -e "   Subscription: ${SUBSCRIPTION_NAME}"
echo -e "   ID: ${SUBSCRIPTION_ID}"

# Step 3: Create resource group
echo -e "\n${BLUE}[3/7] Creating resource group...${NC}"
if az group show --name "$RESOURCE_GROUP" &> /dev/null; then
    echo -e "${YELLOW}⚠️  Resource group already exists: ${RESOURCE_GROUP}${NC}"
else
    az group create \
        --name "$RESOURCE_GROUP" \
        --location "$PRIMARY_REGION" \
        --tags \
            Environment="$ENVIRONMENT" \
            Project="GitOps-2.0-Healthcare-Intelligence" \
            Compliance="HIPAA-FDA-SOX" \
        --output none
    echo -e "${GREEN}✅ Resource group created: ${RESOURCE_GROUP}${NC}"
fi

# Step 4: Validate Bicep template
echo -e "\n${BLUE}[4/7] Validating Bicep template...${NC}"
if [ ! -f "$BICEP_FILE" ]; then
    echo -e "${RED}❌ Bicep file not found: ${BICEP_FILE}${NC}"
    exit 1
fi

az deployment group validate \
    --resource-group "$RESOURCE_GROUP" \
    --template-file "$BICEP_FILE" \
    --parameters \
        environmentName="$ENVIRONMENT" \
        location="$PRIMARY_REGION" \
        failoverLocation="$FAILOVER_REGION" \
    --output none

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Bicep template validated successfully${NC}"
else
    echo -e "${RED}❌ Bicep template validation failed${NC}"
    exit 1
fi

# Step 5: Deploy infrastructure
echo -e "\n${BLUE}[5/7] Deploying Azure Cosmos DB...${NC}"
echo -e "   Environment: ${ENVIRONMENT}"
echo -e "   Primary Region: ${PRIMARY_REGION}"
echo -e "   Failover Region: ${FAILOVER_REGION}"
echo -e "   ${YELLOW}This will take 5-10 minutes...${NC}"

DEPLOYMENT_NAME="cosmos-db-$(date +%Y%m%d-%H%M%S)"

az deployment group create \
    --resource-group "$RESOURCE_GROUP" \
    --template-file "$BICEP_FILE" \
    --name "$DEPLOYMENT_NAME" \
    --parameters \
        environmentName="$ENVIRONMENT" \
        location="$PRIMARY_REGION" \
        failoverLocation="$FAILOVER_REGION" \
    --output json > deployment_output.json

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Deployment completed: ${DEPLOYMENT_NAME}${NC}"
else
    echo -e "${RED}❌ Deployment failed. Check Azure Portal for details.${NC}"
    exit 1
fi

# Step 6: Extract outputs
echo -e "\n${BLUE}[6/7] Extracting deployment outputs...${NC}"

COSMOS_ENDPOINT=$(jq -r '.properties.outputs.cosmosEndpoint.value' deployment_output.json)
COSMOS_PRIMARY_KEY=$(jq -r '.properties.outputs.cosmosPrimaryKey.value' deployment_output.json)
DATABASE_NAME=$(jq -r '.properties.outputs.databaseName.value' deployment_output.json)
CONTAINER_NAME=$(jq -r '.properties.outputs.containerName.value' deployment_output.json)
MANAGED_IDENTITY_CLIENT_ID=$(jq -r '.properties.outputs.managedIdentityClientId.value' deployment_output.json)

echo -e "${GREEN}✅ Outputs extracted${NC}"
echo -e "   Cosmos Endpoint: ${COSMOS_ENDPOINT}"
echo -e "   Database: ${DATABASE_NAME}"
echo -e "   Container: ${CONTAINER_NAME}"
echo -e "   Managed Identity: ${MANAGED_IDENTITY_CLIENT_ID}"

# Step 7: Generate .env file
echo -e "\n${BLUE}[7/7] Generating .env file...${NC}"

cat > .env.cosmos << EOF
# Azure Cosmos DB Configuration - GitOps 2.0 Healthcare Intelligence
# Generated: $(date)
# Environment: ${ENVIRONMENT}

# Cosmos DB Connection (use managed identity in production)
COSMOS_ENDPOINT=${COSMOS_ENDPOINT}
COSMOS_KEY=${COSMOS_PRIMARY_KEY}
COSMOS_DATABASE=${DATABASE_NAME}
COSMOS_CONTAINER=${CONTAINER_NAME}

# Managed Identity (for production deployments)
AZURE_CLIENT_ID=${MANAGED_IDENTITY_CLIENT_ID}

# Multi-Region Endpoints
PRIMARY_REGION=${PRIMARY_REGION}
FAILOVER_REGION=${FAILOVER_REGION}

# Tenant Configuration
COSMOS_TENANT_ID=tenant-001

# Security: DO NOT commit this file to git
# Add to .gitignore: .env.cosmos
EOF

echo -e "${GREEN}✅ Configuration saved to: .env.cosmos${NC}"

# Summary
echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}Deployment Complete! 🎉${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "📋 Next Steps:"
echo -e "   1. Add .env.cosmos to .gitignore"
echo -e "   2. Test connection:"
echo -e "      ${BLUE}source .env.cosmos${NC}"
echo -e "      ${BLUE}python tools/azure_cosmos_store.py --test-store --test-query${NC}"
echo -e "   3. For production, use managed identity:"
echo -e "      ${BLUE}unset COSMOS_KEY${NC}"
echo -e "      ${BLUE}export AZURE_CLIENT_ID=${MANAGED_IDENTITY_CLIENT_ID}${NC}"
echo ""
echo -e "📊 Monitoring:"
echo -e "   - Azure Portal: ${BLUE}https://portal.azure.com/#@/resource${NC}"
echo -e "   - Cosmos DB Data Explorer: Query and browse data"
echo -e "   - Log Analytics: View diagnostics and performance"
echo ""
echo -e "🔐 Security:"
echo -e "   - Primary key stored in .env.cosmos (DO NOT COMMIT)"
echo -e "   - Use managed identity for production (no keys needed)"
echo -e "   - Enable firewall rules for production deployments"
echo ""
echo -e "💰 Cost Optimization:"
echo -e "   - Serverless mode: Pay per request (best for dev/test)"
echo -e "   - Provisioned throughput: Fixed cost (best for production)"
echo -e "   - Enable autoscale: 400-4000 RU/s for variable workloads"
echo ""
echo -e "${YELLOW}⚠️  Remember to delete resources when done:${NC}"
echo -e "   ${BLUE}az group delete --name ${RESOURCE_GROUP} --yes --no-wait${NC}"
echo ""

# Cleanup
rm -f deployment_output.json

exit 0
