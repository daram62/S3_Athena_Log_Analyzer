"""AWS 서비스 연동 모듈"""

from .aws_clients import (
    AWSClientManager,
    S3ClientWrapper,
    AthenaClientWrapper,
    BedrockClientWrapper,
    GlueClientWrapper,
    AWSConnectionError,
    AWSAuthenticationError,
    AWSPermissionError,
    aws_client_manager,
    s3_client,
    athena_client,
    bedrock_client,
    glue_client,
    retry_with_backoff
)

from .ddl_generator import DDLGenerator
from .log_detection_engine import (
    log_detection_service,
    LogDetectionEngine,
    DetectionRequest,
    DetectionResult
)
from .log_classifier import (
    LogFormatClassifier,
    LogSampleExtractor,
    LogSample,
    ClassificationResult
)

__all__ = [
    # AWS 클라이언트
    'AWSClientManager',
    'S3ClientWrapper',
    'AthenaClientWrapper', 
    'BedrockClientWrapper',
    'GlueClientWrapper',
    'aws_client_manager',
    's3_client',
    'athena_client',
    'bedrock_client',
    'glue_client',
    
    # 예외 클래스
    'AWSConnectionError',
    'AWSAuthenticationError',
    'AWSPermissionError',
    
    # DDL 생성
    'DDLGenerator',
    
    # 로그 감지
    'log_detection_service',
    'LogDetectionEngine',
    'DetectionRequest',
    'DetectionResult',
    
    # 로그 분류
    'LogFormatClassifier',
    'LogSampleExtractor',
    'LogSample',
    'ClassificationResult',
    
    # 유틸리티
    'retry_with_backoff',
    
    # Bedrock Service
    'BedrockService'
]

from .bedrock_service import BedrockService
