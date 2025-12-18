"""
DDL 생성 엔진
로그 타입별 Athena 테이블 생성 DDL을 자동으로 생성
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import re
from pathlib import Path

from ..models.log_schema import LogType, LogSchema, get_schema_for_log_type
from ..models.log_configuration import LogConfiguration


class DDLGenerator:
    """DDL 생성 엔진"""
    
    def __init__(self):
        self.supported_log_types = [
            LogType.S3_ACCESS,
            LogType.CLOUDFRONT,
            LogType.ALB,
            LogType.VPC_FLOW,
            LogType.CLOUDTRAIL
        ]
    
    def generate_create_table_ddl(self,
                                database_name: str,
                                table_name: str,
                                s3_location: str,
                                log_type: LogType = LogType.S3_ACCESS,
                                partition_strategy: str = "monthly",
                                enable_partition_projection: bool = True) -> str:
        """
        CREATE TABLE DDL 생성
        
        Args:
            database_name: 데이터베이스 이름
            table_name: 테이블 이름
            s3_location: S3 로그 위치
            log_type: 로그 타입
            partition_strategy: 파티션 전략 (daily, monthly, yearly)
            enable_partition_projection: 파티션 프로젝션 활성화 여부
        
        Returns:
            CREATE TABLE DDL 문자열
        """
        
        schema = get_schema_for_log_type(log_type)
        if not schema:
            raise ValueError(f"Unsupported log type: {log_type}")
        
        # S3 위치 정규화
        s3_location = self._normalize_s3_location(s3_location)
        
        # 파티션 프로젝션 설정 생성
        projection_properties = ""
        if enable_partition_projection:
            projection_properties = self._generate_partition_projection(
                s3_location, partition_strategy
            )
        
        # 기본 DDL 생성
        ddl = schema.get_create_table_ddl(
            database_name=database_name,
            table_name=table_name,
            s3_location=s3_location,
            partition_projection=enable_partition_projection
        )
        
        # 파티션 프로젝션 속성 추가
        if projection_properties:
            ddl = ddl.replace(
                "'storage.location.template'='s3://your-bucket/logs/${year}/${month}/${day}/'",
                f"'storage.location.template'='{s3_location}${{year}}/${{month}}/${{day}}/'"
            )
        
        return ddl
    
    def generate_partition_repair_queries(self,
                                        database_name: str,
                                        table_name: str,
                                        start_date: datetime,
                                        end_date: datetime,
                                        partition_strategy: str = "monthly") -> List[str]:
        """
        파티션 복구 쿼리 생성 (파티션 프로젝션을 사용하지 않는 경우)
        
        Args:
            database_name: 데이터베이스 이름
            table_name: 테이블 이름
            start_date: 시작 날짜
            end_date: 종료 날짜
            partition_strategy: 파티션 전략
        
        Returns:
            ALTER TABLE ADD PARTITION 쿼리 목록
        """
        
        queries = []
        current_date = start_date
        
        while current_date <= end_date:
            if partition_strategy == "daily":
                partition_spec = f"year='{current_date.year}', month='{current_date.month:02d}', day='{current_date.day:02d}'"
                current_date += timedelta(days=1)
            elif partition_strategy == "monthly":
                partition_spec = f"year='{current_date.year}', month='{current_date.month:02d}'"
                # 다음 달로 이동
                if current_date.month == 12:
                    current_date = current_date.replace(year=current_date.year + 1, month=1)
                else:
                    current_date = current_date.replace(month=current_date.month + 1)
            elif partition_strategy == "yearly":
                partition_spec = f"year='{current_date.year}'"
                current_date = current_date.replace(year=current_date.year + 1)
            else:
                raise ValueError(f"Unsupported partition strategy: {partition_strategy}")
            
            query = f"""ALTER TABLE `{database_name}`.`{table_name}` 
ADD PARTITION ({partition_spec})"""
            queries.append(query)
        
        return queries
    
    def generate_sample_queries(self,
                              database_name: str,
                              table_name: str,
                              log_type: LogType = LogType.S3_ACCESS) -> Dict[str, str]:
        """
        샘플 쿼리 생성
        
        Args:
            database_name: 데이터베이스 이름
            table_name: 테이블 이름
            log_type: 로그 타입
        
        Returns:
            샘플 쿼리 딕셔너리
        """
        
        full_table_name = f"`{database_name}`.`{table_name}`"
        
        if log_type == LogType.S3_ACCESS:
            return {
                "basic_select": f"""-- Basic data preview
SELECT *
FROM {full_table_name}
WHERE year = '2024' AND month = '01'
LIMIT 10;""",
                
                "top_ips": f"""-- Top 10 IP addresses by request count
SELECT 
    remote_ip,
    COUNT(*) as request_count,
    SUM(CAST(bytes_sent AS bigint)) as total_bytes_sent
FROM {full_table_name}
WHERE year = '2024' AND month = '01'
    AND bytes_sent != '-'
GROUP BY remote_ip
ORDER BY request_count DESC
LIMIT 10;""",
                
                "error_analysis": f"""-- Error analysis
SELECT 
    http_status,
    error_code,
    COUNT(*) as error_count,
    COUNT(*) * 100.0 / SUM(COUNT(*)) OVER() as percentage
FROM {full_table_name}
WHERE year = '2024' AND month = '01'
    AND http_status >= 400
GROUP BY http_status, error_code
ORDER BY error_count DESC;""",
                
                "hourly_traffic": f"""-- Hourly traffic pattern
SELECT 
    EXTRACT(hour FROM date_parse(regexp_replace(time, '\\[|\\]', ''), '%d/%b/%Y:%H:%i:%s %z')) as hour,
    COUNT(*) as requests,
    SUM(CAST(bytes_sent AS bigint)) / 1024 / 1024 as mb_transferred
