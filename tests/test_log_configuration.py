"""로그 설정 모델 테스트"""

import pytest
from datetime import datetime
from src.models.log_configuration import (
    LogConfiguration,
    LogStatusInfo,
    LogType,
    LogStatus,
    VerificationStatus,
    LogConfigurationValidator,
    LogConfigurationManager
)


class TestLogStatusInfo:
    """LogStatusInfo 테스트"""
    
    def test_default_values(self):
        """기본값 테스트"""
        status_info = LogStatusInfo(is_enabled=True)
        
        assert status_info.is_enabled is True
        assert status_info.last_log_time is None
        assert status_info.error_message is None
        assert status_info.verification_status == VerificationStatus.NOT_STARTED
        assert status_info.verification_attempts == 0
        assert status_info.last_verification_time is None
    
    def test_is_healthy_true(self):
        """정상 상태 확인"""
        status_info = LogStatusInfo(
            is_enabled=True,
            verification_status=VerificationStatus.VERIFIED,
            error_message=None
        )
        
        assert status_info.is_healthy is True
    
    def test_is_healthy_false_cases(self):
        """비정상 상태 확인"""
        # 비활성화된 경우
        status_info = LogStatusInfo(
            is_enabled=False,
            verification_status=VerificationStatus.VERIFIED
        )
        assert status_info.is_healthy is False
        
        # 검증 실패한 경우
        status_info = LogStatusInfo(
            is_enabled=True,
            verification_status=VerificationStatus.FAILED
        )
        assert status_info.is_healthy is False
        
        # 오류 메시지가 있는 경우
        status_info = LogStatusInfo(
            is_enabled=True,
            verification_status=VerificationStatus.VERIFIED,
            error_message="Some error"
        )
        assert status_info.is_healthy is False


