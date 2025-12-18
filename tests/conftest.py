"""pytest 설정 및 공통 픽스처"""

import pytest
from datetime import datetime
from unittest.mock import Mock

from src.models import (
    LogConfiguration,
    LogType,
    LogStatus,
    TableMetadata,
    TableStatus,
    PartitionType
)


@pytest.fixture
def sample_log_config():
    """테스트용 로그 설정 샘플"""
    return LogConfiguration(
        id="test-log-config-1",
        source_bucket="test-source-bucket",
        destination_bucket="test-destination-bucket", 
        prefix="access-logs/",
        log_type=LogType.S3,
        status=LogStatus.ACTIVE,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )


@pytest.fixture
def sample_table_metadata():
    """테스트용 테이블 메타데이터 샘플"""
    return TableMetadata(
        database_name="test_database",
        table_name="test_s3_logs",
        s3_location="s3://test-bucket/logs/",
        partition_keys=["year", "month", "day"],
        schema_version="1.0",
        created_at=datetime.now(),
        last_updated=datetime.now(),
        status=TableStatus.ACTIVE,
        partition_type=PartitionType.DATE
    )


@pytest.fixture
def mock_boto3_client():
    """Mock boto3 클라이언트"""
    return Mock()


@pytest.fixture
def mock_s3_client(mock_boto3_client):
    """Mock S3 클라이언트"""
    mock_boto3_client.put_bucket_logging.return_value = {}
    mock_boto3_client.get_bucket_logging.return_value = {
        'LoggingEnabled': {
            'TargetBucket': 'test-destination-bucket',
            'TargetPrefix': 'access-logs/'
        }
    }
    return mock_boto3_client


@pytest.fixture
def mock_athena_client(mock_boto3_client):
    """Mock Athena 클라이언트"""
    mock_boto3_client.start_query_execution.return_value = {
        'QueryExecutionId': 'test-query-id-123'
    }
    mock_boto3_client.get_query_execution.return_value = {
        'QueryExecution': {
            'QueryExecutionId': 'test-query-id-123',
            'Status': {'State': 'SUCCEEDED'},
            'Statistics': {
                'DataScannedInBytes': 1024000,
                'EngineExecutionTimeInMillis': 5000
            }
        }
    }
    return mock_boto3_client