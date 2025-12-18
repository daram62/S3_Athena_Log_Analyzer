"""AWS 서비스 클라이언트 래퍼 및 연결 유틸리티"""

import boto3
import json
import time
from typing import Optional, Dict, Any, List
from botocore.exceptions import ClientError, NoCredentialsError, BotoCoreError
from botocore.config import Config
from dataclasses import dataclass
from enum import Enum
import logging

from ..config import settings

logger = logging.getLogger(__name__)


class AWSServiceType(Enum):
    """AWS 서비스 타입"""
    S3 = "s3"
    ATHENA = "athena"
    BEDROCK = "bedrock-runtime"
    GLUE = "glue"


@dataclass
class RetryConfig:
    """재시도 설정"""
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0


class AWSConnectionError(Exception):
    """AWS 연결 오류"""
    def __init__(self, service: str, error: str, original_error: Optional[Exception] = None):
        self.service = service
        self.error = error
        self.original_error = original_error
        super().__init__(f"AWS {service} connection error: {error}")


class AWSAuthenticationError(AWSConnectionError):
    """AWS 인증 오류"""
    pass


class AWSPermissionError(AWSConnectionError):
    """AWS 권한 오류"""
    pass


class AWSClientManager:
    """AWS 클라이언트 관리자"""
    
    def __init__(self, region: Optional[str] = None, profile: Optional[str] = None):
        self.region = region or settings.aws.region
        self.profile = profile or settings.aws.profile
        self._clients: Dict[str, Any] = {}
        self._session: Optional[boto3.Session] = None
        
        # Boto3 설정
        self._config = Config(
            region_name=self.region,
            retries={
                'max_attempts': 3,
                'mode': 'adaptive'
            },
            max_pool_connections=50
        )
    
    @property
    def session(self) -> boto3.Session:
        """AWS 세션 반환"""
        if self._session is None:
            try:
                if self.profile:
                    self._session = boto3.Session(profile_name=self.profile)
                else:
                    self._session = boto3.Session()
                
                # 인증 테스트
                sts_client = self._session.client('sts', config=self._config)
                identity = sts_client.get_caller_identity()
                logger.info(f"AWS 인증 성공: {identity.get('Arn')}")
                
            except NoCredentialsError as e:
                raise AWSAuthenticationError("STS", "AWS 자격 증명을 찾을 수 없습니다", e)
            except ClientError as e:
                error_code = e.response['Error']['Code']
                if error_code in ['InvalidUserID.NotFound', 'AccessDenied']:
                    raise AWSAuthenticationError("STS", f"인증 실패: {error_code}", e)
                raise AWSConnectionError("STS", f"연결 실패: {error_code}", e)
        
        return self._session
    
    def get_client(self, service_type: AWSServiceType, **kwargs) -> Any:
        """AWS 클라이언트 반환"""
        service_name = service_type.value
        client_key = f"{service_name}_{self.region}"
        
        if client_key not in self._clients:
            try:
                client = self.session.client(
                    service_name,
                    config=self._config,
                    **kwargs
                )
                
                # 클라이언트 연결 테스트
                self._test_client_connection(service_type, client)
                self._clients[client_key] = client
                
                logger.info(f"AWS {service_name} 클라이언트 생성 완료")
                
            except ClientError as e:
                error_code = e.response['Error']['Code']
                if error_code == 'AccessDenied':
                    raise AWSPermissionError(service_name, f"권한 부족: {error_code}", e)
                raise AWSConnectionError(service_name, f"클라이언트 생성 실패: {error_code}", e)
            except Exception as e:
                raise AWSConnectionError(service_name, f"예상치 못한 오류: {str(e)}", e)
        
        return self._clients[client_key]
    
    def _test_client_connection(self, service_type: AWSServiceType, client: Any) -> None:
        """클라이언트 연결 테스트"""
        try:
            if service_type == AWSServiceType.S3:
                client.list_buckets()
            elif service_type == AWSServiceType.ATHENA:
                client.list_work_groups(MaxResults=1)
            elif service_type == AWSServiceType.GLUE:
                client.get_databases(MaxResults=1)
            elif service_type == AWSServiceType.BEDROCK:
                # Bedrock은 연결 테스트가 제한적이므로 기본 설정만 확인
                pass
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code not in ['AccessDenied']:  # 권한 오류는 상위에서 처리
                raise
    
    def clear_clients(self) -> None:
        """모든 클라이언트 캐시 삭제"""
        self._clients.clear()
        logger.info("AWS 클라이언트 캐시 삭제 완료")


