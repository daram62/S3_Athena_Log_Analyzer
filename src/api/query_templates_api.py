"""쿼리 템플릿 API - 자주 사용하는 쿼리 제공"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(prefix="/api/v1/query-templates", tags=["query-templates"])


class QueryTemplate(BaseModel):
    """쿼리 템플릿"""
    id: str
    category: str
    name: str
    description: str
    sql_template: str
    parameters: List[str] = []
    use_cases: List[str] = []


# S3 Access Log 쿼리 템플릿 (AWS 공식 문서 필드명 기준)
S3_ACCESS_LOG_TEMPLATES = [
    QueryTemplate(
        id="top-accessed-files",
        category="트래픽 분석",
        name="가장 많이 접근된 파일 Top 10",
        description="특정 기간 동안 가장 많이 요청된 파일과 전송량 분석",
        sql_template="""SELECT 
  key AS file_path,
  COUNT(*) AS request_count,
  SUM(bytessent) / 1024 / 1024 AS total_mb_sent
FROM {database}.{table}
WHERE timestamp >= '{start_date}'
  AND timestamp < '{end_date}'
  AND httpstatus LIKE '2%'
GROUP BY key
ORDER BY request_count DESC
LIMIT 10;""",
        parameters=["database", "table", "start_date", "end_date"],
        use_cases=["인기 콘텐츠 파악", "캐싱 전략 수립", "CDN 최적화"]
    ),
    
    QueryTemplate(
        id="traffic-by-ip",
        category="트래픽 분석",
        name="IP별 요청 횟수",
        description="IP별 요청 수, 전송량, 접근 파일 수 분석",
        sql_template="""SELECT 
  remoteip,
  COUNT(*) AS request_count,
  SUM(bytessent) / 1024 / 1024 / 1024 AS total_gb_sent,
  COUNT(DISTINCT key) AS unique_files_accessed
FROM {database}.{table}
WHERE timestamp >= '{start_date}'
  AND timestamp < '{end_date}'
GROUP BY remoteip
ORDER BY request_count DESC
LIMIT 20;""",
        parameters=["database", "table", "start_date", "end_date"],
        use_cases=["비정상 트래픽 감지", "DDoS 공격 의심", "특정 IP 과도한 요청 확인"]
    ),
    
    QueryTemplate(
        id="error-analysis",
        category="에러 분석",
        name="에러 분석 (4xx, 5xx)",
        description="HTTP 에러 상태 코드별 발생 횟수와 실패한 파일 분석",
        sql_template="""SELECT 
  httpstatus,
  errorcode,
  COUNT(*) AS error_count,
  key AS failed_file
FROM {database}.{table}
WHERE timestamp >= '{start_date}'
  AND timestamp < '{end_date}'
  AND (httpstatus LIKE '4%' OR httpstatus LIKE '5%')
GROUP BY httpstatus, errorcode, key
ORDER BY error_count DESC
LIMIT 20;""",
        parameters=["database", "table", "start_date", "end_date"],
        use_cases=["에러 원인 파악", "404 에러 수정", "권한 문제 해결"]
    ),
    
    QueryTemplate(
        id="hourly-pattern",
        category="성능 분석",
        name="시간대별 요청 패턴",
        description="시간별 요청 수와 전송량 추이 분석",
        sql_template="""SELECT 
  SUBSTR(requestdatetime, 1, 14) AS hour,
  COUNT(*) AS request_count,
  SUM(bytessent) / 1024 / 1024 AS mb_transferred
FROM {database}.{table}
WHERE timestamp >= '{start_date}'
  AND timestamp < '{end_date}'
GROUP BY SUBSTR(requestdatetime, 1, 14)
ORDER BY hour;""",
        parameters=["database", "table", "start_date", "end_date"],
        use_cases=["피크 시간대 파악", "캐싱 전략 수립", "인프라 스케일링 계획"]
    ),
    
    QueryTemplate(
        id="access-denied",
        category="보안",
        name="권한 거부 (403) 분석",
        description="403 에러 발생 패턴 및 의심스러운 접근 시도 탐지",
        sql_template="""SELECT 
  SUBSTR(requestdatetime, 1, 14) AS hour,
  remoteip,
  key,
  COUNT(*) AS denied_attempts
