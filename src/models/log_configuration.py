"""로그 설정 관련 데이터 모델"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List
import re

# LogType은 log_schema.py에서 import
from .log_schema import LogType


class LogStatus(Enum):
    """로그 설정 상태"""
    PENDING = "pending"
    CONFIGURING = "configuring"
    ACTIVE = "active"
    ERROR = "error"
    DISABLED = "disabled"


class VerificationStatus(Enum):
    """로그 검증 상태"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    VERIFIED = "verified"
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass
class LogStatusInfo:
    """로그 상태 정보"""
    is_enabled: bool
    last_log_time: Optional[datetime] = None
    error_message: Optional[str] = None
    verification_status: VerificationStatus = VerificationStatus.NOT_STARTED
    verification_attempts: int = 0
    last_verification_time: Optional[datetime] = None
    
    @property
    def is_healthy(self) -> bool:
        """로그 상태가 정상인지 확인"""
        return (self.is_enabled and 
                self.verification_status == VerificationStatus.VERIFIED and
                self.error_message is None)


@dataclass
class LogConfiguration:
    """로그 설정 정보"""
    id: str
    source_bucket: str
    destination_bucket: str
    prefix: str
    log_type: LogType
    status: LogStatus
    created_at: datetime
    updated_at: datetime
    status_info: LogStatusInfo = field(default_factory=lambda: LogStatusInfo(is_enabled=False))
    configuration_details: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self) -> None:
        """데이터 검증"""
        self._validate_bucket_names()
        self._validate_prefix()
    
    def _validate_bucket_names(self) -> None:
        """버킷 이름 검증"""
        bucket_pattern = r'^[a-z0-9][a-z0-9\-]*[a-z0-9]$'
        
        if not self.source_bucket:
            raise ValueError("source_bucket은 필수입니다")
        
        if not self.destination_bucket:
            raise ValueError("destination_bucket은 필수입니다")
        
        # 버킷 이름 길이 검증 (3-63자)
        if not (3 <= len(self.source_bucket) <= 63):
            raise ValueError("source_bucket 이름은 3-63자 사이여야 합니다")
        
        if not (3 <= len(self.destination_bucket) <= 63):
            raise ValueError("destination_bucket 이름은 3-63자 사이여야 합니다")
        
        # 버킷 이름 형식 검증
        if not re.match(bucket_pattern, self.source_bucket):
            raise ValueError("source_bucket 이름 형식이 올바르지 않습니다")
        
        if not re.match(bucket_pattern, self.destination_bucket):
            raise ValueError("destination_bucket 이름 형식이 올바르지 않습니다")
        
        # 같은 버킷 사용 방지
        if self.source_bucket == self.destination_bucket:
            raise ValueError("source_bucket과 destination_bucket은 달라야 합니다")
    
    def _validate_prefix(self) -> None:
        """접두사 검증"""
        if self.prefix:
            # 접두사는 슬래시로 끝나야 함
            if not self.prefix.endswith('/'):
                self.prefix += '/'
            
            # 유효하지 않은 문자 검사
            invalid_chars = ['\\', '^', '`', '>', '<', '~', '#', '|', '&', '$']
            if any(char in self.prefix for char in invalid_chars):
                raise ValueError(f"prefix에 유효하지 않은 문자가 포함되어 있습니다: {invalid_chars}")
    
    def update_status(self, new_status: LogStatus, error_message: Optional[str] = None) -> None:
        """상태 업데이트"""
        self.status = new_status
        self.updated_at = datetime.now()
        
        if error_message:
            self.status_info.error_message = error_message
        elif new_status == LogStatus.ACTIVE:
            self.status_info.error_message = None
            self.status_info.is_enabled = True
    
    def update_verification_status(self, verification_status: VerificationStatus, 
                                 error_message: Optional[str] = None) -> None:
        """검증 상태 업데이트"""
        self.status_info.verification_status = verification_status
        self.status_info.last_verification_time = datetime.now()
        self.status_info.verification_attempts += 1
        
        if error_message:
            self.status_info.error_message = error_message
        elif verification_status == VerificationStatus.VERIFIED:
            self.status_info.error_message = None
            self.status_info.last_log_time = datetime.now()
    
    @property
    def full_destination_path(self) -> str:
        """전체 대상 경로 반환"""
        return f"s3://{self.destination_bucket}/{self.prefix}"
    
    @property
    def is_configuration_valid(self) -> bool:
        """설정이 유효한지 확인"""
        try:
            self._validate_bucket_names()
            self._validate_prefix()
            return True
        except ValueError:
            return False
    
    @property
    def days_since_last_log(self) -> Optional[int]:
        """마지막 로그 이후 경과 일수"""
        if self.status_info.last_log_time:
            delta = datetime.now() - self.status_info.last_log_time
            return delta.days
        return None


