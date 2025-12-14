#!/usr/bin/env python3
"""
Unit Tests for Azure Cosmos DB Storage - GitOps 2.0 Healthcare Intelligence Platform
Comprehensive testing with mocks for offline development

Test Coverage:
- Singleton pattern verification
- Commit storage with validation
- Query operations (by tenant, high-risk)
- TTL and partition key configuration
- Error handling and resilience
- Performance monitoring (slow query detection)

Usage:
    pytest tests/python/test_azure_cosmos_store.py -v
    pytest tests/python/test_azure_cosmos_store.py -v --cov=tools.azure_cosmos_store
"""

import asyncio
import os
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock

# Mock Azure SDK before importing our module
@pytest.fixture(autouse=True)
def mock_azure_cosmos():
    """Mock Azure Cosmos SDK for offline testing"""
    with patch.dict('sys.modules', {
        'azure.cosmos.aio': MagicMock(),
        'azure.cosmos': MagicMock(),
        'azure.identity.aio': MagicMock(),
    }):
        # Set flag to indicate SDK is available
        import tools.azure_cosmos_store as module
        module.COSMOS_AVAILABLE = True
        yield


@pytest.fixture
def mock_cosmos_client():
    """Mock Cosmos DB client with async methods"""
    client = AsyncMock()
    database = AsyncMock()
    container = AsyncMock()

    # Mock client methods - properly handle kwargs
    async def create_database(**kwargs):
        return database
    
    async def create_container(**kwargs):
        return container
    
    client.create_database_if_not_exists = create_database
    database.create_container_if_not_exists = create_container
    
    # Mock close method
    client.close = AsyncMock()

    # Mock container methods
    container.upsert_item = AsyncMock()
    container.query_items = AsyncMock()

    return {
        'client': client,
        'database': database,
        'container': container
    }


@pytest.fixture
def sample_commit():
    """Sample commit data for testing"""
    return {
        "commitHash": "a1b2c3d4e5f6g7h8",
        "message": "feat: add PHI encryption for patient records",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "author": "dev@example.com",
        "riskScore": 0.85,
        "compliance": ["HIPAA", "FDA"],
        "filesChanged": ["services/phi-service/encryption.py"],
        "linesAdded": 42,
        "linesDeleted": 8
    }


@pytest.fixture
def env_vars():
    """Set up environment variables for testing"""
    os.environ['COSMOS_ENDPOINT'] = 'https://test-account.documents.azure.com:443/'
    os.environ['COSMOS_KEY'] = 'test-key-12345'
    os.environ['COSMOS_DATABASE'] = 'gitops-healthcare-test'
    os.environ['COSMOS_CONTAINER'] = 'commits-test'
    os.environ['COSMOS_TENANT_ID'] = 'tenant-test-001'
    yield
    # Cleanup
    for key in ['COSMOS_ENDPOINT', 'COSMOS_KEY', 'COSMOS_DATABASE', 'COSMOS_CONTAINER', 'COSMOS_TENANT_ID']:
        os.environ.pop(key, None)


class TestAzureCosmosStoreInitialization:
    """Test suite for AzureCosmosStore initialization"""

    @pytest.mark.asyncio
    async def test_singleton_pattern(self, env_vars, mock_cosmos_client):
        """Test singleton pattern returns same instance"""
        from tools.azure_cosmos_store import AzureCosmosStore

        with patch('tools.azure_cosmos_store.CosmosClient', return_value=mock_cosmos_client['client']):
            # Reset singleton
            AzureCosmosStore._instance = None

            instance1 = await AzureCosmosStore.get_instance()
            instance2 = await AzureCosmosStore.get_instance()

            assert instance1 is instance2, "Singleton should return same instance"

            # Cleanup
            await instance1.close()
            AzureCosmosStore._instance = None

    @pytest.mark.asyncio
    async def test_initialization_with_env_vars(self, env_vars, mock_cosmos_client):
        """Test initialization reads environment variables"""
        from tools.azure_cosmos_store import AzureCosmosStore

        with patch('tools.azure_cosmos_store.CosmosClient', return_value=mock_cosmos_client['client']):
            AzureCosmosStore._instance = None

            store = await AzureCosmosStore.get_instance()

            assert store.endpoint == 'https://test-account.documents.azure.com:443/'
            assert store.database_name == 'gitops-healthcare-test'
            assert store.container_name == 'commits-test'
            assert store.tenant_id == 'tenant-test-001'

            await store.close()
            AzureCosmosStore._instance = None

    @pytest.mark.asyncio
    async def test_missing_endpoint_raises_error(self):
        """Test missing endpoint raises ValueError"""
        from tools.azure_cosmos_store import AzureCosmosStore

        # Clear environment
        os.environ.pop('COSMOS_ENDPOINT', None)

        with pytest.raises(ValueError, match="Cosmos DB endpoint not configured"):
            store = AzureCosmosStore()

    @pytest.mark.asyncio
    async def test_container_created_with_ttl(self, env_vars, mock_cosmos_client):
        """Test container created with 7-year TTL and partition keys"""
        from tools.azure_cosmos_store import AzureCosmosStore

        with patch('tools.azure_cosmos_store.CosmosClient', return_value=mock_cosmos_client['client']):
            AzureCosmosStore._instance = None

            store = await AzureCosmosStore.get_instance()

            # Verify container creation was called with correct properties
            mock_cosmos_client['database'].create_container_if_not_exists.assert_called_once()

            call_args = mock_cosmos_client['database'].create_container_if_not_exists.call_args
            assert call_args.kwargs['id'] == 'commits-test'
            assert call_args.kwargs['defaultTtl'] == 190_512_000  # 7 years

            # Verify hierarchical partition keys
            partition_key = call_args.kwargs['partitionKey']
            assert partition_key['paths'] == ['/tenantId', '/commitDate']
            assert partition_key['kind'] == 'MultiHash'

            await store.close()
            AzureCosmosStore._instance = None