FROM {database}.{table}
WHERE httpstatus = '403'
  AND timestamp >= '{start_date}'
  AND timestamp < '{end_date}'
GROUP BY SUBSTR(requestdatetime, 1, 14), remoteip, key
HAVING COUNT(*) > 10
ORDER BY denied_attempts DESC;""",
        parameters=["database", "table", "start_date", "end_date"],
        use_cases=["보안 위협 탐지", "권한 설정 검토", "무단 접근 시도 추적"]
    ),
    
    QueryTemplate(
        id="cost-estimation",
        category="비용 분석",
        name="데이터 전송 비용 추정",
        description="일별 데이터 전송량 및 예상 비용 계산",
        sql_template="""SELECT 
  timestamp AS date,
  SUM(bytessent) / 1024 / 1024 / 1024 AS total_gb_out,
  SUM(bytessent) / 1024 / 1024 / 1024 * 0.09 AS estimated_cost_usd
FROM {database}.{table}
WHERE timestamp >= '{start_date}'
  AND timestamp < '{end_date}'
  AND httpstatus LIKE '2%'
GROUP BY timestamp
ORDER BY date;""",
        parameters=["database", "table", "start_date", "end_date"],
        use_cases=["비용 예측", "예산 계획", "비용 최적화"]
    ),
]


# VPC Flow Log 쿼리 템플릿 (AWS 공식 문서 필드명 기준)
VPC_FLOW_LOG_TEMPLATES = [
    QueryTemplate(
        id="top-talkers",
        category="네트워크 분석",
        name="가장 많은 트래픽을 발생시킨 IP Top 20",
        description="송신/수신 IP별 트래픽량 및 연결 수 분석",
        sql_template="""SELECT 
  srcaddr AS source_ip,
  dstaddr AS destination_ip,
  COUNT(*) AS connection_count,
  SUM(bytes) / 1024 / 1024 AS total_mb,
  SUM(packets) AS total_packets
FROM {database}.{table}
WHERE "date" = DATE '{query_date}'
GROUP BY srcaddr, dstaddr
ORDER BY SUM(bytes) DESC
LIMIT 20;""",
        parameters=["database", "table", "query_date"],
        use_cases=["대량 트래픽 발생 원인 파악", "네트워크 병목 분석", "비정상 트래픽 탐지"]
    ),
    
    QueryTemplate(
        id="rejected-connections",
        category="보안",
        name="거부된 연결 시도 (REJECT)",
        description="방화벽에 의해 차단된 연결 시도 분석",
        sql_template="""SELECT 
  srcaddr,
  dstaddr,
  dstport,
  protocol,
  COUNT(*) AS reject_count
FROM {database}.{table}
WHERE action = 'REJECT'
  AND "date" = DATE '{query_date}'
GROUP BY srcaddr, dstaddr, dstport, protocol
ORDER BY reject_count DESC
LIMIT 50;""",
        parameters=["database", "table", "query_date"],
        use_cases=["보안 위협 탐지", "방화벽 규칙 검증", "공격 시도 분석"]
    ),
    
    QueryTemplate(
        id="port-scan-detection",
        category="보안",
        name="포트 스캔 탐지",
        description="단일 IP에서 여러 포트로 접근 시도하는 의심스러운 활동",
        sql_template="""SELECT 
  srcaddr,
  COUNT(DISTINCT dstport) AS unique_ports_accessed,
  COUNT(*) AS total_attempts
