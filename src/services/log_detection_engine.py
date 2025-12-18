"""로그 탐지 및 분류 엔진 - 통합 서비스"""

import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import logging

from .log_scanner import LogFileScanner, LogMetadataCollector, ScanResult
from .log_classifier import LogFormatClassifier, LogSampleExtractor, LogSample
from .log_metadata_analyzer import LogMetadataAnalyzer, MetadataAnalysisResult
from .aws_clients import AWSConnectionError
from ..models.log_configuration import LogType

logger = logging.getLogger(__name__)


@dataclass
class DetectionRequest:
    """탐지 요청"""
    bucket_name: str
    prefix: str = ""
    max_files: Optional[int] = None
    detailed_analysis: bool = True
    sample_files: bool = True


@dataclass
class DetectionProgress:
    """탐지 진행 상황"""
    stage: str
    progress_percentage: float
    current_task: str
    estimated_remaining_seconds: Optional[float] = None
    files_processed: int = 0
    total_files: int = 0


@dataclass
class DetectionResult:
    """탐지 결과"""
    request: DetectionRequest
    scan_result: ScanResult
    metadata_analysis: MetadataAnalysisResult
    execution_time_seconds: float
    success: bool
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            'request': {
                'bucket_name': self.request.bucket_name,
                'prefix': self.request.prefix,
                'max_files': self.request.max_files,
                'detailed_analysis': self.request.detailed_analysis
            },
            'scan_summary': {
                'total_files': self.scan_result.total_files,
                'log_files_count': self.scan_result.log_files_count,
                'total_size_gb': self.scan_result.total_size_gb,
                'primary_log_type': self.scan_result.primary_log_type.value if self.scan_result.primary_log_type else None,
                'detected_log_types': {k.value: v for k, v in self.scan_result.detected_log_types.items()},
                'date_range': {
                    'start': self.scan_result.date_range[0].isoformat() if self.scan_result.date_range else None,
                    'end': self.scan_result.date_range[1].isoformat() if self.scan_result.date_range else None
                }
            },
            'metadata_analysis': self.metadata_analysis.to_dict(),
            'execution_info': {
                'execution_time_seconds': self.execution_time_seconds,
                'success': self.success,
                'error_message': self.error_message
            }
        }