FROM {full_table_name}
WHERE year = '2024' AND month = '01' AND day = '01'
    AND bytes_sent != '-'
GROUP BY EXTRACT(hour FROM date_parse(regexp_replace(time, '\\[|\\]', ''), '%d/%b/%Y:%H:%i:%s %z'))
ORDER BY hour;""",
                
                "popular_objects": f"""-- Most accessed objects
SELECT 
    key,
    COUNT(*) as access_count,
    SUM(CAST(bytes_sent AS bigint)) as total_bytes
FROM {full_table_name}
WHERE year = '2024' AND month = '01'
    AND operation = 'REST.GET.OBJECT'
    AND http_status = 200
    AND key != '-'
GROUP BY key
ORDER BY access_count DESC
LIMIT 20;""",
                
                "user_agents": f"""-- User agent analysis
SELECT 
    user_agent,
    COUNT(*) as request_count,
    COUNT(DISTINCT remote_ip) as unique_ips
FROM {full_table_name}
WHERE year = '2024' AND month = '01'
    AND user_agent != '-'
GROUP BY user_agent
ORDER BY request_count DESC
LIMIT 15;"""
            }
        
        return {}
    
    def validate_ddl_syntax(self, ddl: str) -> Tuple[bool, Optional[str]]:
        """
        DDL 구문 검증
        
        Args:
            ddl: 검증할 DDL 문자열
        
        Returns:
            (유효성, 오류 메시지)
        """
        
        try:
            # 기본적인 구문 검증
            if not ddl.strip().upper().startswith('CREATE'):
                return False, "DDL must start with CREATE statement"
            
            # 필수 키워드 확인
            required_keywords = ['CREATE', 'EXTERNAL', 'TABLE', 'STORED', 'LOCATION']
            ddl_upper = ddl.upper()
            
            for keyword in required_keywords:
                if keyword not in ddl_upper:
                    return False, f"Missing required keyword: {keyword}"
            
            # 괄호 균형 확인
            open_parens = ddl.count('(')
            close_parens = ddl.count(')')
            if open_parens != close_parens:
                return False, "Unbalanced parentheses in DDL"
            
            # S3 위치 형식 확인
            s3_pattern = r"s3://[a-z0-9.-]+(/.*)?/?"
            if not re.search(s3_pattern, ddl, re.IGNORECASE):
                return False, "Invalid S3 location format"
            
            return True, None
            
        except Exception as e:
            return False, f"DDL validation error: {str(e)}"
    
    def _normalize_s3_location(self, s3_location: str) -> str:
        """S3 위치 정규화"""
        # s3:// 접두사 확인
        if not s3_location.startswith('s3://'):
            s3_location = f's3://{s3_location}'
        
        # 끝에 슬래시 추가
        if not s3_location.endswith('/'):
            s3_location += '/'
        
        return s3_location
    
    def _generate_partition_projection(self, s3_location: str, strategy: str) -> str:
        """파티션 프로젝션 설정 생성"""
        
        current_year = datetime.now().year
        
        if strategy == "daily":
            return f""",
  'projection.enabled'='true',
  'projection.year.type'='integer',
  'projection.year.range'='{current_year-2},{current_year+1}',
  'projection.year.interval'='1',
  'projection.month.type'='integer',
  'projection.month.range'='1,12',
  'projection.month.interval'='1',
  'projection.day.type'='integer',
  'projection.day.range'='1,31',
  'projection.day.interval'='1',
  'storage.location.template'='{s3_location}${{year}}/${{month}}/${{day}}/'"""
        
        elif strategy == "monthly":
            return f""",
  'projection.enabled'='true',
  'projection.year.type'='integer',
  'projection.year.range'='{current_year-2},{current_year+1}',
  'projection.year.interval'='1',
  'projection.month.type'='integer',
  'projection.month.range'='1,12',
  'projection.month.interval'='1',
  'storage.location.template'='{s3_location}${{year}}/${{month}}/'"""
        
        elif strategy == "yearly":
            return f""",
  'projection.enabled'='true',
  'projection.year.type'='integer',
  'projection.year.range'='{current_year-5},{current_year+1}',
  'projection.year.interval'='1',
  'storage.location.template'='{s3_location}${{year}}/'"""
        
        return ""


# 전역 DDL 생성기 인스턴스
ddl_generator = DDLGenerator()


def generate_s3_access_log_table(database_name: str,
                                table_name: str,
                                s3_location: str,
                                partition_strategy: str = "monthly") -> Dict[str, any]:
    """
    S3 Access Log 테이블 생성을 위한 완전한 DDL 패키지 생성
    
    Returns:
        DDL과 샘플 쿼리가 포함된 딕셔너리
    """
    
    # DDL 생성
    create_ddl = ddl_generator.generate_create_table_ddl(
        database_name=database_name,
        table_name=table_name,
        s3_location=s3_location,
        log_type=LogType.S3_ACCESS,
        partition_strategy=partition_strategy
    )
    
    # 샘플 쿼리 생성
    sample_queries = ddl_generator.generate_sample_queries(
        database_name=database_name,
        table_name=table_name,
        log_type=LogType.S3_ACCESS
    )
    
    # DDL 검증
    is_valid, error_message = ddl_generator.validate_ddl_syntax(create_ddl)
    
    return {
        "create_table_ddl": create_ddl,
        "sample_queries": sample_queries,
        "is_valid": is_valid,
        "error_message": error_message,
        "log_type": LogType.S3_ACCESS.value,
        "partition_strategy": partition_strategy,
        "field_count": 26,
        "supports_partition_projection": True
    }