FROM {database}.{table}
WHERE "date" = DATE '{query_date}'
GROUP BY srcaddr
HAVING COUNT(DISTINCT dstport) > 10
ORDER BY unique_ports_accessed DESC;""",
        parameters=["database", "table", "query_date"],
        use_cases=["포트 스캔 공격 탐지", "보안 위협 식별", "침입 시도 추적"]
    ),
    
    QueryTemplate(
        id="protocol-distribution",
        category="네트워크 분석",
        name="프로토콜별 트래픽 분포",
        description="TCP, UDP, ICMP 등 프로토콜별 사용량 분석",
        sql_template="""SELECT 
  CASE protocol
    WHEN 6 THEN 'TCP'
    WHEN 17 THEN 'UDP'
    WHEN 1 THEN 'ICMP'
    ELSE CAST(protocol AS VARCHAR)
  END AS protocol_name,
  COUNT(*) AS flow_count,
  SUM(bytes) / 1024 / 1024 / 1024 AS total_gb,
  SUM(packets) AS total_packets
FROM {database}.{table}
WHERE "date" = DATE '{query_date}'
GROUP BY protocol
ORDER BY SUM(bytes) DESC;""",
        parameters=["database", "table", "query_date"],
        use_cases=["네트워크 프로토콜 분석", "트래픽 패턴 이해", "최적화 전략 수립"]
    ),
    
    QueryTemplate(
        id="top-destination-ports",
        category="네트워크 분석",
        name="가장 많이 사용된 목적지 포트",
        description="서비스별 트래픽 분석 (HTTP, HTTPS, SSH 등)",
        sql_template="""SELECT 
  dstport,
  CASE dstport
    WHEN 80 THEN 'HTTP'
    WHEN 443 THEN 'HTTPS'
    WHEN 22 THEN 'SSH'
    WHEN 3306 THEN 'MySQL'
    WHEN 5432 THEN 'PostgreSQL'
    WHEN 6379 THEN 'Redis'
    ELSE 'Other'
  END AS service_name,
  COUNT(*) AS connection_count,
  SUM(bytes) / 1024 / 1024 AS total_mb
FROM {database}.{table}
WHERE "date" = DATE '{query_date}'
GROUP BY dstport
ORDER BY connection_count DESC
LIMIT 20;""",
        parameters=["database", "table", "query_date"],
        use_cases=["서비스별 트래픽 분석", "포트 사용 현황", "보안 그룹 최적화"]
    ),
    
    QueryTemplate(
        id="data-transfer-by-interface",
        category="네트워크 분석",
        name="네트워크 인터페이스별 데이터 전송량",
        description="ENI별 트래픽 분석",
        sql_template="""SELECT 
  interface_id,
  COUNT(*) AS flow_count,
  SUM(bytes) / 1024 / 1024 / 1024 AS total_gb_transferred,
  SUM(packets) AS total_packets
FROM {database}.{table}
WHERE "date" = DATE '{query_date}'
GROUP BY interface_id
ORDER BY SUM(bytes) DESC;""",
        parameters=["database", "table", "query_date"],
        use_cases=["인스턴스별 트래픽 분석", "네트워크 비용 추적", "리소스 사용량 모니터링"]
    ),
]


# CloudFront 쿼리 템플릿 (AWS 공식 문서 필드명 기준)
CLOUDFRONT_LOG_TEMPLATES = [
    QueryTemplate(
        id="cache-hit-ratio",
        category="캐시 성능",
        name="캐시 히트율 분석",
        description="Hit, Miss, RefreshHit 등 캐시 상태별 비율 분석",
        sql_template="""SELECT 
  x_edge_result_type,
  COUNT(*) AS request_count,
  COUNT(*) * 100.0 / SUM(COUNT(*)) OVER() AS percentage,
  SUM(sc_bytes) / 1024 / 1024 / 1024 AS total_gb
FROM {database}.{table}
WHERE "date" >= DATE '{start_date}' AND "date" < DATE '{end_date}'
GROUP BY x_edge_result_type
ORDER BY request_count DESC;""",
        parameters=["database", "table", "start_date", "end_date"],
        use_cases=["캐시 효율성 평가", "오리진 부하 분석", "CDN 최적화"]
    ),
    
    QueryTemplate(
        id="geographic-distribution",
        category="지리적 분석",
        name="엣지 로케이션별 트래픽 분포",
        description="엣지 로케이션별 요청 수 및 데이터 전송량",
        sql_template="""SELECT 
  x_edge_location,
  COUNT(*) AS request_count,
  SUM(sc_bytes) / 1024 / 1024 / 1024 AS total_gb,
  AVG(time_taken) AS avg_response_time