class LogDetectionEngine:
    """로그 탐지 및 분류 엔진"""
    
    def __init__(self):
        self.scanner = LogFileScanner()
        self.classifier = LogFormatClassifier()
        self.sample_extractor = LogSampleExtractor()
        self.metadata_analyzer = LogMetadataAnalyzer()
        self.metadata_collector = LogMetadataCollector(self.scanner)
        
        # 진행 상황 콜백
        self.progress_callback: Optional[callable] = None
    
    def set_progress_callback(self, callback: callable) -> None:
        """진행 상황 콜백 설정"""
        self.progress_callback = callback
    
    async def detect_logs_async(self, request: DetectionRequest) -> DetectionResult:
        """비동기 로그 탐지"""
        start_time = datetime.now()
        
        try:
            # 1단계: S3 스캔
            await self._report_progress("scanning", 10, "S3 버킷 스캔 중...")
            scan_result = await self._scan_bucket_async(request)
            
            # 2단계: 로그 분류 (샘플링)
            if request.sample_files and scan_result.log_files:
                await self._report_progress("classifying", 40, "로그 파일 분류 중...")
                await self._enhance_classification_async(request.bucket_name, scan_result)
            
            # 3단계: 메타데이터 분석
            await self._report_progress("analyzing", 70, "메타데이터 분석 중...")
            metadata_analysis = await self._analyze_metadata_async(scan_result, request.detailed_analysis)
            
            # 4단계: 완료
            await self._report_progress("completed", 100, "분석 완료")
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return DetectionResult(
                request=request,
                scan_result=scan_result,
                metadata_analysis=metadata_analysis,
                execution_time_seconds=execution_time,
                success=True
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"로그 탐지 실패: {str(e)}")
            
            return DetectionResult(
                request=request,
                scan_result=ScanResult(
                    bucket_name=request.bucket_name,
                    prefix=request.prefix,
                    total_files=0,
                    total_size=0
                ),
                metadata_analysis=None,
                execution_time_seconds=execution_time,
                success=False,
                error_message=str(e)
            )
    
    def detect_logs(self, request: DetectionRequest) -> DetectionResult:
        """동기 로그 탐지"""
        return asyncio.run(self.detect_logs_async(request))
    
    async def _scan_bucket_async(self, request: DetectionRequest) -> ScanResult:
        """비동기 버킷 스캔"""
        loop = asyncio.get_event_loop()
        
        # CPU 집약적 작업을 별도 스레드에서 실행
        # functools.partial을 사용하여 키워드 인자 전달
        from functools import partial
        scan_func = partial(
            self.scanner.scan_bucket_prefix,
            bucket_name=request.bucket_name,
            prefix=request.prefix,
            max_files=request.max_files
        )
        scan_result = await loop.run_in_executor(None, scan_func)
        
        # 버킷 이름 기반 로그 타입 힌트 적용
        scan_result = self._apply_bucket_name_hint(request.bucket_name, scan_result)
        
        return scan_result
    
    def _apply_bucket_name_hint(self, bucket_name: str, scan_result: ScanResult) -> ScanResult:
        """버킷 이름에서 로그 타입 힌트 추출하여 적용"""
        bucket_lower = bucket_name.lower()
        
        # 버킷 이름에서 로그 타입 힌트 추출
        hint_type = None
        if 'alb' in bucket_lower or 'elb' in bucket_lower:
            hint_type = LogType.ALB
        elif 'cloudfront' in bucket_lower or 'cf-' in bucket_lower:
            hint_type = LogType.CLOUDFRONT
        elif 'vpc' in bucket_lower and 'flow' in bucket_lower:
            hint_type = LogType.VPC_FLOW
        elif 'cloudtrail' in bucket_lower:
            hint_type = LogType.CLOUDTRAIL
        elif 's3' in bucket_lower and 'access' in bucket_lower:
            hint_type = LogType.S3_ACCESS
        
        # 힌트가 있고, 현재 감지된 타입과 다르면 힌트 타입으로 변경
        if hint_type and scan_result.primary_log_type != hint_type:
            logger.info(f"버킷 이름 힌트 적용: {bucket_name} -> {hint_type.value}")
            scan_result.primary_log_type = hint_type
            
            # detected_log_types도 업데이트
            if hint_type not in scan_result.detected_log_types:
                scan_result.detected_log_types[hint_type] = scan_result.log_files_count
        
        return scan_result
    
    async def _enhance_classification_async(self, bucket_name: str, scan_result: ScanResult) -> None:
        """비동기 분류 향상"""
        # 샘플링할 파일 선택 (최대 20개)
        sample_files = scan_result.log_files[:20]
        
        for i, log_file in enumerate(sample_files):
            # 진행 상황 업데이트
            progress = 40 + (i / len(sample_files)) * 20  # 40-60% 구간
            await self._report_progress(
                "classifying", 
                progress, 
                f"로그 파일 분류 중... ({i+1}/{len(sample_files)})",
                files_processed=i,
                total_files=len(sample_files)
            )
            
            # 샘플 추출 및 분류
            sample = self.sample_extractor.extract_sample(bucket_name, log_file.key)
            if sample:
                result = self.classifier.classify_log_sample(sample)
                if result and result.confidence_score > log_file.confidence_score:
                    # 더 높은 신뢰도로 업데이트
                    log_file.detected_log_type = result.log_type
                    log_file.confidence_score = result.confidence_score
            
            # 비동기 처리를 위한 양보
            await asyncio.sleep(0.01)
        
        # 탐지된 로그 타입 통계 업데이트
        scan_result.detected_log_types.clear()
        for log_file in scan_result.log_files:
            if log_file.detected_log_type:
                scan_result.detected_log_types[log_file.detected_log_type] = \
                    scan_result.detected_log_types.get(log_file.detected_log_type, 0) + 1
    
    async def _analyze_metadata_async(self, scan_result: ScanResult, 
                                    detailed_analysis: bool) -> MetadataAnalysisResult:
        """비동기 메타데이터 분석"""
        loop = asyncio.get_event_loop()
        
        # CPU 집약적 작업을 별도 스레드에서 실행
        analysis_result = await loop.run_in_executor(
            None,
            self.metadata_analyzer.analyze_logs,
            scan_result,
            detailed_analysis
        )
        
        return analysis_result
    
    async def _report_progress(self, stage: str, progress: float, task: str,
                             files_processed: int = 0, total_files: int = 0) -> None:
        """진행 상황 보고"""
        if self.progress_callback:
            progress_info = DetectionProgress(
                stage=stage,
                progress_percentage=progress,
                current_task=task,
                files_processed=files_processed,
                total_files=total_files
            )
            
            try:
                if asyncio.iscoroutinefunction(self.progress_callback):
                    await self.progress_callback(progress_info)
                else:
                    self.progress_callback(progress_info)
            except Exception as e:
                logger.warning(f"진행 상황 콜백 오류: {str(e)}")
    
    def get_supported_log_types(self) -> List[LogType]:
        """지원하는 로그 타입 목록"""
        return self.classifier.get_supported_log_types()
    
    def get_log_format_examples(self) -> Dict[LogType, str]:
        """로그 형식 예시"""
        return self.classifier.get_format_examples()
    
    def validate_bucket_access(self, bucket_name: str) -> Tuple[bool, Optional[str]]:
        """버킷 접근 권한 검증"""
        try:
            from .aws_clients import s3_client
            
            # 버킷 존재 여부 확인
            if not s3_client.bucket_exists(bucket_name):
                return False, f"버킷 '{bucket_name}'이 존재하지 않습니다"
            
            # 목록 조회 권한 확인
            s3_client.client.list_objects_v2(Bucket=bucket_name, MaxKeys=1)
            
            return True, None
            
        except AWSConnectionError as e:
            return False, f"AWS 연결 오류: {e.error}"
        except Exception as e:
            return False, f"버킷 접근 오류: {str(e)}"
    
    def estimate_scan_time(self, bucket_name: str, prefix: str = "") -> Dict[str, Any]:
        """스캔 시간 추정"""
        try:
            from .aws_clients import s3_client
            
            # 샘플 객체 수 확인 (최대 1000개)
            response = s3_client.client.list_objects_v2(
                Bucket=bucket_name,
                Prefix=prefix,
                MaxKeys=1000
            )
            
            sample_count = len(response.get('Contents', []))
            is_truncated = response.get('IsTruncated', False)
            
            # 추정 계산
            if is_truncated:
                estimated_total = sample_count * 10  # 대략적 추정
            else:
                estimated_total = sample_count
            
            # 스캔 시간 추정 (파일당 0.1초 기준)
            estimated_scan_seconds = estimated_total * 0.1
            
            # 분류 시간 추정 (샘플링 파일당 0.5초)
            sample_files = min(20, estimated_total)
            estimated_classification_seconds = sample_files * 0.5
            
            # 분석 시간 추정 (고정 5초)
            estimated_analysis_seconds = 5
            
            total_estimated_seconds = (
                estimated_scan_seconds + 
                estimated_classification_seconds + 
                estimated_analysis_seconds
            )
            
            return {
                'estimated_files': estimated_total,
                'sample_files_for_classification': sample_files,
                'estimated_scan_seconds': estimated_scan_seconds,
                'estimated_classification_seconds': estimated_classification_seconds,
                'estimated_analysis_seconds': estimated_analysis_seconds,
                'total_estimated_seconds': total_estimated_seconds,
                'is_estimate': is_truncated
            }
            
        except Exception as e:
            logger.warning(f"스캔 시간 추정 실패: {str(e)}")
            return {
                'estimated_files': 0,
                'total_estimated_seconds': 30,  # 기본값
                'error': str(e)
            }


