"""쿼리 히스토리 데이터 모델"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class QueryStatus(str, Enum):
    """쿼리 실행 상태"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class QueryType(str, Enum):
    """쿼리 타입"""
    NATURAL_LANGUAGE = "natural_language"  # 자연어 쿼리
    TEMPLATE = "template"  # 템플릿 쿼리
    CUSTOM = "custom"  # 직접 작성한 SQL


class QueryHistoryEntry(BaseModel):
    """쿼리 히스토리 항목"""
    
    # 기본 정보
    id: str = Field(..., description="쿼리 ID (UUID)")
    query_type: QueryType = Field(..., description="쿼리 타입")
    
    # 자연어 쿼리 정보
    natural_language_question: Optional[str] = Field(None, description="자연어 질문")
    
    # SQL 정보
    sql_query: str = Field(..., description="실행된 SQL 쿼리")
    database_name: str = Field(..., description="데이터베이스 이름")
    table_name: str = Field(..., description="테이블 이름")
    log_type: Optional[str] = Field(None, description="로그 타입")
    
    # 실행 정보
    status: QueryStatus = Field(default=QueryStatus.PENDING, description="실행 상태")
    athena_query_execution_id: Optional[str] = Field(None, description="Athena 쿼리 실행 ID")
    
    # 결과 정보
    row_count: Optional[int] = Field(None, description="결과 행 수")
    data_scanned_bytes: Optional[int] = Field(None, description="스캔된 데이터 크기 (bytes)")
    execution_time_ms: Optional[int] = Field(None, description="실행 시간 (ms)")
    
    # AI 메타데이터 (자연어 쿼리인 경우)
    ai_confidence: Optional[float] = Field(None, description="AI 신뢰도 (0-1)")
    ai_explanation: Optional[str] = Field(None, description="쿼리 설명")
    ai_assumptions: Optional[List[str]] = Field(default=[], description="AI가 가정한 사항")
    ai_suggestions: Optional[List[str]] = Field(default=[], description="추가 분석 제안")
    
    # 에러 정보
    error_message: Optional[str] = Field(None, description="에러 메시지")
    
    # 타임스탬프
    created_at: datetime = Field(default_factory=datetime.utcnow, description="생성 시간")
    started_at: Optional[datetime] = Field(None, description="실행 시작 시간")
    completed_at: Optional[datetime] = Field(None, description="완료 시간")
    
    # 사용자 정보 (향후 확장)
    user_id: Optional[str] = Field(None, description="사용자 ID")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "query_type": "natural_language",
                "natural_language_question": "지난 7일간 가장 많이 접근된 파일은?",
                "sql_query": "SELECT key, COUNT(*) as count FROM logs.s3_access GROUP BY key ORDER BY count DESC LIMIT 10",
                "database_name": "logs",
                "table_name": "s3_access",
                "log_type": "s3_access",
                "status": "succeeded",
                "row_count": 10,
                "data_scanned_bytes": 1048576,
                "execution_time_ms": 1250,
                "ai_confidence": 0.95,
                "ai_explanation": "최근 7일간의 S3 접근 로그에서 파일별 접근 횟수를 집계합니다"
            }
        }


class QueryHistoryList(BaseModel):
    """쿼리 히스토리 목록"""
    total: int = Field(..., description="전체 쿼리 수")
    items: List[QueryHistoryEntry] = Field(..., description="쿼리 목록")
    page: int = Field(default=1, description="현재 페이지")
    page_size: int = Field(default=20, description="페이지 크기")


class QueryStatistics(BaseModel):
    """쿼리 통계"""
    total_queries: int = Field(..., description="전체 쿼리 수")
    successful_queries: int = Field(..., description="성공한 쿼리 수")
    failed_queries: int = Field(..., description="실패한 쿼리 수")
    avg_execution_time_ms: float = Field(..., description="평균 실행 시간 (ms)")
    total_data_scanned_gb: float = Field(..., description="총 스캔된 데이터 (GB)")
    
    # 쿼리 타입별 통계
    natural_language_count: int = Field(default=0, description="자연어 쿼리 수")
    template_count: int = Field(default=0, description="템플릿 쿼리 수")
    custom_count: int = Field(default=0, description="커스텀 쿼리 수")
    
    # 로그 타입별 통계
    queries_by_log_type: Dict[str, int] = Field(default={}, description="로그 타입별 쿼리 수")


class NaturalLanguageQueryRequest(BaseModel):
    """자연어 쿼리 요청"""
    question: str = Field(..., description="자연어 질문", min_length=5, max_length=500)
    database_name: str = Field(..., description="데이터베이스 이름")
    table_name: str = Field(..., description="테이블 이름")
    log_type: str = Field(default="s3_access", description="로그 타입")
    execute_immediately: bool = Field(default=True, description="즉시 실행 여부")
    
    class Config:
        json_schema_extra = {
            "example": {
                "question": "지난 7일간 가장 많이 접근된 파일 10개는?",
                "database_name": "log_analytics",
                "table_name": "s3_access_logs",
                "log_type": "s3_access",
                "execute_immediately": True
            }
        }


class NaturalLanguageQueryResponse(BaseModel):
    """자연어 쿼리 응답"""
    query_id: str = Field(..., description="쿼리 ID")
    
    # 생성된 SQL
    sql_query: str = Field(..., description="생성된 SQL 쿼리")
    explanation: str = Field(..., description="쿼리 설명")
    confidence: float = Field(..., description="신뢰도 (0-1)")
    
    # AI 메타데이터
    assumptions: List[str] = Field(default=[], description="가정한 사항")
    suggestions: List[str] = Field(default=[], description="추가 분석 제안")
    
    # 실행 결과 (execute_immediately=True인 경우)
    execution_status: Optional[QueryStatus] = Field(None, description="실행 상태")
    athena_query_execution_id: Optional[str] = Field(None, description="Athena 쿼리 실행 ID")
    results: Optional[List[Dict[str, Any]]] = Field(None, description="쿼리 결과")
    row_count: Optional[int] = Field(None, description="결과 행 수")
    execution_time_ms: Optional[int] = Field(None, description="실행 시간 (ms)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query_id": "550e8400-e29b-41d4-a716-446655440000",
                "sql_query": "SELECT key, COUNT(*) as count FROM logs.s3_access GROUP BY key ORDER BY count DESC LIMIT 10",
                "explanation": "최근 7일간의 S3 접근 로그에서 파일별 접근 횟수를 집계하여 상위 10개를 반환합니다",
                "confidence": 0.95,
                "assumptions": ["최근 7일은 파티션 기준으로 계산", "성공한 요청만 포함"],
                "suggestions": ["에러가 발생한 파일도 함께 분석해보세요", "시간대별 패턴도 확인해보세요"],
                "execution_status": "succeeded",
                "row_count": 10,
                "execution_time_ms": 1250
            }
        }


class SuggestedQuestion(BaseModel):
    """추천 질문"""
    question: str = Field(..., description="추천 질문")
    category: str = Field(..., description="카테고리")
    description: Optional[str] = Field(None, description="설명")
    
    class Config:
        json_schema_extra = {
            "example": {
                "question": "지난 7일간 가장 많이 접근된 파일은?",
                "category": "트래픽 분석",
                "description": "인기 콘텐츠를 파악하여 캐싱 전략을 수립할 수 있습니다"
            }
        }
