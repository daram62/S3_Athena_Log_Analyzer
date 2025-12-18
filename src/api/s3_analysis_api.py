"""Part 1: S3 → Athena 자동 셋업 API"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import boto3
from botocore.exceptions import ClientError
import logging

from ..services.log_detection_engine import log_detection_service, DetectionRequest
from ..services.ddl_generator import DDLGenerator
from ..models.log_schema import LogType, get_schema_for_log_type

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["s3-analysis"])

# AWS 클라이언트 초기화
s3_client = boto3.client('s3')
athena_client = boto3.client('athena')
glue_client = boto3.client('glue')

# 서비스 초기화
ddl_generator = DDLGenerator()


def _get_log_type_from_bucket_hint(bucket_name: str, fallback_type: str) -> LogType:
    """버킷 이름에서 로그 타입 힌트 추출 (테이블 생성 시 사용)"""
    bucket_lower = bucket_name.lower()
    
    # 버킷 이름 기반 힌트 (우선순위 순)
    if 'alb' in bucket_lower or 'elb' in bucket_lower:
        return LogType.ALB
    elif 'cloudfront' in bucket_lower or 'cf-' in bucket_lower:
        return LogType.CLOUDFRONT
    elif 'vpc' in bucket_lower and 'flow' in bucket_lower:
        return LogType.VPC_FLOW
    elif 'cloudtrail' in bucket_lower:
        return LogType.CLOUDTRAIL
    
    # 힌트가 없으면 원래 타입 사용
    try:
        return LogType(fallback_type)
    except ValueError:
        return LogType.S3_ACCESS


class BucketInfo(BaseModel):
    """S3 버킷 정보"""
    name: str
    creation_date: str
    region: Optional[str] = None


class LogAnalysisRequest(BaseModel):
    """로그 분석 요청"""
    bucket_name: str
    prefix: Optional[str] = ""
    max_samples: int = 10


class LogAnalysisResult(BaseModel):
    """로그 분석 결과"""
    bucket_name: str
    log_type: str
    confidence: float
    sample_count: int
    total_files: int
    total_size_mb: float
    date_range: Optional[Dict[str, str]] = None
    inferred_schema: Dict[str, Any]
    partition_strategy: str
    field_count: int


class TableCreationRequest(BaseModel):
    """테이블 생성 요청"""
    bucket_name: str
    log_type: str
    database_name: str = "genai_log_analyzer"
    table_name: Optional[str] = None
    s3_location: Optional[str] = None


class TableCreationResult(BaseModel):
    """테이블 생성 결과"""
    database_name: str
    table_name: str
    ddl_statement: str
    status: str
    message: str


@router.get("/")
async def root():
    """API 루트"""
    return {
        "service": "Gen-AI Log Analyzer",
        "version": "1.0.0",
        "part": "Part 1: S3 → Athena Auto Setup",
        "supported_log_types": ["s3_access", "cloudfront", "alb", "vpc_flow", "cloudtrail"]
    }


@router.get("/buckets", response_model=List[BucketInfo])
async def list_buckets():
    """S3 버킷 목록 조회"""
    try:
        response = s3_client.list_buckets()
        
        buckets = []
        for bucket in response['Buckets']:
            # 버킷 리전 조회
            try:
                location = s3_client.get_bucket_location(Bucket=bucket['Name'])
                region = location['LocationConstraint'] or 'us-east-1'
            except:
                region = None
            
            buckets.append(BucketInfo(
                name=bucket['Name'],
                creation_date=bucket['CreationDate'].isoformat(),
                region=region
            ))
        
        return buckets
        
    except ClientError as e:
        raise HTTPException(status_code=500, detail=f"S3 버킷 목록 조회 실패: {str(e)}")


@router.get("/buckets/{bucket_name}/folders")
async def list_folders(bucket_name: str, prefix: str = ""):
    """S3 버킷의 폴더 목록 조회"""
    try:
        response = s3_client.list_objects_v2(
            Bucket=bucket_name,
            Prefix=prefix,
            Delimiter='/',
            MaxKeys=100
        )
        
        folders = []
        
        if 'CommonPrefixes' in response:
            for prefix_obj in response['CommonPrefixes']:
                folder_path = prefix_obj['Prefix']
                folders.append({
                    "path": folder_path,
                    "name": folder_path.rstrip('/').split('/')[-1] + '/'
                })
        
        return {
            "bucket": bucket_name,
            "folders": folders
        }
        
    except ClientError as e:
        raise HTTPException(status_code=500, detail=f"폴더 목록 조회 실패: {str(e)}")


@router.post("/analyze-logs", response_model=LogAnalysisResult)
async def analyze_logs(request: LogAnalysisRequest):
    """로그 파일 분석 (타입 감지, 스키마 추론) - 강력한 로그 감지 엔진 사용"""
    try:
        logger.info(f"로그 분석 시작: bucket={request.bucket_name}, prefix={request.prefix}")
        
        # 비동기 감지 실행 (키워드 인자로 전달)
        result = await log_detection_service.detect_logs_async(
            bucket_name=request.bucket_name,
            prefix=request.prefix or "",
            max_files=request.max_samples,
            detailed_analysis=True
        )
        
        if not result.success:
            raise HTTPException(status_code=500, detail=result.error_message or "로그 분석 실패")
        
        # 주요 로그 타입 결정
        primary_log_type = result.scan_result.primary_log_type
        if not primary_log_type:
            raise HTTPException(status_code=422, detail="로그 타입을 감지할 수 없습니다")
        
        logger.info(f"감지된 로그 타입: {primary_log_type}, 타입: {type(primary_log_type)}")
        
        # 스키마 정보 가져오기
        schema = get_schema_for_log_type(primary_log_type)
        if not schema:
            logger.error(f"스키마 조회 실패: log_type={primary_log_type}, type={type(primary_log_type)}")
            raise HTTPException(status_code=500, detail=f"지원하지 않는 로그 타입: {primary_log_type}")
        
        # 신뢰도 계산
        total_files = result.scan_result.log_files_count
        detected_count = result.scan_result.detected_log_types.get(primary_log_type, 0)
        confidence = detected_count / total_files if total_files > 0 else 0.0
        
        # 스키마 정보 구성
        inferred_schema = {
            "fields": [
                {"name": field.name, "type": field.type.value, "description": field.description}
                for field in schema.fields
            ],
            "partition_keys": schema.partition_fields
        }
        
        # 날짜 범위
        date_range = None
        if result.scan_result.date_range:
            date_range = {
                "start": result.scan_result.date_range[0].isoformat(),
                "end": result.scan_result.date_range[1].isoformat()
            }
        
        logger.info(f"로그 분석 완료: type={primary_log_type.value}, confidence={confidence:.2f}")
        
        return LogAnalysisResult(
            bucket_name=request.bucket_name,
            log_type=primary_log_type.value,
            confidence=confidence,
            sample_count=len(result.scan_result.log_files),
            total_files=result.scan_result.total_files,
            total_size_mb=result.scan_result.total_size_gb * 1024,
            date_range=date_range,
            inferred_schema=inferred_schema,
            partition_strategy="date",
            field_count=len(schema.fields)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"로그 분석 오류: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"로그 분석 실패: {str(e)}")


@router.post("/tables/create", response_model=TableCreationResult)
async def create_table(request: TableCreationRequest):
    """Athena 테이블 자동 생성 - DDL Generator 사용"""
    try:
        logger.info(f"테이블 생성 시작: {request.database_name}.{request.table_name}")
        
        # 1. 로그 타입 변환 (버킷 이름 힌트 우선 적용)
        log_type = _get_log_type_from_bucket_hint(request.bucket_name, request.log_type)
        logger.info(f"최종 로그 타입: {log_type.value} (원본: {request.log_type})")
        
        # 2. 데이터베이스 생성 (없으면)
        try:
            glue_client.create_database(
                DatabaseInput={'Name': request.database_name}
            )
            logger.info(f"데이터베이스 생성: {request.database_name}")
        except glue_client.exceptions.AlreadyExistsException:
            logger.info(f"데이터베이스 이미 존재: {request.database_name}")
        
        # 3. 테이블명 생성
        table_name = request.table_name or f"{request.log_type}_logs"
        
        # 4. S3 위치 결정
        s3_location = request.s3_location or f"s3://{request.bucket_name}/"
        if not s3_location.endswith('/'):
            s3_location += '/'
        
        # 5. DDL 생성 (DDL Generator 사용)
        logger.info(f"DDL 생성 시작: log_type={log_type}, log_type.value={log_type.value}")
        ddl = ddl_generator.generate_create_table_ddl(
            database_name=request.database_name,
            table_name=table_name,
            s3_location=s3_location,
            log_type=log_type,
            partition_strategy="daily",
            enable_partition_projection=True
        )
        logger.info(f"생성된 DDL (처음 500자): {ddl[:500]}")
        
        # 6. Athena에서 DDL 실행
        athena_output = f"s3://{request.bucket_name}/athena-results/"
        
        response = athena_client.start_query_execution(
            QueryString=ddl,
            QueryExecutionContext={'Database': request.database_name},
            ResultConfiguration={'OutputLocation': athena_output}
        )
        
        query_execution_id = response['QueryExecutionId']
        logger.info(f"Athena 쿼리 실행: {query_execution_id}")
        
        # 7. 쿼리 완료 대기 (최대 30초)
        import time
        max_wait = 30
        waited = 0
        
        while waited < max_wait:
            status_response = athena_client.get_query_execution(
                QueryExecutionId=query_execution_id
            )
            status = status_response['QueryExecution']['Status']['State']
            
            if status == 'SUCCEEDED':
                logger.info(f"테이블 생성 성공: {request.database_name}.{table_name}")
                return TableCreationResult(
                    database_name=request.database_name,
                    table_name=table_name,
                    ddl_statement=ddl,
                    status="success",
                    message=f"테이블 {request.database_name}.{table_name}이 성공적으로 생성되었습니다"
                )
            elif status == 'FAILED':
                error_msg = status_response['QueryExecution']['Status'].get('StateChangeReason', 'Unknown error')
                logger.error(f"테이블 생성 실패: {error_msg}")
                raise HTTPException(status_code=500, detail=f"테이블 생성 실패: {error_msg}")
            elif status == 'CANCELLED':
                raise HTTPException(status_code=500, detail="쿼리가 취소되었습니다")
            
            time.sleep(1)
            waited += 1
        
        raise HTTPException(status_code=504, detail="테이블 생성 시간 초과")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"테이블 생성 오류: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"테이블 생성 실패: {str(e)}")


@router.get("/tables/check/{database_name}/{table_name}")
async def check_table(database_name: str, table_name: str):
    """테이블 존재 여부 확인"""
    try:
        response = glue_client.get_table(
            DatabaseName=database_name,
            Name=table_name
        )
        
        table = response['Table']
        
        return {
            "exists": True,
            "database": database_name,
            "table": table_name,
            "location": table.get('StorageDescriptor', {}).get('Location'),
            "created": table.get('CreateTime').isoformat() if table.get('CreateTime') else None
        }
        
    except glue_client.exceptions.EntityNotFoundException:
        return {
            "exists": False,
            "database": database_name,
            "table": table_name
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"테이블 확인 실패: {str(e)}")


@router.get("/health")
async def health():
    """헬스 체크"""
    return {
        "status": "healthy",
        "service": "s3-analysis-api",
        "supported_log_types": [lt.value for lt in LogType]
    }
