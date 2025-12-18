"""데이터 모델 테스트"""

import pytest
from datetime import datetime

from src.models import (
    LogConfiguration,
    LogType,
    LogStatus,
    VerificationStatus,
    LogStatusInfo,
    TableMetadata,
    TableStatus,
    PartitionType,
    AnalysisResult,
    Anomaly,
    AnomalyType,
    Severity,
    TimeRange,
    QueryExecution
)


class TestLogConfiguration:
    """LogConfiguration 모델 테스트"""
    
    def test_valid_log_configuration(self):
        """유효한 로그 설정 생성 테스트"""
        config = LogConfiguration(
            id="test-1",
            source_bucket="source-bucket",
            destination_bucket="dest-bucket",
            prefix="logs/",
            log_type=LogType.S3,
            status=LogStatus.ACTIVE,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        assert config.id == "test-1"
        assert config.source_bucket == "source-bucket"
        assert config.log_type == LogType.S3
    
    def test_empty_source_bucket_raises_error(self):
        """빈 소스 버킷 시 오류 발생 테스트"""
        with pytest.raises(ValueError, match="source_bucket은 필수입니다"):
            LogConfiguration(
                id="test-1",
                source_bucket="",
                destination_bucket="dest-bucket",
                prefix="logs/",
                log_type=LogType.S3,
                status=LogStatus.ACTIVE,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
    
    def test_empty_destination_bucket_raises_error(self):
        """빈 대상 버킷 시 오류 발생 테스트"""
        with pytest.raises(ValueError, match="destination_bucket은 필수입니다"):
            LogConfiguration(
                id="test-1",
                source_bucket="source-bucket",
                destination_bucket="",
                prefix="logs/",
                log_type=LogType.S3,
                status=LogStatus.ACTIVE,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )


class TestLogStatusInfo:
    """LogStatusInfo 모델 테스트"""
    
    def test_healthy_status(self):
        """정상 상태 확인 테스트"""
        status = LogStatusInfo(
            is_enabled=True,
            last_log_time=datetime.now(),
            error_message=None,
            verification_status=VerificationStatus.VERIFIED
        )
        
        assert status.is_healthy() is True
    
    def test_unhealthy_status_disabled(self):
        """비활성화 상태 테스트"""
        status = LogStatusInfo(
            is_enabled=False,
            last_log_time=None,
            error_message=None,
            verification_status=VerificationStatus.NOT_VERIFIED
        )
        
        assert status.is_healthy() is False


class TestTableMetadata:
    """TableMetadata 모델 테스트"""
    
    def test_valid_table_metadata(self):
        """유효한 테이블 메타데이터 생성 테스트"""
        metadata = TableMetadata(
            database_name="test_db",
            table_name="test_table",
            s3_location="s3://test-bucket/data/",
            partition_keys=["year", "month"],
            schema_version="1.0",
            created_at=datetime.now(),
            last_updated=datetime.now()
        )
        
        assert metadata.full_table_name == "test_db.test_table"
        assert metadata.status == TableStatus.CREATING
    
    def test_invalid_s3_location_raises_error(self):
        """잘못된 S3 위치 시 오류 발생 테스트"""
        with pytest.raises(ValueError, match="s3_location은 s3:// 형식이어야 합니다"):
            TableMetadata(
                database_name="test_db",
                table_name="test_table",
                s3_location="invalid-location",
                partition_keys=["year"],
                schema_version="1.0",
                created_at=datetime.now(),
                last_updated=datetime.now()
            )


class TestTimeRange:
    """TimeRange 모델 테스트"""
    
    def test_valid_time_range(self):
        """유효한 시간 범위 테스트"""
        start = datetime(2024, 1, 1, 10, 0, 0)
        end = datetime(2024, 1, 1, 11, 30, 0)
        
        time_range = TimeRange(start_time=start, end_time=end)
        
        assert time_range.duration_minutes == 90
    
    def test_invalid_time_range_raises_error(self):
        """잘못된 시간 범위 시 오류 발생 테스트"""
        start = datetime(2024, 1, 1, 11, 0, 0)
        end = datetime(2024, 1, 1, 10, 0, 0)  # 시작이 끝보다 늦음
        
        with pytest.raises(ValueError, match="start_time은 end_time보다 이전이어야 합니다"):
            TimeRange(start_time=start, end_time=end)


class TestAnomaly:
    """Anomaly 모델 테스트"""
    
    def test_valid_anomaly(self):
        """유효한 이상 탐지 결과 테스트"""
        time_range = TimeRange(
            start_time=datetime(2024, 1, 1, 10, 0, 0),
            end_time=datetime(2024, 1, 1, 11, 0, 0)
        )
        
        anomaly = Anomaly(
            type=AnomalyType.TRAFFIC_SPIKE,
            severity=Severity.HIGH,
            description="트래픽 급증 감지",
            confidence_score=0.95,
            affected_timerange=time_range
        )
        
        assert anomaly.type == AnomalyType.TRAFFIC_SPIKE
        assert anomaly.confidence_score == 0.95
    
    def test_invalid_confidence_score_raises_error(self):
        """잘못된 신뢰도 점수 시 오류 발생 테스트"""
        time_range = TimeRange(
            start_time=datetime(2024, 1, 1, 10, 0, 0),
            end_time=datetime(2024, 1, 1, 11, 0, 0)
        )
        
        with pytest.raises(ValueError, match="confidence_score는 0과 1 사이여야 합니다"):
            Anomaly(
                type=AnomalyType.TRAFFIC_SPIKE,
                severity=Severity.HIGH,
                description="테스트",
                confidence_score=1.5,  # 잘못된 값
                affected_timerange=time_range
            )


class TestAnalysisResult:
    """AnalysisResult 모델 테스트"""
    
    def test_analysis_result_with_critical_anomalies(self):
        """심각한 이상이 포함된 분석 결과 테스트"""
        query_execution = QueryExecution(
            query_id="test-query-1",
            sql_query="SELECT * FROM test_table",
            execution_time_ms=1000.0,
            data_scanned_mb=10.5,
            result_count=100,
            status="SUCCEEDED",
            started_at=datetime.now()
        )
        
        time_range = TimeRange(
            start_time=datetime(2024, 1, 1, 10, 0, 0),
            end_time=datetime(2024, 1, 1, 11, 0, 0)
        )
        
        critical_anomaly = Anomaly(
            type=AnomalyType.SECURITY_THREAT,
            severity=Severity.CRITICAL,
            description="보안 위협 감지",
            confidence_score=0.98,
            affected_timerange=time_range
        )
        
        result = AnalysisResult(
            query_execution=query_execution,
            anomalies=[critical_anomaly]
        )
        
        assert result.has_critical_anomalies is True
        assert result.anomaly_count_by_severity["critical"] == 1