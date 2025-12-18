"""AWS Bedrock 서비스 - 자연어를 SQL로 변환"""

import json
import logging
from typing import Dict, List, Optional
from datetime import datetime

from ..config import settings
from .aws_clients import AWSClients
from ..models.log_schema import schema_registry

logger = logging.getLogger(__name__)


class BedrockService:
    """Bedrock을 사용한 자연어 → SQL 변환 서비스"""
    
    def __init__(self, aws_clients: Optional[AWSClients] = None):
        self.aws_clients = aws_clients or AWSClients()
        self.bedrock_client = self.aws_clients.get_bedrock_runtime_client()
        self.model_id = settings.aws.bedrock_model_id
        self.max_tokens = settings.aws.bedrock_max_tokens
        
        # 로그 타입별 스키마 매핑 (schema_registry 사용)
        self.schema_registry = schema_registry
    
    def natural_language_to_sql(
        self,
        question: str,
        database_name: str,
        table_name: str,
        log_type: str = "s3_access"
    ) -> Dict:
        """
        자연어 질문을 SQL 쿼리로 변환
        
        Args:
            question: 자연어 질문
            database_name: 데이터베이스 이름
            table_name: 테이블 이름
            log_type: 로그 타입
            
        Returns:
            변환 결과 (SQL, 설명, 신뢰도 등)
        """
        try:
            # 스키마 정보 가져오기
            from ..models.log_schema import LogType
            
            # log_type을 LogType enum으로 변환
            if isinstance(log_type, str):
                # 문자열을 LogType enum으로 변환
                log_type_map = {
                    "s3_access": LogType.S3_ACCESS,
                    "cloudfront": LogType.CLOUDFRONT,
                    "alb": LogType.ALB,
                    "vpc_flow": LogType.VPC_FLOW
                }
                log_type_enum = log_type_map.get(log_type, LogType.S3_ACCESS)
            else:
                log_type_enum = log_type
            
            schema = self.schema_registry.get_schema(log_type_enum)
            
            if not schema:
                raise ValueError(f"스키마를 찾을 수 없습니다: {log_type}")
            
            # 프롬프트 생성
            prompt = self._build_prompt(
                question=question,
                database_name=database_name,
                table_name=table_name,
                schema=schema,
                log_type=log_type
            )
            
            # Bedrock 호출
            response = self._invoke_bedrock(prompt)
            
            # 응답 파싱
            result = self._parse_response(response)
            
            # 메타데이터 추가
            result["metadata"] = {
                "question": question,
                "database": database_name,
                "table": table_name,
                "log_type": log_type,
                "timestamp": datetime.utcnow().isoformat(),
                "model_id": self.model_id
            }
            
            return result
            
        except Exception as e:
            logger.error(f"자연어 → SQL 변환 실패: {e}")
            raise
    
    def _build_prompt(
        self,
        question: str,
        database_name: str,
        table_name: str,
        schema: Dict,
        log_type: str
    ) -> str:
        """SQL 생성을 위한 프롬프트 구성"""
        
        # 스키마 정보를 문자열로 변환
        schema_info = self._format_schema(schema)
        
        # 로그 타입별 예시 쿼리
        examples = self._get_example_queries(log_type)
        
        prompt = f"""당신은 AWS 로그 분석 전문가입니다. 사용자의 자연어 질문을 Athena SQL 쿼리로 변환해주세요.

## 데이터베이스 정보
- 데이터베이스: {database_name}
- 테이블: {table_name}
- 로그 타입: {log_type}

## 테이블 스키마
{schema_info}

## 예시 쿼리
{examples}

## 사용자 질문
"{question}"

## 응답 형식 (JSON)
다음 JSON 형식으로 응답해주세요:
{{
  "sql": "생성된 SQL 쿼리",
  "explanation": "쿼리에 대한 한글 설명",
  "confidence": 0.95,
  "assumptions": ["가정한 사항들"],
  "suggestions": ["추가 분석 제안"]
}}

## 중요 규칙
1. 테이블 이름은 반드시 {database_name}.{table_name} 형식 사용
2. 성능을 위해 LIMIT 절 추가 (기본 100)
3. 문자열 비교 시 LIKE 또는 정확한 매칭 사용
4. 집계 함수 사용 시 적절한 GROUP BY 추가
5. 응답은 반드시 유효한 JSON 형식
6. SQL은 Athena Presto 문법 준수
7. 필드명은 위 스키마에 정의된 이름을 정확히 사용 (예: httpstatus, remoteip, bytessent)

응답:"""
        
        return prompt
    
    def _format_schema(self, schema) -> str:
        """스키마를 읽기 쉬운 형식으로 변환"""
        lines = []
        
        # LogSchema 객체인 경우
        if hasattr(schema, 'fields'):
            for field in schema.fields:
                field_info = f"- {field.name} ({field.type.value})"
                if field.description:
                    field_info += f": {field.description}"
                lines.append(field_info)
            
            # 파티션 정보 추가
            if hasattr(schema, 'partition_fields') and schema.partition_fields:
                lines.append("\n## 파티션 컬럼")
                for partition in schema.partition_fields:
                    lines.append(f"- {partition} (string)")
        
        return "\n".join(lines)
    
    def _get_example_queries(self, log_type: str) -> str:
        """로그 타입별 예시 쿼리 (AWS 공식 문서 필드명 기준)"""
        
        examples = {
            "s3_access": """
1. 가장 많이 접근된 파일:
   SELECT key, COUNT(*) as count FROM {db}.{table} GROUP BY key ORDER BY count DESC LIMIT 10;

2. 에러 분석:
   SELECT httpstatus, COUNT(*) FROM {db}.{table} WHERE httpstatus >= '400' GROUP BY httpstatus;

3. IP별 요청 수:
   SELECT remoteip, COUNT(*) FROM {db}.{table} GROUP BY remoteip ORDER BY COUNT(*) DESC LIMIT 20;

4. 전체 데이터 미리보기:
   SELECT * FROM {db}.{table} LIMIT 10;
""",
            "cloudfront": """
## CloudFront 테이블 - 주요 컬럼:
date, time, x_edge_location, sc_bytes, c_ip, cs_method, cs_host, cs_uri_stem,
sc_status, cs_referer, cs_user_agent, cs_uri_query, cs_cookie, x_edge_result_type,
x_edge_request_id, x_host_header, cs_protocol, cs_bytes, time_taken, x_forwarded_for,
ssl_protocol, ssl_cipher, x_edge_response_result_type, cs_protocol_version

## 중요: 컬럼명이 확실하지 않으면 SELECT * 사용

1. 전체 데이터 미리보기:
   SELECT * FROM {db}.{table} LIMIT 10;

2. 상태 코드별 분포:
   SELECT sc_status, COUNT(*) as cnt FROM {db}.{table} GROUP BY sc_status ORDER BY cnt DESC;

3. 엣지 로케이션별 트래픽:
   SELECT x_edge_location, COUNT(*) as cnt FROM {db}.{table} GROUP BY x_edge_location ORDER BY cnt DESC LIMIT 20;

4. 캐시 히트율:
   SELECT x_edge_result_type, COUNT(*) as cnt FROM {db}.{table} GROUP BY x_edge_result_type ORDER BY cnt DESC;

5. 에러 분석:
   SELECT * FROM {db}.{table} WHERE sc_status >= 400 ORDER BY date DESC, time DESC LIMIT 100;
""",
            "alb": """
## ALB 테이블 - 주요 컬럼:
type, time, elb, client_ip, client_port, request_processing_time, 
target_processing_time, response_processing_time, elb_status_code, 
target_status_code, received_bytes, sent_bytes, request_verb, request_url, 
request_proto, user_agent, ssl_cipher, ssl_protocol, target_group_arn, 
trace_id, domain_name, actions_executed, error_reason

## 중요: 컬럼명이 확실하지 않으면 SELECT * 사용

1. 전체 데이터 미리보기:
   SELECT * FROM {db}.{table} LIMIT 10;

2. 에러 분석 (elb_status_code 사용):
   SELECT elb_status_code, COUNT(*) as cnt FROM {db}.{table} WHERE elb_status_code >= 400 GROUP BY elb_status_code ORDER BY cnt DESC;

3. 요청 메서드별 통계:
   SELECT request_verb, COUNT(*) as cnt FROM {db}.{table} GROUP BY request_verb ORDER BY cnt DESC;

4. 시간대별 요청 수:
   SELECT SUBSTR(time, 1, 13) as hour, COUNT(*) as cnt FROM {db}.{table} GROUP BY SUBSTR(time, 1, 13) ORDER BY hour DESC LIMIT 24;

5. 5xx 에러 요청:
   SELECT * FROM {db}.{table} WHERE elb_status_code >= 500 ORDER BY time DESC LIMIT 100;
""",
            "vpc_flow": """
## VPC Flow Logs 테이블 - 주요 컬럼:
version, account_id, interface_id, srcaddr, dstaddr, srcport, dstport, 
protocol, packets, bytes, start, end, action, log_status

## 중요: 컬럼명이 확실하지 않으면 SELECT * 사용

1. 전체 데이터 미리보기:
   SELECT * FROM {db}.{table} LIMIT 10;

2. 가장 많은 트래픽 IP:
   SELECT srcaddr, dstaddr, SUM(bytes) as total_bytes FROM {db}.{table} GROUP BY srcaddr, dstaddr ORDER BY total_bytes DESC LIMIT 20;

3. 거부된 연결:
   SELECT srcaddr, dstaddr, dstport, COUNT(*) as cnt FROM {db}.{table} WHERE action = 'REJECT' GROUP BY srcaddr, dstaddr, dstport ORDER BY cnt DESC LIMIT 20;

4. 포트별 트래픽:
   SELECT dstport, COUNT(*) as cnt, SUM(bytes) as total_bytes FROM {db}.{table} GROUP BY dstport ORDER BY cnt DESC LIMIT 20;
""",

        }
        
        return examples.get(log_type, examples["s3_access"])
    
    def _invoke_bedrock(self, prompt: str) -> str:
        """Bedrock API 호출"""
        try:
            # Claude 모델용 요청 본문 (temperature와 top_p 중 하나만 사용)
            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": self.max_tokens,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.1  # 낮은 온도로 일관된 결과
            }
            
            # Bedrock 호출
            response = self.bedrock_client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(request_body)
            )
            
            # 응답 파싱
            response_body = json.loads(response['body'].read())
            
            # Claude 응답에서 텍스트 추출
            if 'content' in response_body and len(response_body['content']) > 0:
                return response_body['content'][0]['text']
            else:
                raise ValueError("Bedrock 응답에 content가 없습니다")
                
        except Exception as e:
            logger.error(f"Bedrock 호출 실패: {e}")
            raise
    
    def _parse_response(self, response_text: str) -> Dict:
        """Bedrock 응답을 파싱"""
        try:
            # JSON 부분만 추출 (마크다운 코드 블록 제거)
            json_text = response_text
            if "```json" in response_text:
                json_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                json_text = response_text.split("```")[1].split("```")[0].strip()
            
            # JSON 파싱
            result = json.loads(json_text)
            
            # 필수 필드 검증
            if "sql" not in result:
                raise ValueError("응답에 SQL이 없습니다")
            
            # 기본값 설정
            result.setdefault("explanation", "SQL 쿼리가 생성되었습니다.")
            result.setdefault("confidence", 0.8)
            result.setdefault("assumptions", [])
            result.setdefault("suggestions", [])
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON 파싱 실패: {e}\n응답: {response_text}")
            # 파싱 실패 시 기본 응답
            return {
                "sql": "",
                "explanation": "SQL 생성에 실패했습니다. 질문을 다시 작성해주세요.",
                "confidence": 0.0,
                "error": str(e),
                "raw_response": response_text
            }
    
    def get_suggested_questions(self, log_type: str = "s3_access") -> List[str]:
        """로그 타입별 추천 질문 목록"""
        
        suggestions = {
            "s3_access": [
                "지난 7일간 가장 많이 접근된 파일 10개는?",
                "어제 발생한 4xx, 5xx 에러는 몇 건인가요?",
                "IP별 요청 횟수를 많은 순으로 보여주세요",
                "시간대별 트래픽 패턴을 분석해주세요",
                "가장 많은 데이터를 전송한 파일은?",
                "특정 IP(1.2.3.4)의 접근 기록을 보여주세요",
                "오늘 403 에러가 발생한 파일 목록은?",
                "User Agent별 요청 분포를 보여주세요"
            ],
            "cloudfront": [
                "엣지 로케이션별 트래픽 분포는?",
                "캐시 히트율은 얼마인가요?",
                "가장 느린 응답 시간을 가진 요청은?",
                "4xx, 5xx 에러 분석해주세요",
                "국가별 요청 수를 보여주세요",
                "가장 많이 요청된 콘텐츠는?",
                "SSL/TLS 버전별 분포는?",
                "모바일 vs 데스크톱 트래픽 비율은?"
            ],
            "alb": [
                "타겟별 평균 응답 시간은?",
                "가장 많은 에러를 발생시킨 타겟은?",
                "요청 경로별 트래픽 분포는?",
                "5xx 에러가 발생한 요청들을 보여주세요",
                "가장 느린 응답 시간을 가진 요청은?",
                "클라이언트 IP별 요청 수는?",
                "HTTP vs HTTPS 트래픽 비율은?",
                "User Agent별 요청 분포는?"
            ],
            "vpc_flow": [
                "가장 많은 트래픽을 발생시킨 IP는?",
                "거부된(REJECT) 연결 시도는 몇 건인가요?",
                "포트별 트래픽 분포를 보여주세요",
                "특정 IP로의 연결 시도를 분석해주세요",
                "시간대별 네트워크 트래픽 패턴은?",
                "가장 많이 사용된 프로토콜은?",
                "외부에서 들어오는 트래픽 Top 10은?",
                "내부 통신 패턴을 분석해주세요"
            ],

        }
        
        return suggestions.get(log_type, suggestions["s3_access"])
