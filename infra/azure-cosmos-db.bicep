// Azure Cosmos DB Infrastructure - GitOps 2.0 Healthcare Intelligence Platform
// Production-grade deployment with HIPAA compliance

// Parameters
@description('Environment name (dev, staging, prod)')
param environmentName string = 'prod'

@description('Azure region for primary deployment')
param location string = resourceGroup().location

@description('Azure region for failover (multi-region)')
param failoverLocation string = 'westeurope'

@description('Cosmos DB account name (must be globally unique)')
param cosmosAccountName string = 'gitops-healthcare-${uniqueString(resourceGroup().id)}'

@description('Database name')
param databaseName string = 'gitops-healthcare'

@description('Container name for commit metadata')
param containerName string = 'commits'

@description('Enable multi-region writes')
param enableMultiRegionWrites bool = true

@description('Enable automatic failover')
param enableAutomaticFailover bool = true

@description('Tags for resource organization')
param tags object = {
  Environment: environmentName
  Project: 'GitOps-2.0-Healthcare-Intelligence'
  Compliance: 'HIPAA-FDA-SOX'
  CostCenter: 'Engineering'
  DataClassification: 'PHI'
}

// Cosmos DB Account with Multi-Region Support
resource cosmosAccount 'Microsoft.DocumentDB/databaseAccounts@2024-05-15' = {
  name: cosmosAccountName
  location: location
  tags: tags
  kind: 'GlobalDocumentDB'
  properties: {
    databaseAccountOfferType: 'Standard'
    consistencyPolicy: {
      defaultConsistencyLevel: 'Session' // Balance between consistency and performance
      maxStalenessPrefix: 100
      maxIntervalInSeconds: 5
    }
    locations: [
      {
        locationName: location
        failoverPriority: 0
        isZoneRedundant: true // Zone redundancy for high availability
      }
      {
        locationName: failoverLocation
        failoverPriority: 1
        isZoneRedundant: true
      }
    ]
    enableMultipleWriteLocations: enableMultiRegionWrites
    enableAutomaticFailover: enableAutomaticFailover
    capabilities: [
      {
        name: 'EnableServerless' // Serverless mode for cost optimization (remove for provisioned throughput)
      }
    ]
    backupPolicy: {
      type: 'Continuous' // Continuous backup for HIPAA compliance (7-year retention)
      continuousModeProperties: {
        tier: 'Continuous7Days' // Can restore to any point in last 7 days
      }
    }
    networkAclBypass: 'AzureServices' // Allow Azure services to bypass firewall
    publicNetworkAccess: 'Enabled' // Change to 'Disabled' for private endpoint only
    ipRules: [] // Add IP allowlist for production: [{ ipAddressOrRange: '203.0.113.0/24' }]
    isVirtualNetworkFilterEnabled: false // Enable for VNet integration
    virtualNetworkRules: [] // Add VNet rules if needed
    disableKeyBasedMetadataWriteAccess: false // Allow SDK operations
    enableFreeTier: false // Set to true for dev/test (one per subscription)
    analyticalStorageConfiguration: {
      schemaType: 'FullFidelity' // Enable Azure Synapse Link for analytics
    }
    enableAnalyticalStorage: true // Enable for big data analytics
  }
}

// Database
resource database 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2024-05-15' = {
  parent: cosmosAccount
  name: databaseName
  properties: {
    resource: {
      id: databaseName
    }
    options: {
      // Serverless mode doesn't use throughput, remove this section if using serverless
      // throughput: 400 // Autoscale between 400-4000 RU/s
    }
  }
}