class TestCommitStorage:
    """Test suite for commit storage operations"""

    @pytest.mark.asyncio
    async def test_store_commit_success(self, env_vars, mock_cosmos_client, sample_commit):
        """Test successful commit storage"""
        from tools.azure_cosmos_store import AzureCosmosStore

        # Mock upsert result
        mock_result = {
            'id': sample_commit['commitHash'],
            '_rid': 'test-rid',
            '_etag': 'test-etag'
        }
        mock_cosmos_client['container'].upsert_item.return_value = mock_result

        with patch('tools.azure_cosmos_store.CosmosClient', return_value=mock_cosmos_client['client']):
            AzureCosmosStore._instance = None

            store = await AzureCosmosStore.get_instance()
            result = await store.store_commit(sample_commit)

            assert result['id'] == sample_commit['commitHash']
            assert result['_rid'] == 'test-rid'
            assert result['_etag'] == 'test-etag'

            # Verify upsert was called
            mock_cosmos_client['container'].upsert_item.assert_called_once()

            await store.close()
            AzureCosmosStore._instance = None

    @pytest.mark.asyncio
    async def test_store_commit_missing_required_fields(self, env_vars, mock_cosmos_client):
        """Test storage fails with missing required fields"""
        from tools.azure_cosmos_store import AzureCosmosStore

        with patch('tools.azure_cosmos_store.CosmosClient', return_value=mock_cosmos_client['client']):
            AzureCosmosStore._instance = None

            store = await AzureCosmosStore.get_instance()

            # Missing commitHash
            incomplete_commit = {
                "message": "test commit",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

            with pytest.raises(ValueError, match="Missing required fields"):
                await store.store_commit(incomplete_commit)

            await store.close()
            AzureCosmosStore._instance = None

    @pytest.mark.asyncio
    async def test_store_commit_partition_key_extraction(self, env_vars, mock_cosmos_client, sample_commit):
        """Test partition key (commitDate) is correctly extracted from timestamp"""
        from tools.azure_cosmos_store import AzureCosmosStore

        mock_cosmos_client['container'].upsert_item.return_value = {'id': 'test'}

        with patch('tools.azure_cosmos_store.CosmosClient', return_value=mock_cosmos_client['client']):
            AzureCosmosStore._instance = None

            store = await AzureCosmosStore.get_instance()

            # Use a specific timestamp
            sample_commit['timestamp'] = '2025-01-15T10:30:00Z'
            await store.store_commit(sample_commit)

            # Verify document structure
            call_args = mock_cosmos_client['container'].upsert_item.call_args
            document = call_args.kwargs['body']

            assert document['commitDate'] == '2025-01-15'
            assert document['tenantId'] == 'tenant-test-001'

            await store.close()
            AzureCosmosStore._instance = None

    @pytest.mark.asyncio
    async def test_store_commit_invalid_timestamp(self, env_vars, mock_cosmos_client, sample_commit):
        """Test storage fails with invalid timestamp format"""
        from tools.azure_cosmos_store import AzureCosmosStore

        with patch('tools.azure_cosmos_store.CosmosClient', return_value=mock_cosmos_client['client']):
            AzureCosmosStore._instance = None

            store = await AzureCosmosStore.get_instance()

            sample_commit['timestamp'] = 'invalid-timestamp'

            with pytest.raises(ValueError, match="Invalid timestamp format"):
                await store.store_commit(sample_commit)

            await store.close()
            AzureCosmosStore._instance = None


class TestQueryOperations:
    """Test suite for query operations"""

    @pytest.mark.asyncio
    async def test_query_commits_by_tenant(self, env_vars, mock_cosmos_client):
        """Test querying commits by tenant ID"""
        from tools.azure_cosmos_store import AzureCosmosStore

        # Mock query results
        mock_items = [
            {'commitHash': 'abc123', 'message': 'commit 1', 'riskScore': 0.5},
            {'commitHash': 'def456', 'message': 'commit 2', 'riskScore': 0.3}
        ]

        async def async_generator():
            for item in mock_items:
                yield item

        mock_cosmos_client['container'].query_items.return_value = async_generator()

        with patch('tools.azure_cosmos_store.CosmosClient', return_value=mock_cosmos_client['client']):
            AzureCosmosStore._instance = None

            store = await AzureCosmosStore.get_instance()
            results = await store.query_commits_by_tenant(tenant_id='tenant-test-001')

            assert len(results) == 2
            assert results[0]['commitHash'] == 'abc123'
            assert results[1]['commitHash'] == 'def456'

            await store.close()
            AzureCosmosStore._instance = None

    @pytest.mark.asyncio
    async def test_query_high_risk_commits(self, env_vars, mock_cosmos_client):
        """Test querying high-risk commits"""
        from tools.azure_cosmos_store import AzureCosmosStore

        # Mock high-risk commits
        mock_items = [
            {'commitHash': 'xyz789', 'riskScore': 0.95, 'message': 'critical change'},
            {'commitHash': 'uvw321', 'riskScore': 0.85, 'message': 'high risk change'}
        ]

        async def async_generator():
            for item in mock_items:
                yield item

        mock_cosmos_client['container'].query_items.return_value = async_generator()

        with patch('tools.azure_cosmos_store.CosmosClient', return_value=mock_cosmos_client['client']):
            AzureCosmosStore._instance = None

            store = await AzureCosmosStore.get_instance()
            results = await store.query_high_risk_commits(risk_threshold=0.7, days=7)

            assert len(results) == 2
            assert results[0]['riskScore'] == 0.95
            assert results[1]['riskScore'] == 0.85

            await store.close()
            AzureCosmosStore._instance = None

    @pytest.mark.asyncio
    async def test_query_with_date_range(self, env_vars, mock_cosmos_client):
        """Test querying with custom date range"""
        from tools.azure_cosmos_store import AzureCosmosStore

        async def async_generator():
            return
            yield  # Make it a generator

        mock_cosmos_client['container'].query_items.return_value = async_generator()

        with patch('tools.azure_cosmos_store.CosmosClient', return_value=mock_cosmos_client['client']):
            AzureCosmosStore._instance = None

            store = await AzureCosmosStore.get_instance()

            start_date = '2024-01-01'
            end_date = '2024-12-31'

            await store.query_commits_by_tenant(
                start_date=start_date,
                end_date=end_date
            )

            # Verify query parameters
            call_args = mock_cosmos_client['container'].query_items.call_args
            parameters = call_args.kwargs['parameters']

            # Find start_date and end_date parameters
            param_dict = {p['name']: p['value'] for p in parameters}
            assert param_dict['@startDate'] == start_date
            assert param_dict['@endDate'] == end_date

            await store.close()
            AzureCosmosStore._instance = None


class TestPerformanceMonitoring:
    """Test suite for performance monitoring"""

    @pytest.mark.asyncio
    async def test_slow_query_detection(self, env_vars, mock_cosmos_client, sample_commit, caplog):
        """Test slow query detection (> 100ms) is logged"""
        from tools.azure_cosmos_store import AzureCosmosStore
        import logging

        # Mock slow upsert operation
        async def slow_upsert(*args, **kwargs):
            await asyncio.sleep(0.15)  # 150ms delay
            return {'id': 'test', '_etag': 'test-etag'}

        mock_cosmos_client['container'].upsert_item.side_effect = slow_upsert

        with patch('tools.azure_cosmos_store.CosmosClient', return_value=mock_cosmos_client['client']):
            with caplog.at_level(logging.WARNING):
                AzureCosmosStore._instance = None

                store = await AzureCosmosStore.get_instance()
                await store.store_commit(sample_commit)

                # Check if slow operation was logged
                assert any('Slow upsert operation' in record.message for record in caplog.records)

                await store.close()
                AzureCosmosStore._instance = None


class TestContextManager:
    """Test suite for async context manager"""

    @pytest.mark.asyncio
    async def test_context_manager_usage(self, env_vars, mock_cosmos_client):
        """Test using AzureCosmosStore as async context manager"""
        from tools.azure_cosmos_store import AzureCosmosStore

        with patch('tools.azure_cosmos_store.CosmosClient', return_value=mock_cosmos_client['client']):
            AzureCosmosStore._instance = None

            async with AzureCosmosStore() as store:
                assert store._initialized is True

            # After context exit, connection should be closed
            assert store.client is not None  # Client still exists but connection closed

            AzureCosmosStore._instance = None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=tools.azure_cosmos_store", "--cov-report=term-missing"])