FROM {database}.{table}
WHERE "date" >= DATE '{start_date}' AND "date" < DATE '{end_date}'
GROUP BY x_edge_location
ORDER BY request_count DESC
LIMIT 30;""",
        parameters=["database", "table", "start_date", "end_date"],
        use_cases=["글로벌 사용자 분포 파악", "지역별 성능 분석", "엣지 로케이션 최적화"]
    ),
    
    QueryTemplate(
        id="slow-requests",
        category="성능 분석",
        name="느린 요청 분석 (1초 이상)",
        description="응답 시간이 긴 요청 찾기 및 원인 분석",
        sql_template="""SELECT 
  cs_uri_stem,
  c_ip AS client_ip,
  time_taken,
  x_edge_result_type,
  sc_status,
  sc_bytes,
  x_edge_location
FROM {database}.{table}
WHERE time_taken > 1.0
  AND "date" >= DATE '{start_date}' AND "date" < DATE '{end_date}'
ORDER BY time_taken DESC
LIMIT 100;""",
        parameters=["database", "table", "start_date", "end_date"],
        use_cases=["성능 병목 파악", "사용자 경험 개선", "오리진 최적화"]
    ),
    
    QueryTemplate(
        id="error-rate",
        category="에러 분석",
        name="4xx/5xx 에러율 분석",
        description="시간대별 에러 발생 추이 및 상태 코드 분포",
        sql_template="""SELECT 
  "date",
  time,
  sc_status,
  COUNT(*) AS error_count,
  cs_uri_stem
FROM {database}.{table}
WHERE (sc_status >= 400 AND sc_status < 600)
  AND "date" >= DATE '{start_date}' AND "date" < DATE '{end_date}'
GROUP BY "date", time, sc_status, cs_uri_stem
ORDER BY "date" DESC, error_count DESC
LIMIT 50;""",
        parameters=["database", "table", "start_date", "end_date"],
        use_cases=["에러 원인 파악", "장애 대응", "서비스 안정성 모니터링"]
    ),
    
    QueryTemplate(
        id="popular-content",
        category="콘텐츠 분석",
        name="인기 콘텐츠 Top 20",
        description="가장 많이 요청된 URI 및 전송량",
        sql_template="""SELECT 
  cs_uri_stem,
  COUNT(*) AS request_count,
  SUM(sc_bytes) / 1024 / 1024 AS total_mb_sent,
  AVG(time_taken) AS avg_response_time
FROM {database}.{table}
WHERE "date" >= DATE '{start_date}' AND "date" < DATE '{end_date}'
  AND sc_status = 200
GROUP BY cs_uri_stem
ORDER BY request_count DESC
LIMIT 20;""",
        parameters=["database", "table", "start_date", "end_date"],
        use_cases=["인기 콘텐츠 파악", "캐싱 전략 수립", "리소스 최적화"]
    ),
    
    QueryTemplate(
        id="user-agent-analysis",
        category="클라이언트 분석",
        name="User Agent 분석 (브라우저/디바이스)",
        description="브라우저, 모바일, 봇 등 클라이언트 유형별 분석",
        sql_template="""SELECT 
  CASE
    WHEN cs_user_agent LIKE '%Mobile%' THEN 'Mobile'
    WHEN cs_user_agent LIKE '%Chrome%' THEN 'Chrome'
    WHEN cs_user_agent LIKE '%Firefox%' THEN 'Firefox'
    WHEN cs_user_agent LIKE '%Safari%' THEN 'Safari'
    WHEN cs_user_agent LIKE '%bot%' THEN 'Bot'
    ELSE 'Other'
  END AS client_type,
  COUNT(*) AS request_count,
  SUM(sc_bytes) / 1024 / 1024 / 1024 AS total_gb
