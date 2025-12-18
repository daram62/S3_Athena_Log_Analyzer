"""분석 결과 관련 데이터 모델"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any


class AnomalyType(Enum):
    """이상 탐지 타입"""
    TRAFFIC_SPIKE = "traffic_spike"
    ERROR_RATE_INCREASE = "error_rate_increase"
    UNUSUAL_ACCESS_PATTERN = "unusual_access_pattern"
    SECURITY_THREAT = "security_threat"
    PERFORMANCE_DEGRADATION = "performance_degradation"


class Severity(Enum):
    """심각도 레벨"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class InsightType(Enum):
    """인사이트 타입"""
    TREND = "trend"
    RECOMMENDATION = "recommendation"
    PREDICTION = "prediction"
    SUMMARY = "summary"


@dataclass
class TimeRange:
    """시간 범위"""
    start_time: datetime
    end_time: datetime
    
    def __post_init__(self) -> None:
        """데이터 검증"""
        if self.start_time >= self.end_time:
            raise ValueError("start_time은 end_time보다 이전이어야 합니다")
    
    @property
    def duration_minutes(self) -> int:
        """기간을 분 단위로 반환"""
        return int((self.end_time - self.start_time).total_seconds() / 60)


@dataclass
class Anomaly:
    """이상 탐지 결과"""
    type: AnomalyType
    severity: Severity
    description: str
    confidence_score: float
    affected_timerange: TimeRange
    root_cause_analysis: Optional[str] = None
    affected_resources: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self) -> None:
        """데이터 검증"""
        if not 0 <= self.confidence_score <= 1:
            raise ValueError("confidence_score는 0과 1 사이여야 합니다")
        if not self.description:
            raise ValueError("description은 필수입니다")


@dataclass
class Insight:
    """분석 인사이트"""
    type: InsightType
    title: str
    description: str
    confidence_score: float
    data: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    
    def __post_init__(self) -> None:
        """데이터 검증"""
        if not 0 <= self.confidence_score <= 1:
            raise ValueError("confidence_score는 0과 1 사이여야 합니다")
        if not self.title:
            raise ValueError("title은 필수입니다")


@dataclass
class QueryExecution:
    """쿼리 실행 정보"""
    query_id: str
    sql_query: str
    execution_time_ms: float
    data_scanned_mb: float
    result_count: int
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    
    @property
    def is_successful(self) -> bool:
        """쿼리 실행 성공 여부"""
        return self.status == "SUCCEEDED" and self.error_message is None


@dataclass
class AnalysisResult:
    """전체 분석 결과"""
    query_execution: QueryExecution
    anomalies: List[Anomaly] = field(default_factory=list)
    insights: List[Insight] = field(default_factory=list)
    summary_stats: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    
    @property
    def has_critical_anomalies(self) -> bool:
        """심각한 이상이 있는지 확인"""
        return any(anomaly.severity == Severity.CRITICAL for anomaly in self.anomalies)
    
    @property
    def anomaly_count_by_severity(self) -> Dict[str, int]:
        """심각도별 이상 개수"""
        counts = {severity.value: 0 for severity in Severity}
        for anomaly in self.anomalies:
            counts[anomaly.severity.value] += 1
        return counts  