class LogConfigurationValidator:
    """로그 설정 검증기"""
    
    @staticmethod
    def validate_bucket_name(bucket_name: str) -> List[str]:
        """버킷 이름 검증 및 오류 목록 반환"""
        errors = []
        
        if not bucket_name:
            errors.append("버킷 이름이 필요합니다")
            return errors
        
        # 길이 검증
        if len(bucket_name) < 3:
            errors.append("버킷 이름은 최소 3자 이상이어야 합니다")
        elif len(bucket_name) > 63:
            errors.append("버킷 이름은 최대 63자 이하여야 합니다")
        
        # 형식 검증
        if not re.match(r'^[a-z0-9][a-z0-9\-]*[a-z0-9]$', bucket_name):
            errors.append("버킷 이름은 소문자, 숫자, 하이픈만 사용 가능하며 하이픈으로 시작하거나 끝날 수 없습니다")
        
        # 연속 하이픈 검사
        if '--' in bucket_name:
            errors.append("버킷 이름에 연속된 하이픈을 사용할 수 없습니다")
        
        # IP 주소 형식 검사
        if re.match(r'^\d+\.\d+\.\d+\.\d+$', bucket_name):
            errors.append("버킷 이름은 IP 주소 형식을 사용할 수 없습니다")
        
        # 예약어 검사
        reserved_prefixes = ['xn--', 'sthree-', 'sthree-configurator']
        if any(bucket_name.startswith(prefix) for prefix in reserved_prefixes):
            errors.append("버킷 이름에 예약된 접두사를 사용할 수 없습니다")
        
        return errors
    
    @staticmethod
    def validate_prefix(prefix: str) -> List[str]:
        """접두사 검증 및 오류 목록 반환"""
        errors = []
        
        if not prefix:
            return errors  # 접두사는 선택사항
        
        # 길이 검증
        if len(prefix) > 1024:
            errors.append("접두사는 최대 1024자까지 가능합니다")
        
        # 유효하지 않은 문자 검사
        invalid_chars = ['\\', '^', '`', '>', '<', '~', '#', '|', '&', '$']
        found_invalid = [char for char in invalid_chars if char in prefix]
        if found_invalid:
            errors.append(f"접두사에 유효하지 않은 문자가 포함되어 있습니다: {', '.join(found_invalid)}")
        
        # 시작 문자 검증
        if prefix.startswith('/'):
            errors.append("접두사는 슬래시(/)로 시작할 수 없습니다")
        
        return errors
    
    @staticmethod
    def validate_log_configuration(config: LogConfiguration) -> List[str]:
        """전체 로그 설정 검증"""
        errors = []
        
        # 버킷 이름 검증
        source_errors = LogConfigurationValidator.validate_bucket_name(config.source_bucket)
        if source_errors:
            errors.extend([f"Source bucket: {error}" for error in source_errors])
        
        destination_errors = LogConfigurationValidator.validate_bucket_name(config.destination_bucket)
        if destination_errors:
            errors.extend([f"Destination bucket: {error}" for error in destination_errors])
        
        # 접두사 검증
        prefix_errors = LogConfigurationValidator.validate_prefix(config.prefix)
        if prefix_errors:
            errors.extend([f"Prefix: {error}" for error in prefix_errors])
        
        # 같은 버킷 사용 검사
        if config.source_bucket == config.destination_bucket:
            errors.append("Source bucket과 destination bucket은 달라야 합니다")
        
        return errors


class LogConfigurationManager:
    """로그 설정 상태 추적 관리자"""
    
    def __init__(self):
        self._configurations: Dict[str, LogConfiguration] = {}
    
    def add_configuration(self, config: LogConfiguration) -> None:
        """로그 설정 추가"""
        validation_errors = LogConfigurationValidator.validate_log_configuration(config)
        if validation_errors:
            raise ValueError(f"설정 검증 실패: {', '.join(validation_errors)}")
        
        self._configurations[config.id] = config
    
    def get_configuration(self, config_id: str) -> Optional[LogConfiguration]:
        """로그 설정 조회"""
        return self._configurations.get(config_id)
    
    def update_configuration_status(self, config_id: str, status: LogStatus, 
                                  error_message: Optional[str] = None) -> None:
        """로그 설정 상태 업데이트"""
        if config_id in self._configurations:
            self._configurations[config_id].update_status(status, error_message)
    
    def get_configurations_by_status(self, status: LogStatus) -> List[LogConfiguration]:
        """상태별 로그 설정 조회"""
        return [config for config in self._configurations.values() 
                if config.status == status]
    
    def get_configurations_by_bucket(self, bucket_name: str) -> List[LogConfiguration]:
        """버킷별 로그 설정 조회"""
        return [config for config in self._configurations.values() 
                if config.source_bucket == bucket_name or config.destination_bucket == bucket_name]
    
    def remove_configuration(self, config_id: str) -> bool:
        """로그 설정 제거"""
        if config_id in self._configurations:
            del self._configurations[config_id]
            return True
        return False
    
    def get_all_configurations(self) -> List[LogConfiguration]:
        """모든 로그 설정 조회"""
        return list(self._configurations.values())
    
    def get_health_summary(self) -> Dict[str, int]:
        """로그 설정 상태 요약"""
        summary = {status.value: 0 for status in LogStatus}
        
        for config in self._configurations.values():
            summary[config.status.value] += 1
        
        return summary