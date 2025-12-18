"""애플리케이션 설정 관리"""

from pydantic import Field
from pydantic_settings import BaseSettings
from typing import Optional


class AWSSettings(BaseSettings):
    """AWS 관련 설정"""
    region: str = Field(default="ap-northeast-2", description="AWS 리전")
    profile: Optional[str] = Field(default=None, description="AWS 프로파일")
    
    # S3 설정
    default_log_bucket_prefix: str = Field(default="s3-loglift-logs", description="기본 로그 버킷 접두사")
    
    # Athena 설정
    athena_database: str = Field(default="s3_loglift_analytics", description="Athena 데이터베이스 이름")
    athena_workgroup: str = Field(default="primary", description="Athena 워크그룹")
    athena_output_location: str = Field(default="s3://s3-loglift-athena-results/", description="Athena 결과 저장 위치")
    athena_results_bucket: str = Field(default="s3-loglift-athena-results", description="Athena 결과 저장 버킷")
    
    # Bedrock 설정 (inference profile ID 사용 필수)
    # Claude Opus 4.5: global.anthropic.claude-opus-4-5-20251101-v1:0
    # Claude Sonnet 4.5: global.anthropic.claude-sonnet-4-5-20250929-v1:0
    # Claude Haiku 4.5: global.anthropic.claude-haiku-4-5-20251001-v1:0
    bedrock_model_id: str = Field(default="global.anthropic.claude-sonnet-4-5-20250929-v1:0", description="Bedrock inference profile ID")
    bedrock_max_tokens: int = Field(default=2000, description="Bedrock 최대 토큰 수")

    class Config:
        env_prefix = "AWS_"


class DatabaseSettings(BaseSettings):
    """데이터베이스 설정"""
    redis_url: str = Field(default="redis://localhost:6379", description="Redis 연결 URL")
    redis_db: int = Field(default=0, description="Redis 데이터베이스 번호")
    cache_ttl: int = Field(default=3600, description="캐시 TTL (초)")

    class Config:
        env_prefix = "DB_"


class APISettings(BaseSettings):
    """API 서버 설정"""
    host: str = Field(default="0.0.0.0", description="서버 호스트")
    port: int = Field(default=8003, description="서버 포트")
    debug: bool = Field(default=False, description="디버그 모드")
    reload: bool = Field(default=False, description="자동 리로드")
    
    # 보안 설정
    secret_key: str = Field(default="your-secret-key-here", description="JWT 시크릿 키")
    access_token_expire_minutes: int = Field(default=30, description="액세스 토큰 만료 시간 (분)")
    
    # CORS 설정
    cors_origins: list[str] = Field(default=["http://localhost:3000"], description="CORS 허용 오리진")

    class Config:
        env_prefix = "API_"


class LoggingSettings(BaseSettings):
    """로깅 설정"""
    level: str = Field(default="INFO", description="로그 레벨")
    format: str = Field(default="json", description="로그 형식 (json|text)")
    
    class Config:
        env_prefix = "LOG_"


class Settings(BaseSettings):
    """전체 애플리케이션 설정"""
    
    # 환경 설정
    environment: str = Field(default="development", description="실행 환경")
    
    # 하위 설정들
    aws: AWSSettings = Field(default_factory=AWSSettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    api: APISettings = Field(default_factory=APISettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# 전역 설정 인스턴스
settings = Settings()