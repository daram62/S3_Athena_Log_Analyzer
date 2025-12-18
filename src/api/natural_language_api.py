"""자연어 쿼리 API - 자연어를 SQL로 변환하고 실행"""

from fastapi import APIRouter, HTTPException
from typing import List, Optional
import uuid
import logging
from datetime import datetime, timedelta

from ..models.query_history import (
    NaturalLanguageQueryRequest,
    NaturalLanguageQueryResponse,
    QueryHistoryEntry,
    QueryHistoryList,
    QueryStatistics,
    QueryStatus,
    QueryType,
    SuggestedQuestion
)
from ..services.bedrock_service import BedrockService
from ..services.athena_manager import AthenaManager
from ..services.aws_clients import AWSClients

router = APIRouter(prefix="/api/v1/natural-language", tags=["natural-language"])
logger = logging.getLogger(__name__)

# 인메모리 쿼리 히스토리 (실제로는 DB 사용)
query_history_store: List[QueryHistoryEntry] = []


@router.post("/query", response_model=NaturalLanguageQueryResponse)
async def natural_language_query(request: NaturalLanguageQueryRequest):
    """
    자연어 질문을 SQL로 변환하고 선택적으로 실행
    
    - 자연어 질문을 Bedrock Claude를 사용하여 SQL로 변환
    - execute_immediately=True인 경우 Athena에서 즉시 실행
    - 쿼리 히스토리에 저장
    """
    try:
        # 1. 쿼리 ID 생성
        query_id = str(uuid.uuid4())
        
        # 2. Bedrock으로 자연어 → SQL 변환
        logger.info(f"자연어 쿼리 변환 시작: {request.question}")
        bedrock_service = BedrockService()
        
        conversion_result = bedrock_service.natural_language_to_sql(
            question=request.question,
            database_name=request.database_name,
            table_name=request.table_name,
            log_type=request.log_type
        )
        
        sql_query = conversion_result.get("sql", "")
        if not sql_query:
            raise HTTPException(
                status_code=400,
                detail="SQL 생성에 실패했습니다. 질문을 다시 작성해주세요."
            )
        
        # 3. 쿼리 히스토리 항목 생성
        history_entry = QueryHistoryEntry(
            id=query_id,
            query_type=QueryType.NATURAL_LANGUAGE,
            natural_language_question=request.question,
            sql_query=sql_query,
            database_name=request.database_name,
            table_name=request.table_name,
            log_type=request.log_type,
            status=QueryStatus.PENDING,
            ai_confidence=conversion_result.get("confidence", 0.8),
            ai_explanation=conversion_result.get("explanation", ""),
            ai_assumptions=conversion_result.get("assumptions", []),
            ai_suggestions=conversion_result.get("suggestions", []),
            created_at=datetime.utcnow()
        )
        
        # 4. 즉시 실행 여부 확인
        execution_status = None
        athena_query_execution_id = None
        results = None
        row_count = None
        execution_time_ms = None
        
        if request.execute_immediately:
            try:
                logger.info(f"Athena 쿼리 실행 시작: {query_id}")
                athena_manager = AthenaManager()
                
                # 쿼리 실행 (execute_query가 완료까지 대기함)
                start_time = datetime.utcnow()
                history_entry.status = QueryStatus.RUNNING
                history_entry.started_at = start_time
                
                execution_result = athena_manager.execute_query(sql_query, timeout=60)
                athena_query_execution_id = execution_result.get("query_execution_id")
                query_status = execution_result.get("status")
                
                if execution_result.get("success") and query_status == "SUCCEEDED":
                    # 결과 가져오기
                    results_response = athena_manager.get_query_results(athena_query_execution_id)
                    
                    if results_response.get("success"):
                        results = results_response.get("data", [])
                        row_count = results_response.get("row_count", 0)
                    else:
                        results = []
                        row_count = 0
                    
                    # 실행 시간 계산
                    end_time = datetime.utcnow()
                    execution_time_ms = int((end_time - start_time).total_seconds() * 1000)
                    
                    # 히스토리 업데이트
                    history_entry.status = QueryStatus.SUCCEEDED
                    history_entry.athena_query_execution_id = athena_query_execution_id
                    history_entry.row_count = row_count
                    history_entry.execution_time_ms = execution_time_ms
                    history_entry.completed_at = end_time
                    
                    execution_status = QueryStatus.SUCCEEDED
                    
                    logger.info(f"쿼리 실행 성공: {query_id}, 행 수: {row_count}")
                    
                elif query_status in ["FAILED", "ERROR"]:
                    error_message = execution_result.get("error", "알 수 없는 오류")
                    
                    history_entry.status = QueryStatus.FAILED
                    history_entry.error_message = error_message
                    history_entry.completed_at = datetime.utcnow()
                    
                    execution_status = QueryStatus.FAILED
                    
                    logger.error(f"쿼리 실행 실패: {query_id}, 오류: {error_message}")
                    
                else:
                    # CANCELLED, TIMEOUT 또는 기타 상태
                    error_message = execution_result.get("error", f"쿼리 상태: {query_status}")
                    history_entry.status = QueryStatus.CANCELLED
                    history_entry.error_message = error_message
                    history_entry.completed_at = datetime.utcnow()
                    execution_status = QueryStatus.CANCELLED
                    
            except Exception as e:
                logger.error(f"쿼리 실행 중 오류: {e}", exc_info=True)
                history_entry.status = QueryStatus.FAILED
                history_entry.error_message = str(e)
                history_entry.completed_at = datetime.utcnow()
                execution_status = QueryStatus.FAILED
        
        # 5. 히스토리에 저장
        query_history_store.append(history_entry)
        
        # 6. 응답 생성
        response = NaturalLanguageQueryResponse(
            query_id=query_id,
            sql_query=sql_query,
            explanation=conversion_result.get("explanation", ""),
            confidence=conversion_result.get("confidence", 0.8),
            assumptions=conversion_result.get("assumptions", []),
            suggestions=conversion_result.get("suggestions", []),
            execution_status=execution_status.value if execution_status else None,  # enum을 문자열로 변환
            athena_query_execution_id=athena_query_execution_id,
            results=results,
            row_count=row_count,
            execution_time_ms=execution_time_ms
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"자연어 쿼리 처리 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"자연어 쿼리 처리 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/suggestions/{log_type}", response_model=List[SuggestedQuestion])
async def get_suggested_questions(log_type: str = "s3_access"):
    """
    로그 타입별 추천 질문 목록
    
    - 자주 사용되는 분석 질문 제공
    - 로그 타입에 맞는 질문 추천
    """
    try:
        bedrock_service = BedrockService()
        questions = bedrock_service.get_suggested_questions(log_type)
        
        # 카테고리 매핑
        category_map = {
            "가장": "트래픽 분석",
            "에러": "에러 분석",
            "IP": "보안 분석",
            "시간": "성능 분석",
            "캐시": "성능 분석",
            "타겟": "성능 분석",
            "API": "활동 분석",
            "사용자": "활동 분석",
            "권한": "보안 분석",
            "루트": "보안 분석"
        }
        
        suggested_questions = []
        for question in questions:
            # 카테고리 자동 분류
            category = "일반 분석"
            for keyword, cat in category_map.items():
                if keyword in question:
                    category = cat
                    break
            
            suggested_questions.append(
                SuggestedQuestion(
                    question=question,
                    category=category,
                    description=f"{log_type} 로그 분석을 위한 추천 질문"
                )
            )
        
        return suggested_questions
        
    except Exception as e:
        logger.error(f"추천 질문 조회 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"추천 질문 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/history", response_model=QueryHistoryList)
async def get_query_history(
    page: int = 1,
    page_size: int = 20,
    query_type: Optional[QueryType] = None,
    status: Optional[QueryStatus] = None,
    log_type: Optional[str] = None
):
    """
    쿼리 히스토리 조회
    
    - 페이지네이션 지원
    - 쿼리 타입, 상태, 로그 타입으로 필터링 가능
    """
    try:
        # 필터링
        filtered_history = query_history_store.copy()
        
        if query_type:
            filtered_history = [h for h in filtered_history if h.query_type == query_type]
        
        if status:
            filtered_history = [h for h in filtered_history if h.status == status]
        
        if log_type:
            filtered_history = [h for h in filtered_history if h.log_type == log_type]
        
        # 최신순 정렬
        filtered_history.sort(key=lambda x: x.created_at, reverse=True)
        
        # 페이지네이션
        total = len(filtered_history)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        items = filtered_history[start_idx:end_idx]
        
        return QueryHistoryList(
            total=total,
            items=items,
            page=page,
            page_size=page_size
        )
        
    except Exception as e:
        logger.error(f"쿼리 히스토리 조회 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"쿼리 히스토리 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/history/{query_id}", response_model=QueryHistoryEntry)
async def get_query_detail(query_id: str):
    """특정 쿼리의 상세 정보 조회"""
    try:
        # 쿼리 찾기
        query = next((q for q in query_history_store if q.id == query_id), None)
        
        if not query:
            raise HTTPException(
                status_code=404,
                detail=f"쿼리를 찾을 수 없습니다: {query_id}"
            )
        
        return query
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"쿼리 상세 조회 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"쿼리 상세 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/statistics", response_model=QueryStatistics)
async def get_query_statistics(days: int = 7):
    """
    쿼리 통계 조회
    
    - 최근 N일간의 쿼리 통계
    - 성공/실패율, 평균 실행 시간 등
    """
    try:
        # 기간 필터링
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        recent_queries = [q for q in query_history_store if q.created_at >= cutoff_date]
        
        if not recent_queries:
            return QueryStatistics(
                total_queries=0,
                successful_queries=0,
                failed_queries=0,
                avg_execution_time_ms=0.0,
                total_data_scanned_gb=0.0
            )
        
        # 통계 계산
        total_queries = len(recent_queries)
        successful_queries = len([q for q in recent_queries if q.status == QueryStatus.SUCCEEDED])
        failed_queries = len([q for q in recent_queries if q.status == QueryStatus.FAILED])
        
        # 평균 실행 시간
        execution_times = [q.execution_time_ms for q in recent_queries if q.execution_time_ms]
        avg_execution_time_ms = sum(execution_times) / len(execution_times) if execution_times else 0.0
        
        # 총 스캔 데이터
        data_scanned = [q.data_scanned_bytes for q in recent_queries if q.data_scanned_bytes]
        total_data_scanned_gb = sum(data_scanned) / (1024 ** 3) if data_scanned else 0.0
        
        # 쿼리 타입별 통계
        natural_language_count = len([q for q in recent_queries if q.query_type == QueryType.NATURAL_LANGUAGE])
        template_count = len([q for q in recent_queries if q.query_type == QueryType.TEMPLATE])
        custom_count = len([q for q in recent_queries if q.query_type == QueryType.CUSTOM])
        
        # 로그 타입별 통계
        queries_by_log_type = {}
        for query in recent_queries:
            if query.log_type:
                queries_by_log_type[query.log_type] = queries_by_log_type.get(query.log_type, 0) + 1
        
        return QueryStatistics(
            total_queries=total_queries,
            successful_queries=successful_queries,
            failed_queries=failed_queries,
            avg_execution_time_ms=avg_execution_time_ms,
            total_data_scanned_gb=total_data_scanned_gb,
            natural_language_count=natural_language_count,
            template_count=template_count,
            custom_count=custom_count,
            queries_by_log_type=queries_by_log_type
        )
        
    except Exception as e:
        logger.error(f"쿼리 통계 조회 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"쿼리 통계 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.delete("/history/{query_id}")
async def delete_query_history(query_id: str):
    """쿼리 히스토리 삭제"""
    try:
        global query_history_store
        
        # 쿼리 찾기
        query = next((q for q in query_history_store if q.id == query_id), None)
        
        if not query:
            raise HTTPException(
                status_code=404,
                detail=f"쿼리를 찾을 수 없습니다: {query_id}"
            )
        
        # 삭제
        query_history_store = [q for q in query_history_store if q.id != query_id]
        
        return {
            "success": True,
            "message": f"쿼리 히스토리가 삭제되었습니다: {query_id}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"쿼리 히스토리 삭제 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"쿼리 히스토리 삭제 중 오류가 발생했습니다: {str(e)}"
        )