class S3ClientWrapper:
    """S3 클라이언트 래퍼"""
    
    def __init__(self, client_manager: AWSClientManager):
        self.client_manager = client_manager
        self.retry_config = RetryConfig()
    
    @property
    def client(self):
        """S3 클라이언트 반환"""
        return self.client_manager.get_client(AWSServiceType.S3)
    
    def bucket_exists(self, bucket_name: str) -> bool:
        """버킷 존재 여부 확인"""
        try:
            self.client.head_bucket(Bucket=bucket_name)
            return True
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                return False
            raise AWSConnectionError("S3", f"버킷 확인 실패: {error_code}", e)
    
    def get_bucket_policy(self, bucket_name: str) -> Optional[Dict[str, Any]]:
        """버킷 정책 조회"""
        try:
            response = self.client.get_bucket_policy(Bucket=bucket_name)
            return json.loads(response['Policy'])
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NoSuchBucketPolicy':
                return None
            raise AWSConnectionError("S3", f"버킷 정책 조회 실패: {error_code}", e)
    
    def put_bucket_policy(self, bucket_name: str, policy: Dict[str, Any]) -> None:
        """버킷 정책 설정"""
        try:
            policy_json = json.dumps(policy)
            self.client.put_bucket_policy(Bucket=bucket_name, Policy=policy_json)
            logger.info(f"버킷 정책 설정 완료: {bucket_name}")
        except ClientError as e:
            error_code = e.response['Error']['Code']
            raise AWSConnectionError("S3", f"버킷 정책 설정 실패: {error_code}", e)
    
    def enable_bucket_logging(self, source_bucket: str, target_bucket: str, prefix: str = "") -> None:
        """버킷 로깅 활성화"""
        try:
            logging_config = {
                'LoggingEnabled': {
                    'TargetBucket': target_bucket,
                    'TargetPrefix': prefix
                }
            }
            
            self.client.put_bucket_logging(
                Bucket=source_bucket,
                BucketLoggingStatus=logging_config
            )
            logger.info(f"버킷 로깅 활성화 완료: {source_bucket} -> {target_bucket}")
        except ClientError as e:
            error_code = e.response['Error']['Code']
            raise AWSConnectionError("S3", f"버킷 로깅 설정 실패: {error_code}", e)
    
    def get_bucket_logging(self, bucket_name: str) -> Optional[Dict[str, Any]]:
        """버킷 로깅 설정 조회"""
        try:
            response = self.client.get_bucket_logging(Bucket=bucket_name)
            return response.get('LoggingEnabled')
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NoSuchBucket':
                return None
            raise AWSConnectionError("S3", f"버킷 로깅 조회 실패: {error_code}", e)