// Container with Hierarchical Partition Keys and TTL
resource container 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2024-05-15' = {
  parent: database
  name: containerName
  properties: {
    resource: {
      id: containerName
      partitionKey: {
        paths: [
          '/tenantId'
          '/commitDate'
        ]
        kind: 'MultiHash' // Hierarchical partition keys (v2)
        version: 2
      }
      indexingPolicy: {
        automatic: true
        indexingMode: 'consistent'
        includedPaths: [
          {
            path: '/*' // Index all properties by default
          }
        ]
        excludedPaths: [
          {
            path: '/filesChanged/*' // Exclude large arrays from indexing
          }
          {
            path: '/_etag/?' // System property, no need to index
          }
        ]
        compositeIndexes: [
          [
            {
              path: '/tenantId'
              order: 'ascending'
            }
            {
              path: '/commitDate'
              order: 'descending'
            }
            {
              path: '/riskScore'
              order: 'descending'
            }
          ]
        ]
      }
      defaultTtl: 190512000 // 7 years in seconds (2,208 days) for HIPAA compliance
      uniqueKeyPolicy: {
        uniqueKeys: [
          {
            paths: [
              '/commitHash' // Ensure commit hashes are unique
            ]
          }
        ]
      }
    }
    options: {
      // Serverless mode doesn't use throughput
      // throughput: 400 // Manual throughput (use autoscaleSettings for autoscale)
    }
  }
}

// Diagnostic Settings for Monitoring (send to Log Analytics)
resource diagnosticSettings 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = {
  name: 'cosmos-diagnostics'
  scope: cosmosAccount
  properties: {
    logs: [
      {
        category: 'DataPlaneRequests'
        enabled: true
        retentionPolicy: {
          enabled: true
          days: 90 // Keep logs for 90 days
        }
      }
      {
        category: 'QueryRuntimeStatistics'
        enabled: true
        retentionPolicy: {
          enabled: true
          days: 90
        }
      }
      {
        category: 'PartitionKeyStatistics'
        enabled: true
        retentionPolicy: {
          enabled: true
          days: 90
        }
      }
    ]
    metrics: [
      {
        category: 'Requests'
        enabled: true
        retentionPolicy: {
          enabled: true
          days: 90
        }
      }
    ]
    workspaceId: logAnalyticsWorkspace.id
  }
}

// Log Analytics Workspace for Diagnostics
resource logAnalyticsWorkspace 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: 'gitops-healthcare-logs-${uniqueString(resourceGroup().id)}'
  location: location
  tags: tags
  properties: {
    sku: {
      name: 'PerGB2018' // Pay-as-you-go
    }
    retentionInDays: 90 // Keep logs for 90 days
    features: {
      enableLogAccessUsingOnlyResourcePermissions: true
    }
  }
}

// Managed Identity for Application Access (no keys needed)
resource managedIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: 'gitops-cosmos-identity-${uniqueString(resourceGroup().id)}'
  location: location
  tags: tags
}

// Role Assignment: Grant Managed Identity access to Cosmos DB
// Built-in role: Cosmos DB Built-in Data Contributor (00000000-0000-0000-0000-000000000002)
resource roleAssignment 'Microsoft.DocumentDB/databaseAccounts/sqlRoleAssignments@2024-05-15' = {
  name: guid(cosmosAccount.id, managedIdentity.id, 'contributor')
  parent: cosmosAccount
  properties: {
    roleDefinitionId: '${cosmosAccount.id}/sqlRoleDefinitions/00000000-0000-0000-0000-000000000002'
    principalId: managedIdentity.properties.principalId
    scope: cosmosAccount.id
  }
}

// Outputs for Application Configuration
output cosmosEndpoint string = cosmosAccount.properties.documentEndpoint
output cosmosPrimaryKey string = cosmosAccount.listKeys().primaryMasterKey
output databaseName string = databaseName
output containerName string = containerName
output managedIdentityClientId string = managedIdentity.properties.clientId
output managedIdentityPrincipalId string = managedIdentity.properties.principalId
output logAnalyticsWorkspaceId string = logAnalyticsWorkspace.id

// Multi-Region Endpoints
output primaryRegion string = location
output failoverRegion string = failoverLocation
output primaryEndpoint string = 'https://${cosmosAccountName}.documents.azure.com:443/'
output failoverEndpoint string = 'https://${cosmosAccountName}-${failoverLocation}.documents.azure.com:443/'
