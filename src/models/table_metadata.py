"""테이블 메타데이터 관련 데이터 모델"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Dict, Any, Optional


class PartitionType(Enum):
    """파티션 타입"""
    DATE = "date"
    HOUR = "hour"
    CUSTOM = "custom"


class TableStatus(Enum):
    """테이블 상태"""
    CREATING = "creating"
    ACTIVE = "active"
    UPDATING = "updating"
    ERROR = "error"
    DELETED = "deleted"


@dataclass
class Parameter:
    """쿼리 템플릿 파라미터"""
    name: str
    type: str
    description: str
    default_value: Optional[Any] = None
    required: bool = True


@dataclass
class TableMetadata:
    """Athena 테이블 메타데이터"""
    database_name: str
    table_name: str
    s3_location: str
    partition_keys: List[str]
    schema_version: str
    created_at: datetime
    last_updated: datetime
    status: TableStatus = TableStatus.CREATING
    partition_type: PartitionType = PartitionType.DATE
    
    def __post_init__(self) -> None:
        """데이터 검증"""
        if not self.database_name:
            raise ValueError("database_name은 필수입니다")
        if not self.table_name:
            raise ValueError("table_name은 필수입니다")
        if not self.s3_location.startswith('s3://'):
            raise ValueError("s3_location은 s3:// 형식이어야 합니다")
    
    @property
    def full_table_name(self) -> str:
        """전체 테이블 이름 반환"""
        return f"{self.database_name}.{self.table_name}"


@dataclass
class QueryTemplate:
    """쿼리 템플릿 정보"""
    id: str
    name: str
    description: str
    pattern: str
    sql_template: str
    parameters: List[Parameter] = field(default_factory=list)
    category: str = "general"
    usage_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self) -> None:
        """데이터 검증"""
        if not self.name:
            raise ValueError("name은 필수입니다")
        if not self.sql_template:
            raise ValueError("sql_template은 필수입니다")
    
    def increment_usage(self) -> None:
        """사용 횟수 증가"""
        self.usage_count += 1


@dataclass
class Partition:
    """테이블 파티션 정보"""
    table_name: str
    partition_values: Dict[str, str]
    location: str
    created_at: datetime
    size_bytes: int = 0
    record_count: int = 0
    
    @property
    def partition_spec(self) -> str:
        """파티션 스펙 문자열 생성"""
        specs = [f"{key}='{value}'" for key, value in self.partition_values.items()]
        return ", ".join(specs)