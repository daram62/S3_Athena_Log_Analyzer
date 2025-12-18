"""테이블 관리 API - 생성된 Athena 테이블 관리"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import boto3
from botocore.exceptions import ClientError
from datetime import datetime
import logging

from ..models.log_schema import LogType

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/tables", tags=["table-management"])

# AWS 클라이언트
glue_client = boto3.client('glue')
athena_client = boto3.client('athena')


class TableInfo(BaseModel):
    """테이블 정보"""
    database_name: str
    table_name: str
    log_type: str
    s3_location: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    row_count: Optional[int] = None
    size_mb: Optional[float] = None
    partition_count: Optional[int] = None
    field_count: int
    status: str = "active"


class TableListResponse(BaseModel):
    """테이블 목록 응답"""
    tables: List[TableInfo]
    total_count: int
    database_name: str


class TableDetailResponse(BaseModel):
    """테이블 상세 정보"""
    table_info: TableInfo
    columns: List[Dict[str, str]]
    partitions: List[str]
    sample_queries: List[Dict[str, str]]


class TableDeleteRequest(BaseModel):
    """테이블 삭제 요청"""
    database_name: str
    table_name: str
    delete_data: bool = False


@router.get("/list", response_model=TableListResponse)
async def list_tables(database_name: Optional[str] = None):
    """모든 데이터베이스의 테이블 목록 조회 (database_name이 없으면 모든 DB 스캔)"""
    try:
        tables = []
        
        # 데이터베이스 목록 결정
        if database_name:
            # 특정 데이터베이스만 조회
            database_names = [database_name]
        else:
            # db_ 접두사가 있는 데이터베이스만 조회 (성능 최적화)
            try:
                db_response = glue_client.get_databases()
                database_names = [
                    db['Name'] for db in db_response['DatabaseList']
                    if db['Name'].startswith('db_')
                ]
                logger.info(f"db_ 접두사 데이터베이스 {len(database_names)}개 발견")
            except Exception as e:
                logger.warning(f"데이터베이스 목록 조회 실패: {str(e)}")
                database_names = []
        
        # 각 데이터베이스의 테이블 조회
        for db_name in database_names:
            try:
                paginator = glue_client.get_paginator('get_tables')
                
                for page in paginator.paginate(DatabaseName=db_name):
                    for table in page['TableList']:
                        # 로그 타입 추론 (테이블명에서)
                        table_name = table['Name']
                        log_type = _infer_log_type_from_table_name(table_name)
                        
                        # S3 위치
                        s3_location = table.get('StorageDescriptor', {}).get('Location', '')
                        
                        # 생성/수정 시간
                        created_at = table.get('CreateTime')
                        updated_at = table.get('UpdateTime')
                        
                        # 필드 수
                        columns = table.get('StorageDescriptor', {}).get('Columns', [])
                        field_count = len(columns)
                        
                        # 파티션 수 조회
                        partition_count = _get_partition_count(db_name, table_name)
                        
                        tables.append(TableInfo(
                            database_name=db_name,
                            table_name=table_name,
                            log_type=log_type,
                            s3_location=s3_location,
                            created_at=created_at.isoformat() if created_at else None,
                            updated_at=updated_at.isoformat() if updated_at else None,
                            field_count=field_count,
                            partition_count=partition_count,
                            status="active"
                        ))
            except Exception as e:
                logger.warning(f"데이터베이스 {db_name} 테이블 조회 실패: {str(e)}")
                continue
        
        return TableListResponse(
            tables=tables,
            total_count=len(tables),
            database_name=database_name or "all"
        )
        
    except Exception as e:
        logger.error(f"테이블 목록 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"테이블 목록 조회 실패: {str(e)}")


@router.get("/detail/{database_name}/{table_name}", response_model=TableDetailResponse)
async def get_table_detail(database_name: str, table_name: str):
    """테이블 상세 정보 조회"""
    try:
        # 테이블 정보 조회
        response = glue_client.get_table(
            DatabaseName=database_name,
            Name=table_name
        )
        
        table = response['Table']
        
        # 기본 정보
        log_type = _infer_log_type_from_table_name(table_name)
        s3_location = table.get('StorageDescriptor', {}).get('Location', '')
        created_at = table.get('CreateTime')
        updated_at = table.get('UpdateTime')
        
        # 컬럼 정보
        columns = []
        for col in table.get('StorageDescriptor', {}).get('Columns', []):
            columns.append({
                'name': col['Name'],
                'type': col['Type'],
                'comment': col.get('Comment', '')
            })
        
        # 파티션 키
        partition_keys = []
        for pk in table.get('PartitionKeys', []):
            partition_keys.append(pk['Name'])
        
        # 파티션 수
        partition_count = _get_partition_count(database_name, table_name)
        
        # 테이블 통계 (행 수, 크기)
        stats = _get_table_statistics(database_name, table_name, s3_location)
        
        # 샘플 쿼리 생성
        sample_queries = _generate_sample_queries(database_name, table_name, log_type)
        
        table_info = TableInfo(
            database_name=database_name,
            table_name=table_name,
            log_type=log_type,
            s3_location=s3_location,
            created_at=created_at.isoformat() if created_at else None,
            updated_at=updated_at.isoformat() if updated_at else None,
            field_count=len(columns),
            partition_count=partition_count,
            row_count=stats.get('row_count'),
            size_mb=stats.get('size_mb'),
            status="active"
        )
        
        return TableDetailResponse(
            table_info=table_info,
            columns=columns,
            partitions=partition_keys,
            sample_queries=sample_queries
        )
        
    except glue_client.exceptions.EntityNotFoundException:
        raise HTTPException(status_code=404, detail=f"테이블을 찾을 수 없습니다: {database_name}.{table_name}")
    except Exception as e:
        logger.error(f"테이블 상세 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"테이블 상세 조회 실패: {str(e)}")


@router.delete("/delete")
async def delete_table(request: TableDeleteRequest):
    """테이블 삭제"""
    try:
        # 테이블 존재 확인
        try:
            glue_client.get_table(
                DatabaseName=request.database_name,
                Name=request.table_name
            )
        except glue_client.exceptions.EntityNotFoundException:
            raise HTTPException(status_code=404, detail=f"테이블을 찾을 수 없습니다: {request.table_name}")
        
        # 테이블 삭제
        glue_client.delete_table(
            DatabaseName=request.database_name,
            Name=request.table_name
        )
        
        logger.info(f"테이블 삭제 완료: {request.database_name}.{request.table_name}")
        
        return {
            "success": True,
            "message": f"테이블 {request.table_name}이 삭제되었습니다",
            "database_name": request.database_name,
            "table_name": request.table_name
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"테이블 삭제 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"테이블 삭제 실패: {str(e)}")


@router.post("/refresh-partitions/{database_name}/{table_name}")
async def refresh_partitions(database_name: str, table_name: str):
    """파티션 새로고침 (MSCK REPAIR TABLE)"""
    try:
        # Athena 쿼리 실행
        query = f"MSCK REPAIR TABLE `{database_name}`.`{table_name}`"
        
        # 출력 위치 (.env에서 가져오거나 기본값 사용)
        import os
        output_location = os.getenv('AWS_ATHENA_OUTPUT_LOCATION', 's3://athena-query-results-619710251562/')
        
        response = athena_client.start_query_execution(
            QueryString=query,
            QueryExecutionContext={'Database': database_name},
            ResultConfiguration={'OutputLocation': output_location}
        )
        
        query_execution_id = response['QueryExecutionId']
        
        # 쿼리 완료 대기 (최대 30초)
        import time
        max_wait = 30
        waited = 0
        
        while waited < max_wait:
            status_response = athena_client.get_query_execution(
                QueryExecutionId=query_execution_id
            )
            status = status_response['QueryExecution']['Status']['State']
            
            if status == 'SUCCEEDED':
                return {
                    "success": True,
                    "message": f"파티션 새로고침 완료",
                    "query_execution_id": query_execution_id
                }
            elif status in ['FAILED', 'CANCELLED']:
                error_msg = status_response['QueryExecution']['Status'].get('StateChangeReason', 'Unknown error')
                raise HTTPException(status_code=500, detail=f"파티션 새로고침 실패: {error_msg}")
            
            time.sleep(1)
            waited += 1
        
        raise HTTPException(status_code=504, detail="파티션 새로고침 시간 초과")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"파티션 새로고침 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"파티션 새로고침 실패: {str(e)}")


def _infer_log_type_from_table_name(table_name: str) -> str:
    """테이블명에서 로그 타입 추론"""
    table_name_lower = table_name.lower()
    
    if 's3' in table_name_lower and 'access' in table_name_lower:
        return LogType.S3_ACCESS.value
    elif 'cloudfront' in table_name_lower:
        return LogType.CLOUDFRONT.value
    elif 'alb' in table_name_lower or 'elb' in table_name_lower:
        return LogType.ALB.value
    elif 'vpc' in table_name_lower and 'flow' in table_name_lower:
        return LogType.VPC_FLOW.value
    elif 'cloudtrail' in table_name_lower:
        return LogType.CLOUDTRAIL.value
    else:
        return "unknown"


def _get_partition_count(database_name: str, table_name: str) -> int:
    """파티션 수 조회"""
    try:
        paginator = glue_client.get_paginator('get_partitions')
        partition_count = 0
        
        for page in paginator.paginate(DatabaseName=database_name, TableName=table_name):
            partition_count += len(page.get('Partitions', []))
        
        return partition_count
    except:
        return 0


def _get_table_statistics(database_name: str, table_name: str, s3_location: str) -> Dict[str, Any]:
    """테이블 통계 조회 (간단한 COUNT 쿼리)"""
    # 실제 구현에서는 Athena 쿼리를 실행하여 통계를 가져올 수 있습니다
    # 여기서는 기본값 반환
    return {
        'row_count': None,
        'size_mb': None
    }


def _generate_sample_queries(database_name: str, table_name: str, log_type: str) -> List[Dict[str, str]]:
    """로그 타입별 샘플 쿼리 생성"""
    full_table = f"`{database_name}`.`{table_name}`"
    
    queries = [
        {
            "name": "데이터 미리보기",
            "description": "최근 데이터 10개 조회",
            "sql": f"SELECT * FROM {full_table} LIMIT 10;"
        },
        {
            "name": "전체 행 수",
            "description": "테이블의 총 행 수 확인",
            "sql": f"SELECT COUNT(*) as total_rows FROM {full_table};"
        }
    ]
    
    # 로그 타입별 특화 쿼리
    if log_type == LogType.S3_ACCESS.value:
        queries.extend([
            {
                "name": "상위 IP 주소",
                "description": "요청이 가장 많은 IP 주소 10개",
                "sql": f"SELECT remote_ip, COUNT(*) as request_count FROM {full_table} GROUP BY remote_ip ORDER BY request_count DESC LIMIT 10;"
            },
            {
                "name": "에러 분석",
                "description": "HTTP 4xx, 5xx 에러 분석",
                "sql": f"SELECT http_status, COUNT(*) as error_count FROM {full_table} WHERE http_status >= 400 GROUP BY http_status ORDER BY error_count DESC;"
            }
        ])
    elif log_type == LogType.ALB.value:
        queries.extend([
            {
                "name": "응답 시간 분석",
                "description": "평균 응답 시간 및 느린 요청",
                "sql": f"SELECT AVG(target_processing_time) as avg_time, MAX(target_processing_time) as max_time FROM {full_table};"
            },
            {
                "name": "상태 코드 분포",
                "description": "ELB 상태 코드별 요청 수",
                "sql": f"SELECT elb_status_code, COUNT(*) as count FROM {full_table} GROUP BY elb_status_code ORDER BY count DESC;"
            }
        ])
    elif log_type == LogType.CLOUDTRAIL.value:
        queries.extend([
            {
                "name": "최근 이벤트",
                "description": "최근 CloudTrail 이벤트 조회",
                "sql": f"SELECT eventtime, eventname, eventsource, sourceipaddress FROM {full_table} ORDER BY eventtime DESC LIMIT 20;"
            },
            {
                "name": "이벤트 통계",
                "description": "이벤트 타입별 통계",
                "sql": f"SELECT eventname, COUNT(*) as event_count FROM {full_table} GROUP BY eventname ORDER BY event_count DESC LIMIT 10;"
            }
        ])
    
    return queries