class TestLogConfiguration:
    """LogConfiguration 테스트"""
    
    def test_valid_configuration(self):
        """유효한 설정 테스트"""
        config = LogConfiguration(
            id="test-config-1",
            source_bucket="my-source-bucket",
            destination_bucket="my-log-bucket",
            prefix="logs/",
            log_type=LogType.S3_ACCESS,
            status=LogStatus.PENDING,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        assert config.source_bucket == "my-source-bucket"
        assert config.destination_bucket == "my-log-bucket"
        assert config.prefix == "logs/"
        assert config.is_configuration_valid is True
    
    def test_prefix_auto_correction(self):
        """접두사 자동 수정 테스트"""
        config = LogConfiguration(
            id="test-config-2",
            source_bucket="my-source-bucket",
            destination_bucket="my-log-bucket",
            prefix="logs",  # 슬래시 없음
            log_type=LogType.S3_ACCESS,
            status=LogStatus.PENDING,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        assert config.prefix == "logs/"  # 자동으로 슬래시 추가
    
    def test_invalid_bucket_names(self):
        """잘못된 버킷 이름 테스트"""
        # 빈 버킷 이름
        with pytest.raises(ValueError, match="source_bucket은 필수입니다"):
            LogConfiguration(
                id="test-config-3",
                source_bucket="",
                destination_bucket="my-log-bucket",
                prefix="logs/",
                log_type=LogType.S3_ACCESS,
                status=LogStatus.PENDING,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
        
        # 너무 짧은 버킷 이름
        with pytest.raises(ValueError, match="source_bucket 이름은 3-63자 사이여야 합니다"):
            LogConfiguration(
                id="test-config-4",
                source_bucket="ab",
                destination_bucket="my-log-bucket",
                prefix="logs/",
                log_type=LogType.S3_ACCESS,
                status=LogStatus.PENDING,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
        
        # 잘못된 형식의 버킷 이름
        with pytest.raises(ValueError, match="source_bucket 이름 형식이 올바르지 않습니다"):
            LogConfiguration(
                id="test-config-5",
                source_bucket="My-Bucket",  # 대문자 포함
                destination_bucket="my-log-bucket",
                prefix="logs/",
                log_type=LogType.S3_ACCESS,
                status=LogStatus.PENDING,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
    
    def test_same_bucket_validation(self):
        """같은 버킷 사용 검증"""
        with pytest.raises(ValueError, match="source_bucket과 destination_bucket은 달라야 합니다"):
            LogConfiguration(
                id="test-config-6",
                source_bucket="same-bucket",
                destination_bucket="same-bucket",
                prefix="logs/",
                log_type=LogType.S3_ACCESS,
                status=LogStatus.PENDING,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
    
    def test_invalid_prefix_characters(self):
        """잘못된 접두사 문자 테스트"""
        with pytest.raises(ValueError, match="prefix에 유효하지 않은 문자가 포함되어 있습니다"):
            LogConfiguration(
                id="test-config-7",
                source_bucket="my-source-bucket",
                destination_bucket="my-log-bucket",
                prefix="logs#invalid/",
                log_type=LogType.S3_ACCESS,
                status=LogStatus.PENDING,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
    
    def test_update_status(self):
        """상태 업데이트 테스트"""
        config = LogConfiguration(
            id="test-config-8",
            source_bucket="my-source-bucket",
            destination_bucket="my-log-bucket",
            prefix="logs/",
            log_type=LogType.S3_ACCESS,
            status=LogStatus.PENDING,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        original_updated_at = config.updated_at
        
        # 상태 업데이트
        config.update_status(LogStatus.ACTIVE)
        
        assert config.status == LogStatus.ACTIVE
        assert config.updated_at > original_updated_at
        assert config.status_info.is_enabled is True
        assert config.status_info.error_message is None
    
    def test_update_verification_status(self):
        """검증 상태 업데이트 테스트"""
        config = LogConfiguration(
            id="test-config-9",
            source_bucket="my-source-bucket",
            destination_bucket="my-log-bucket",
            prefix="logs/",
            log_type=LogType.S3_ACCESS,
            status=LogStatus.PENDING,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # 검증 상태 업데이트
        config.update_verification_status(VerificationStatus.VERIFIED)
        
        assert config.status_info.verification_status == VerificationStatus.VERIFIED
        assert config.status_info.verification_attempts == 1
        assert config.status_info.last_verification_time is not None
        assert config.status_info.error_message is None
        assert config.status_info.last_log_time is not None
    
    def test_full_destination_path(self):
        """전체 대상 경로 테스트"""
        config = LogConfiguration(
            id="test-config-10",
            source_bucket="my-source-bucket",
            destination_bucket="my-log-bucket",
            prefix="logs/access/",
            log_type=LogType.S3_ACCESS,
            status=LogStatus.PENDING,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        assert config.full_destination_path == "s3://my-log-bucket/logs/access/"


class TestLogConfigurationValidator:
    """LogConfigurationValidator 테스트"""
    
    def test_validate_bucket_name_valid(self):
        """유효한 버킷 이름 검증"""
        errors = LogConfigurationValidator.validate_bucket_name("my-valid-bucket-123")
        assert errors == []
    
    def test_validate_bucket_name_invalid_cases(self):
        """잘못된 버킷 이름 검증"""
        # 빈 이름
        errors = LogConfigurationValidator.validate_bucket_name("")
        assert "버킷 이름이 필요합니다" in errors
        
        # 너무 짧은 이름
        errors = LogConfigurationValidator.validate_bucket_name("ab")
        assert any("최소 3자" in error for error in errors)
        
        # 너무 긴 이름
        long_name = "a" * 64
        errors = LogConfigurationValidator.validate_bucket_name(long_name)
        assert any("최대 63자" in error for error in errors)
        
        # 잘못된 형식
        errors = LogConfigurationValidator.validate_bucket_name("My-Bucket")
        assert any("소문자, 숫자, 하이픈만" in error for error in errors)
        
        # 연속 하이픈
        errors = LogConfigurationValidator.validate_bucket_name("my--bucket")
        assert any("연속된 하이픈" in error for error in errors)
        
        # IP 주소 형식
        errors = LogConfigurationValidator.validate_bucket_name("192.168.1.1")
        assert any("IP 주소 형식" in error for error in errors)
    
    def test_validate_prefix_valid(self):
        """유효한 접두사 검증"""
        errors = LogConfigurationValidator.validate_prefix("logs/access/")
        assert errors == []
        
        # 빈 접두사도 유효
        errors = LogConfigurationValidator.validate_prefix("")
        assert errors == []
    
    def test_validate_prefix_invalid_cases(self):
        """잘못된 접두사 검증"""
        # 너무 긴 접두사
        long_prefix = "a" * 1025
        errors = LogConfigurationValidator.validate_prefix(long_prefix)
        assert any("최대 1024자" in error for error in errors)
        
        # 유효하지 않은 문자
        errors = LogConfigurationValidator.validate_prefix("logs#invalid/")
        assert any("유효하지 않은 문자" in error for error in errors)
        
        # 슬래시로 시작
        errors = LogConfigurationValidator.validate_prefix("/logs/")
        assert any("슬래시(/)로 시작할 수 없습니다" in error for error in errors)


class TestLogConfigurationManager:
    """LogConfigurationManager 테스트"""
    
    def test_add_and_get_configuration(self):
        """설정 추가 및 조회 테스트"""
        manager = LogConfigurationManager()
        
        config = LogConfiguration(
            id="test-config-1",
            source_bucket="my-source-bucket",
            destination_bucket="my-log-bucket",
            prefix="logs/",
            log_type=LogType.S3_ACCESS,
            status=LogStatus.PENDING,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        manager.add_configuration(config)
        retrieved_config = manager.get_configuration("test-config-1")
        
        assert retrieved_config is not None
        assert retrieved_config.id == "test-config-1"
        assert retrieved_config.source_bucket == "my-source-bucket"
    
    def test_add_invalid_configuration(self):
        """잘못된 설정 추가 테스트"""
        manager = LogConfigurationManager()
        
        # 잘못된 설정
        with pytest.raises(ValueError, match="source_bucket과 destination_bucket은 달라야 합니다"):
            config = LogConfiguration(
                id="test-config-2",
                source_bucket="same-bucket",
                destination_bucket="same-bucket",  # 같은 버킷
                prefix="logs/",
                log_type=LogType.S3_ACCESS,
                status=LogStatus.PENDING,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            manager.add_configuration(config)
    
    def test_update_configuration_status(self):
        """설정 상태 업데이트 테스트"""
        manager = LogConfigurationManager()
        
        config = LogConfiguration(
            id="test-config-3",
            source_bucket="my-source-bucket",
            destination_bucket="my-log-bucket",
            prefix="logs/",
            log_type=LogType.S3_ACCESS,
            status=LogStatus.PENDING,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        manager.add_configuration(config)
        manager.update_configuration_status("test-config-3", LogStatus.ACTIVE)
        
        updated_config = manager.get_configuration("test-config-3")
        assert updated_config.status == LogStatus.ACTIVE
    
    def test_get_configurations_by_status(self):
        """상태별 설정 조회 테스트"""
        manager = LogConfigurationManager()
        
        # 여러 설정 추가
        for i in range(3):
            config = LogConfiguration(
                id=f"test-config-{i}",
                source_bucket=f"source-bucket-{i}",
                destination_bucket=f"log-bucket-{i}",
                prefix="logs/",
                log_type=LogType.S3_ACCESS,
                status=LogStatus.PENDING if i < 2 else LogStatus.ACTIVE,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            manager.add_configuration(config)
        
        pending_configs = manager.get_configurations_by_status(LogStatus.PENDING)
        active_configs = manager.get_configurations_by_status(LogStatus.ACTIVE)
        
        assert len(pending_configs) == 2
        assert len(active_configs) == 1
    
    def test_get_health_summary(self):
        """상태 요약 테스트"""
        manager = LogConfigurationManager()
        
        # 다양한 상태의 설정 추가
        statuses = [LogStatus.PENDING, LogStatus.ACTIVE, LogStatus.ERROR, LogStatus.ACTIVE]
        
        for i, status in enumerate(statuses):
            config = LogConfiguration(
                id=f"test-config-{i}",
                source_bucket=f"source-bucket-{i}",
                destination_bucket=f"log-bucket-{i}",
                prefix="logs/",
                log_type=LogType.S3_ACCESS,
                status=status,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            manager.add_configuration(config)
        
        summary = manager.get_health_summary()
        
        assert summary[LogStatus.PENDING.value] == 1
        assert summary[LogStatus.ACTIVE.value] == 2
        assert summary[LogStatus.ERROR.value] == 1
        assert summary[LogStatus.CONFIGURING.value] == 0
        assert summary[LogStatus.DISABLED.value] == 0