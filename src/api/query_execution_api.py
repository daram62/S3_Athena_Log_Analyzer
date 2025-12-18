"""쿼리 실행 API - Athena 쿼리 실행"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import time

from ..services.aws_clients import aws_client_manager

router = APIRouter(prefix="/api/v1/query", tags=["query-execution"])


class QueryExecuteRequest(BaseModel):
    """쿼리 실행 요청"""
    query: str
    database: str
    output_location: Optional[str] = None


class QueryExecuteResponse(BaseModel):
    """쿼리 실행 응답"""
    query_execution_id: str
    status: str
    columns: List[str] = []
    rows: List[List[str]] = []
    execution_time_ms: int = 0
    data_scanned_bytes: int = 0
    error_message: Optional[str] = None


@router.post("/execute", response_model=QueryExecuteResponse)
async def execute_query(request: QueryExecuteRequest):
    """Athena 쿼리 실행"""
    try:
        from ..services.aws_clients import AWSServiceType
        import logging
        logger = logging.getLogger(__name__)
        
        athena_client = aws_client_manager.get_client(AWSServiceType.ATHENA)
        
        # 출력 위치 설정 (환경 변수 또는 기본값)
        import os
        default_output = os.getenv('ATHENA_OUTPUT_LOCATION', 's3://athena-results-ap-northeast-2-777786711649/')
        output_location = request.output_location or default_output
        
        # 쿼리 로깅
        logger.info(f"Executing query on database: {request.database}")
        logger.info(f"Query: {request.query[:200]}...")
        
        # 쿼리 실행
        start_time = time.time()
        response = athena_client.start_query_execution(
            QueryString=request.query,
            QueryExecutionContext={'Database': request.database},
            ResultConfiguration={'OutputLocation': output_location}
        )
        
        query_execution_id = response['QueryExecutionId']
        
        # 쿼리 완료 대기 (최대 30초)
        max_wait = 30
        wait_interval = 0.5
        elapsed = 0
        
        while elapsed < max_wait:
            execution_response = athena_client.get_query_execution(
                QueryExecutionId=query_execution_id
            )
            
            status = execution_response['QueryExecution']['Status']['State']
            
            if status in ['SUCCEEDED', 'FAILED', 'CANCELLED']:
                break
            
            time.sleep(wait_interval)
            elapsed += wait_interval
        
        execution_time_ms = int((time.time() - start_time) * 1000)
        
        # 실행 결과 확인
        if status == 'SUCCEEDED':
            # 결과 가져오기
            results = athena_client.get_query_results(
                QueryExecutionId=query_execution_id,
                MaxResults=100  # 최대 100개 행만 반환
            )
            
            # 컬럼 이름 추출
            columns = []
            if 'ResultSet' in results and 'ColumnInfo' in results['ResultSet']['ResultSetMetadata']:
                columns = [col['Name'] for col in results['ResultSet']['ResultSetMetadata']['ColumnInfo']]
            
            # 데이터 행 추출 (첫 번째 행은 헤더이므로 제외)
            rows = []
            if 'ResultSet' in results and 'Rows' in results['ResultSet']:
                for row in results['ResultSet']['Rows'][1:]:  # 헤더 제외
                    row_data = [field.get('VarCharValue', '') for field in row['Data']]
                    rows.append(row_data)
            
            # 스캔된 데이터 크기
            data_scanned_bytes = execution_response['QueryExecution']['Statistics'].get('DataScannedInBytes', 0)
            
            return QueryExecuteResponse(
                query_execution_id=query_execution_id,
                status=status,
                columns=columns,
                rows=rows,
                execution_time_ms=execution_time_ms,
                data_scanned_bytes=data_scanned_bytes
            )
        
        elif status == 'FAILED':
            error_message = execution_response['QueryExecution']['Status'].get('StateChangeReason', 'Unknown error')
            return QueryExecuteResponse(
                query_execution_id=query_execution_id,
                status=status,
                error_message=error_message,
                execution_time_ms=execution_time_ms
            )
        
        else:
            return QueryExecuteResponse(
                query_execution_id=query_execution_id,
                status=status,
                error_message=f"Query execution timed out or was cancelled (status: {status})",
                execution_time_ms=execution_time_ms
            )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query execution failed: {str(e)}")


@router.get("/status/{query_execution_id}")
async def get_query_status(query_execution_id: str):
    """쿼리 실행 상태 조회"""
    try:
        from ..services.aws_clients import AWSServiceType
        athena_client = aws_client_manager.get_client(AWSServiceType.ATHENA)
        
        response = athena_client.get_query_execution(
            QueryExecutionId=query_execution_id
        )
        
        status = response['QueryExecution']['Status']['State']
        
        return {
            "query_execution_id": query_execution_id,
            "status": status,
            "submission_time": response['QueryExecution']['Status'].get('SubmissionDateTime'),
            "completion_time": response['QueryExecution']['Status'].get('CompletionDateTime')
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get query status: {str(e)}")