class LogDetectionService:
    """로그 탐지 서비스 (싱글톤)"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.engine = LogDetectionEngine()
        return cls._instance
    
    def detect_logs(self, bucket_name: str, prefix: str = "", 
                   max_files: Optional[int] = None,
                   detailed_analysis: bool = True,
                   progress_callback: Optional[callable] = None) -> DetectionResult:
        """로그 탐지 실행"""
        request = DetectionRequest(
            bucket_name=bucket_name,
            prefix=prefix,
            max_files=max_files,
            detailed_analysis=detailed_analysis
        )
        
        if progress_callback:
            self.engine.set_progress_callback(progress_callback)
        
        return self.engine.detect_logs(request)
    
    async def detect_logs_async(self, bucket_name: str, prefix: str = "",
                              max_files: Optional[int] = None,
                              detailed_analysis: bool = True,
                              progress_callback: Optional[callable] = None) -> DetectionResult:
        """비동기 로그 탐지 실행"""
        request = DetectionRequest(
            bucket_name=bucket_name,
            prefix=prefix,
            max_files=max_files,
            detailed_analysis=detailed_analysis
        )
        
        if progress_callback:
            self.engine.set_progress_callback(progress_callback)
        
        return await self.engine.detect_logs_async(request)
    
    def validate_bucket_access(self, bucket_name: str) -> Tuple[bool, Optional[str]]:
        """버킷 접근 권한 검증"""
        return self.engine.validate_bucket_access(bucket_name)
    
    def estimate_scan_time(self, bucket_name: str, prefix: str = "") -> Dict[str, Any]:
        """스캔 시간 추정"""
        return self.engine.estimate_scan_time(bucket_name, prefix)
    
    def get_supported_log_types(self) -> List[LogType]:
        """지원하는 로그 타입 목록"""
        return self.engine.get_supported_log_types()
    
    def get_log_format_examples(self) -> Dict[LogType, str]:
        """로그 형식 예시"""
        return self.engine.get_log_format_examples()


# 전역 서비스 인스턴스
log_detection_service = LogDetectionService()