FROM {database}.{table}
WHERE "date" >= DATE '{start_date}' AND "date" < DATE '{end_date}'
GROUP BY 
  CASE
    WHEN cs_user_agent LIKE '%Mobile%' THEN 'Mobile'
    WHEN cs_user_agent LIKE '%Chrome%' THEN 'Chrome'
    WHEN cs_user_agent LIKE '%Firefox%' THEN 'Firefox'
    WHEN cs_user_agent LIKE '%Safari%' THEN 'Safari'
    WHEN cs_user_agent LIKE '%bot%' THEN 'Bot'
    ELSE 'Other'
  END
ORDER BY request_count DESC;""",
        parameters=["database", "table", "start_date", "end_date"],
        use_cases=["클라이언트 분포 파악", "모바일 최적화", "봇 트래픽 필터링"]
    ),
]


# ALB 쿼리 템플릿 (AWS 공식 문서 필드명 기준)
ALB_LOG_TEMPLATES = [
    QueryTemplate(
        id="response-time-analysis",
        category="성능 분석",
        name="응답 시간 분석 (P50, P95, P99)",
        description="백엔드 응답 시간 분포 및 느린 요청 파악",
        sql_template="""SELECT 
  target_status_code,
  COUNT(*) AS request_count,
  APPROX_PERCENTILE(target_processing_time, 0.5) AS p50_response_time,
  APPROX_PERCENTILE(target_processing_time, 0.95) AS p95_response_time,
  APPROX_PERCENTILE(target_processing_time, 0.99) AS p99_response_time,
  MAX(target_processing_time) AS max_response_time
FROM {database}.{table}
WHERE time >= '{start_datetime}'
  AND time < '{end_datetime}'
GROUP BY target_status_code
ORDER BY request_count DESC;""",
        parameters=["database", "table", "start_datetime", "end_datetime"],
        use_cases=["성능 병목 파악", "SLA 모니터링", "백엔드 최적화"]
    ),
    
    QueryTemplate(
        id="target-health",
        category="타겟 분석",
        name="타겟 그룹별 헬스 체크",
        description="타겟별 요청 수, 에러율, 응답 시간 분석",
        sql_template="""SELECT 
  target_ip,
  target_port,
  COUNT(*) AS total_requests,
  SUM(CASE WHEN elb_status_code >= 500 THEN 1 ELSE 0 END) AS error_5xx_count,
  SUM(CASE WHEN elb_status_code >= 400 AND elb_status_code < 500 THEN 1 ELSE 0 END) AS error_4xx_count,
  AVG(target_processing_time) AS avg_response_time
FROM {database}.{table}
WHERE time >= '{start_datetime}'
  AND time < '{end_datetime}'
GROUP BY target_ip, target_port
ORDER BY error_5xx_count DESC;""",
        parameters=["database", "table", "start_datetime", "end_datetime"],
        use_cases=["타겟 헬스 모니터링", "장애 타겟 식별", "로드 밸런싱 검증"]
    ),
    
    QueryTemplate(
        id="error-analysis",
        category="에러 분석",
        name="5xx 에러 상세 분석",
        description="서버 에러 발생 패턴 및 원인 분석",
        sql_template="""SELECT 
  elb_status_code,
  target_status_code,
  request_url,
  COUNT(*) AS error_count,
  AVG(target_processing_time) AS avg_processing_time
FROM {database}.{table}
WHERE elb_status_code >= 500
  AND time >= '{start_datetime}'
  AND time < '{end_datetime}'
GROUP BY elb_status_code, target_status_code, request_url
ORDER BY error_count DESC
LIMIT 30;""",
        parameters=["database", "table", "start_datetime", "end_datetime"],
        use_cases=["장애 원인 파악", "에러 패턴 분석", "서비스 안정성 개선"]
    ),
    
    QueryTemplate(
        id="top-endpoints",
        category="트래픽 분석",
        name="가장 많이 호출된 엔드포인트",
        description="API 엔드포인트별 요청 수 및 응답 시간",
        sql_template="""SELECT 
  request_url,
  request_verb,
  COUNT(*) AS request_count,
  AVG(target_processing_time) AS avg_response_time,
  SUM(sent_bytes) / 1024 / 1024 AS total_mb_sent
FROM {database}.{table}
WHERE time >= '{start_datetime}'
  AND time < '{end_datetime}'