class AthenaClientWrapper:
    """Athena 클라이언트 래퍼"""
    
    def __init__(self, client_manager: AWSClientManager):
        self.client_manager = client_manager
        self.retry_config = RetryConfig()
    
    @property
    def client(self):
        """Athena 클라이언트 반환"""
        return self.client_manager.get_client(AWSServiceType.ATHENA)
    
    def execute_query(self, query: str, database: str, output_location: str) -> str:
        """쿼리 실행"""
        try:
            response = self.client.start_query_execution(
                QueryString=query,
                QueryExecutionContext={'Database': database},
                ResultConfiguration={'OutputLocation': output_location}
            )
            
            execution_id = response['QueryExecutionId']
            logger.info(f"Athena 쿼리 실행 시작: {execution_id}")
            return execution_id
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            raise AWSConnectionError("Athena", f"쿼리 실행 실패: {error_code}", e)
    
    def get_query_execution(self, execution_id: str) -> Dict[str, Any]:
        """쿼리 실행 상태 조회"""
        try:
            response = self.client.get_query_execution(QueryExecutionId=execution_id)
            return response['QueryExecution']
        except ClientError as e:
            error_code = e.response['Error']['Code']
            raise AWSConnectionError("Athena", f"쿼리 상태 조회 실패: {error_code}", e)
    
    def wait_for_query_completion(self, execution_id: str, timeout: int = 300) -> Dict[str, Any]:
        """쿼리 완료 대기"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            execution = self.get_query_execution(execution_id)
            state = execution['Status']['State']
            
            if state in ['SUCCEEDED', 'FAILED', 'CANCELLED']:
                return execution
            
            time.sleep(2)
        
        raise AWSConnectionError("Athena", f"쿼리 타임아웃: {execution_id}")


class BedrockClientWrapper:
    """Bedrock 클라이언트 래퍼"""
    
    def __init__(self, client_manager: AWSClientManager):
        self.client_manager = client_manager
        self.retry_config = RetryConfig()
    
    @property
    def client(self):
        """Bedrock 클라이언트 반환"""
        return self.client_manager.get_client(AWSServiceType.BEDROCK)
    
    def invoke_model(self, model_id: str, prompt: str, max_tokens: int = 1000) -> str:
        """모델 호출"""
        try:
            body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": max_tokens,
                "messages": [{"role": "user", "content": prompt}]
            }
            
            response = self.client.invoke_model(
                modelId=model_id,
                body=json.dumps(body)
            )
            
            response_body = json.loads(response['body'].read())
            return response_body['content'][0]['text']
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            raise AWSConnectionError("Bedrock", f"모델 호출 실패: {error_code}", e)


class GlueClientWrapper:
    """Glue 클라이언트 래퍼"""
    
    def __init__(self, client_manager: AWSClientManager):
        self.client_manager = client_manager
        self.retry_config = RetryConfig()
    
    @property
    def client(self):
        """Glue 클라이언트 반환"""
        return self.client_manager.get_client(AWSServiceType.GLUE)
    
    def create_database(self, database_name: str, description: str = "") -> None:
        """데이터베이스 생성"""
        try:
            self.client.create_database(
                DatabaseInput={
                    'Name': database_name,
                    'Description': description
                }
            )
            logger.info(f"Glue 데이터베이스 생성 완료: {database_name}")
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code != 'AlreadyExistsException':
                raise AWSConnectionError("Glue", f"데이터베이스 생성 실패: {error_code}", e)
    
    def create_table(self, database_name: str, table_input: Dict[str, Any]) -> None:
        """테이블 생성"""
        try:
            self.client.create_table(
                DatabaseName=database_name,
                TableInput=table_input
            )
            logger.info(f"Glue 테이블 생성 완료: {database_name}.{table_input['Name']}")
        except ClientError as e:
            error_code = e.response['Error']['Code']
            raise AWSConnectionError("Glue", f"테이블 생성 실패: {error_code}", e)


def retry_with_backoff(func, retry_config: RetryConfig = None, *args, **kwargs):
    """지수 백오프를 사용한 재시도 데코레이터"""
    if retry_config is None:
        retry_config = RetryConfig()
    
    last_exception = None
    
    for attempt in range(retry_config.max_attempts):
        try:
            return func(*args, **kwargs)
        except (ClientError, BotoCoreError) as e:
            last_exception = e
            
            if attempt == retry_config.max_attempts - 1:
                break
            
            # 재시도 불가능한 오류는 즉시 실패
            if isinstance(e, ClientError):
                error_code = e.response['Error']['Code']
                if error_code in ['AccessDenied', 'InvalidUserID.NotFound', 'NoSuchBucket']:
                    break
            
            delay = min(
                retry_config.base_delay * (retry_config.exponential_base ** attempt),
                retry_config.max_delay
            )
            
            logger.warning(f"재시도 {attempt + 1}/{retry_config.max_attempts} "
                          f"({delay:.1f}초 후): {str(e)}")
            time.sleep(delay)
    
    raise last_exception


# 전역 클라이언트 매니저 인스턴스
aws_client_manager = AWSClientManager()

# 개별 클라이언트 래퍼 인스턴스
s3_client = S3ClientWrapper(aws_client_manager)
athena_client = AthenaClientWrapper(aws_client_manager)
bedrock_client = BedrockClientWrapper(aws_client_manager)
glue_client = GlueClientWrapper(aws_client_manager)


class AWSClients:
    """통합 AWS 클라이언트 관리 클래스"""
    
    def __init__(self, region: Optional[str] = None, profile: Optional[str] = None):
        self.client_manager = AWSClientManager(region, profile)
        self._s3_wrapper = None
        self._athena_wrapper = None
        self._bedrock_wrapper = None
        self._glue_wrapper = None
    
    def get_s3_client(self):
        """S3 클라이언트 반환"""
        if self._s3_wrapper is None:
            self._s3_wrapper = S3ClientWrapper(self.client_manager)
        return self._s3_wrapper.client
    
    def get_athena_client(self):
        """Athena 클라이언트 반환"""
        if self._athena_wrapper is None:
            self._athena_wrapper = AthenaClientWrapper(self.client_manager)
        return self._athena_wrapper.client
    
    def get_bedrock_runtime_client(self):
        """Bedrock Runtime 클라이언트 반환"""
        if self._bedrock_wrapper is None:
            self._bedrock_wrapper = BedrockClientWrapper(self.client_manager)
        return self._bedrock_wrapper.client
    
    def get_glue_client(self):
        """Glue 클라이언트 반환"""
        if self._glue_wrapper is None:
            self._glue_wrapper = GlueClientWrapper(self.client_manager)
        return self._glue_wrapper.client
    
    def get_s3_wrapper(self) -> S3ClientWrapper:
        """S3 래퍼 반환"""
        if self._s3_wrapper is None:
            self._s3_wrapper = S3ClientWrapper(self.client_manager)
        return self._s3_wrapper
    
    def get_athena_wrapper(self) -> AthenaClientWrapper:
        """Athena 래퍼 반환"""
        if self._athena_wrapper is None:
            self._athena_wrapper = AthenaClientWrapper(self.client_manager)
        return self._athena_wrapper
    
    def get_bedrock_wrapper(self) -> BedrockClientWrapper:
        """Bedrock 래퍼 반환"""
        if self._bedrock_wrapper is None:
            self._bedrock_wrapper = BedrockClientWrapper(self.client_manager)
        return self._bedrock_wrapper
    
    def get_glue_wrapper(self) -> GlueClientWrapper:
        """Glue 래퍼 반환"""
        if self._glue_wrapper is None:
            self._glue_wrapper = GlueClientWrapper(self.client_manager)
        return self._glue_wrapper