GROUP BY request_url, request_verb
ORDER BY request_count DESC
LIMIT 20;""",
        parameters=["database", "table", "start_datetime", "end_datetime"],
        use_cases=["API 사용량 분석", "핫스팟 파악", "캐싱 전략 수립"]
    ),
    
    QueryTemplate(
        id="client-ip-analysis",
        category="트래픽 분석",
        name="클라이언트 IP별 요청 패턴",
        description="IP별 요청 수, 에러율, 전송량 분석",
        sql_template="""SELECT 
  client_ip,
  COUNT(*) AS request_count,
  SUM(CASE WHEN elb_status_code >= 400 THEN 1 ELSE 0 END) AS error_count,
  SUM(sent_bytes) / 1024 / 1024 AS total_mb_sent,
  COUNT(DISTINCT request_url) AS unique_urls_accessed
FROM {database}.{table}
WHERE time >= '{start_datetime}'
  AND time < '{end_datetime}'
GROUP BY client_ip
ORDER BY request_count DESC
LIMIT 30;""",
        parameters=["database", "table", "start_datetime", "end_datetime"],
        use_cases=["비정상 트래픽 탐지", "DDoS 공격 의심", "사용자 행동 분석"]
    ),
    
    QueryTemplate(
        id="ssl-analysis",
        category="보안",
        name="SSL/TLS 프로토콜 분석",
        description="SSL 버전 및 암호화 스위트 사용 현황",
        sql_template="""SELECT 
  ssl_protocol,
  ssl_cipher,
  COUNT(*) AS connection_count
FROM {database}.{table}
WHERE time >= '{start_datetime}'
  AND time < '{end_datetime}'
  AND ssl_protocol IS NOT NULL
  AND ssl_protocol != '-'
GROUP BY ssl_protocol, ssl_cipher
ORDER BY connection_count DESC;""",
        parameters=["database", "table", "start_datetime", "end_datetime"],
        use_cases=["보안 프로토콜 검증", "취약한 암호화 탐지", "규정 준수 확인"]
    ),
]


# CloudTrail 쿼리 템플릿 (AWS 공식 문서 필드명 기준)
CLOUDTRAIL_LOG_TEMPLATES = [
    QueryTemplate(
        id="user-activity",
        category="보안 감사",
        name="사용자별 활동 내역",
        description="IAM 사용자/역할별 API 호출 횟수 및 작업 유형",
        sql_template="""SELECT 
  useridentity.principalid AS user,
  useridentity.type AS identity_type,
  COUNT(*) AS api_call_count,
  COUNT(DISTINCT eventname) AS unique_actions
FROM {database}.{table}
WHERE timestamp >= '{start_date}'
  AND timestamp < '{end_date}'
GROUP BY useridentity.principalid, useridentity.type
ORDER BY api_call_count DESC
LIMIT 30;""",
        parameters=["database", "table", "start_date", "end_date"],
        use_cases=["사용자 활동 추적", "권한 사용 분석", "보안 감사"]
    ),
    
    QueryTemplate(
        id="failed-actions",
        category="보안 감사",
        name="실패한 API 호출 (권한 거부)",
        description="AccessDenied 및 실패한 작업 분석",
        sql_template="""SELECT 
  eventtime,
  useridentity.principalid AS user,
  eventname,
  eventsource,
  errorcode,
  errormessage,
  sourceipaddress
FROM {database}.{table}
WHERE errorcode IS NOT NULL
  AND timestamp >= '{start_date}'
  AND timestamp < '{end_date}'
ORDER BY eventtime DESC
LIMIT 100;""",
        parameters=["database", "table", "start_date", "end_date"],
        use_cases=["권한 문제 해결", "보안 위협 탐지", "정책 검증"]
    ),
    
    QueryTemplate(
        id="root-account-usage",
        category="보안 감사",
        name="루트 계정 사용 감지 (위험)",
        description="루트 계정으로 수행된 모든 작업 추적",
        sql_template="""SELECT 
  eventtime,
  eventname,
  eventsource,
  sourceipaddress,
  useragent,
  requestparameters
FROM {database}.{table}
WHERE useridentity.type = 'Root'
  AND timestamp >= '{start_date}'
  AND timestamp < '{end_date}'
ORDER BY eventtime DESC;""",
        parameters=["database", "table", "start_date", "end_date"],
        use_cases=["루트 계정 사용 감사", "보안 정책 위반 탐지", "규정 준수"]
    ),
    
    QueryTemplate(
        id="resource-changes",
        category="변경 추적",
        name="리소스 생성/삭제/수정 이벤트",
        description="인프라 변경 사항 추적",
        sql_template="""SELECT 
  eventtime,
  eventname,
  eventsource,
  useridentity.principalid AS user,
  requestparameters,
  responseelements
FROM {database}.{table}
WHERE (eventname LIKE '%Create%' 
   OR eventname LIKE '%Delete%' 
   OR eventname LIKE '%Update%'
   OR eventname LIKE '%Modify%')
  AND timestamp >= '{start_date}'
  AND timestamp < '{end_date}'
ORDER BY eventtime DESC
LIMIT 100;""",
        parameters=["database", "table", "start_date", "end_date"],
        use_cases=["변경 이력 추적", "장애 원인 분석", "감사 리포트"]
    ),
    
    QueryTemplate(
        id="console-login",
        category="보안 감사",
        name="콘솔 로그인 이벤트",
        description="AWS 콘솔 로그인 시도 및 성공/실패 분석",
        sql_template="""SELECT 
  eventtime,
  useridentity.principalid AS user,
  sourceipaddress,
  useragent,
  CASE 
    WHEN errorcode IS NULL THEN 'Success'
    ELSE 'Failed'
  END AS status
FROM {database}.{table}
WHERE eventname = 'ConsoleLogin'
  AND timestamp >= '{start_date}'
  AND timestamp < '{end_date}'
ORDER BY eventtime DESC;""",
        parameters=["database", "table", "start_date", "end_date"],
        use_cases=["로그인 모니터링", "무단 접근 탐지", "계정 보안 검증"]
    ),
    
    QueryTemplate(
        id="suspicious-ip",
        category="보안 감사",
        name="의심스러운 IP 주소 활동",
        description="특정 IP에서 발생한 모든 활동 추적",
        sql_template="""SELECT 
  eventtime,
  sourceipaddress,
  useridentity.principalid AS user,
  eventname,
  eventsource,
  errorcode
FROM {database}.{table}
WHERE sourceipaddress = '{ip_address}'
  AND timestamp >= '{start_date}'
  AND timestamp < '{end_date}'
ORDER BY eventtime DESC;""",
        parameters=["database", "table", "ip_address", "start_date", "end_date"],
        use_cases=["보안 사고 조사", "IP 기반 위협 분석", "침입 추적"]
    ),
]


# 로그 타입별 템플릿 매핑
TEMPLATE_MAP = {
    "s3_access": S3_ACCESS_LOG_TEMPLATES,
    "vpc_flow": VPC_FLOW_LOG_TEMPLATES,
    "cloudfront": CLOUDFRONT_LOG_TEMPLATES,
    "alb": ALB_LOG_TEMPLATES,
    "cloudtrail": CLOUDTRAIL_LOG_TEMPLATES,
}


@router.get("/", response_model=List[QueryTemplate])
async def list_query_templates(log_type: str = "s3_access"):
    """쿼리 템플릿 목록 조회"""
    return TEMPLATE_MAP.get(log_type, [])


@router.get("/{template_id}", response_model=QueryTemplate)
async def get_query_template(template_id: str, log_type: str = "s3_access"):
    """특정 쿼리 템플릿 조회"""
    templates = TEMPLATE_MAP.get(log_type, [])
    
    for template in templates:
        if template.id == template_id:
            return template
    
    return None


@router.get("/categories/list")
async def list_categories(log_type: str = "s3_access"):
    """쿼리 템플릿 카테고리 목록"""
    templates = TEMPLATE_MAP.get(log_type, [])
    categories = list(set(t.category for t in templates))
    return {"categories": sorted(categories)}
