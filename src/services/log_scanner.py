"""S3 로그 파일 스캐너 - 로그 파일 자동 탐지 및 메타데이터 수집"""

import re
import gzip
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
import logging
from pathlib import Path

from .aws_clients import s3_client, AWSConnectionError
from ..models.log_configuration import LogType

logger = logging.getLogger(__name__)


class FileType(Enum):
    """파일 타입"""
    LOG = "log"
    COMPRESSED = "compressed"
    ARCHIVE = "archive"
    OTHER = "other"


@dataclass
class LogFileInfo:
    """로그 파일 정보"""
    key: str
    size: int
    last_modified: datetime
    file_type: FileType
    detected_log_type: Optional[LogType] = None
    confidence_score: float = 0.0
    sample_content: Optional[str] = None
    encoding: str = "utf-8"
    line_count_estimate: Optional[int] = None
    
    @property
    def file_extension(self) -> str:
        """파일 확장자 반환"""
        return Path(self.key).suffix.lower()
    
    @property
    def file_name(self) -> str:
        """파일명 반환"""
        return Path(self.key).name
    
    @property
    def size_mb(self) -> float:
        """파일 크기 (MB)"""
        return self.size / (1024 * 1024)


@dataclass
class ScanResult:
    """스캔 결과"""
    bucket_name: str
    prefix: str
    total_files: int
    total_size: int
    log_files: List[LogFileInfo] = field(default_factory=list)
    scan_duration: float = 0.0
    date_range: Optional[Tuple[datetime, datetime]] = None
    detected_log_types: Dict[LogType, int] = field(default_factory=dict)
    
    @property
    def total_size_mb(self) -> float:
        """전체 크기 (MB)"""
        return self.total_size / (1024 * 1024)
    
    @property
    def total_size_gb(self) -> float:
        """전체 크기 (GB)"""
        return self.total_size / (1024 * 1024 * 1024)
    
    @property
    def log_files_count(self) -> int:
        """로그 파일 개수"""
        return len(self.log_files)
    
    @property
    def primary_log_type(self) -> Optional[LogType]:
        """주요 로그 타입"""
        if not self.detected_log_types:
            return None
        return max(self.detected_log_types.keys(), key=lambda k: self.detected_log_types[k])


class LogPatternMatcher:
    """로그 패턴 매처"""
    
    # S3 Access 로그 패턴
    S3_ACCESS_PATTERNS = [
        # 표준 S3 Access 로그 형식
        r'^[a-f0-9]{64}\s+[\w\-\.]+\s+\[\d{2}\/\w{3}\/\d{4}:\d{2}:\d{2}:\d{2}\s+\+\d{4}\]',
        # 간단한 S3 로그 패턴
        r'^\w+\s+\S+\s+\[\d{2}\/\w{3}\/\d{4}:\d{2}:\d{2}:\d{2}',
        # 버킷 소유자 패턴
        r'^[a-f0-9]{64}\s+[\w\-\.]+\s+\[',
    ]
    
    # CloudFront 로그 패턴
    CLOUDFRONT_PATTERNS = [
        r'^#Version:\s+1\.0',
        r'^#Fields:\s+date\s+time\s+x-edge-location',
        r'^\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\s+\w{3}\d+',
        r'^\d{4}-\d{2}-\d{2}\t\d{2}:\d{2}:\d{2}\t',
    ]
    
    # ALB 로그 패턴
    ALB_PATTERNS = [
        r'^https?\s+\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}Z\s+app/',
        r'^h2\s+\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}Z\s+app/',
        r'^\w+\s+\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}Z\s+',
    ]
    
    # VPC Flow 로그 패턴
    VPC_FLOW_PATTERNS = [
        r'^2\s+\d+\s+eni-[a-f0-9]+\s+',
        r'^version\s+account-id\s+interface-id',
        r'^\d+\s+\d+\s+eni-\w+\s+[\d\.]+\s+[\d\.]+',
    ]
    
    # CloudTrail 로그 패턴 (JSON)
    CLOUDTRAIL_PATTERNS = [
        r'^\s*{\s*"Records"\s*:\s*\[',
        r'"eventVersion"\s*:\s*"\d+\.\d+"',
        r'"eventSource"\s*:\s*"[\w\-\.]+\.amazonaws\.com"',
    ]
    
    @classmethod
    def detect_log_type(cls, content: str) -> Tuple[Optional[LogType], float]:
        """로그 타입 탐지"""
        content_lines = content.strip().split('\n')[:10]  # 처음 10줄만 검사
        
        # 각 로그 타입별 점수 계산
        scores = {
            LogType.S3_ACCESS: cls._calculate_pattern_score(content_lines, cls.S3_ACCESS_PATTERNS),
            LogType.CLOUDFRONT: cls._calculate_pattern_score(content_lines, cls.CLOUDFRONT_PATTERNS),
            LogType.ALB: cls._calculate_pattern_score(content_lines, cls.ALB_PATTERNS),
            LogType.VPC_FLOW: cls._calculate_pattern_score(content_lines, cls.VPC_FLOW_PATTERNS),
        }
        
        # CloudTrail은 JSON 형식이므로 별도 처리
        if cls._is_json_format(content):
            cloudtrail_score = cls._calculate_pattern_score([content], cls.CLOUDTRAIL_PATTERNS)
            if cloudtrail_score > 0.3:
                scores[LogType.CLOUDTRAIL] = cloudtrail_score
        
        # 가장 높은 점수의 로그 타입 반환
        if not scores or max(scores.values()) < 0.3:
            return None, 0.0
        
        best_type = max(scores.keys(), key=lambda k: scores[k])
        return best_type, scores[best_type]
    
    @classmethod
    def _calculate_pattern_score(cls, lines: List[str], patterns: List[str]) -> float:
        """패턴 매칭 점수 계산"""
        if not lines or not patterns:
            return 0.0
        
        total_matches = 0
        total_lines = len(lines)
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):  # 빈 줄이나 주석 제외
                continue
                
            for pattern in patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    total_matches += 1
                    break
        
        return total_matches / total_lines if total_lines > 0 else 0.0
    
    @classmethod
    def _is_json_format(cls, content: str) -> bool:
        """JSON 형식인지 확인"""
        try:
            json.loads(content.strip())
            return True
        except (json.JSONDecodeError, ValueError):
            return False


class LogFileScanner:
    """로그 파일 스캐너"""
    
    # 로그 파일로 인식할 확장자
    LOG_EXTENSIONS = {'.log', '.txt', '.gz', '.bz2', '.zip', '.json'}
    
    # 압축 파일 확장자
    COMPRESSED_EXTENSIONS = {'.gz', '.bz2', '.zip', '.tar', '.tar.gz'}
    
    # 로그 파일명 패턴
    LOG_FILENAME_PATTERNS = [
        r'access[_\-]?log',
        r'error[_\-]?log',
        r'application[_\-]?log',
        r'server[_\-]?log',
        r'request[_\-]?log',
        r'cloudfront',
        r'alb[_\-]?access',
        r'vpc[_\-]?flow',
        r'cloudtrail',
        r'\d{4}[_\-]\d{2}[_\-]\d{2}',  # 날짜 패턴
    ]
    
    def __init__(self, max_sample_size: int = 8192, max_files_to_sample: int = 100):
        """
        Args:
            max_sample_size: 샘플링할 최대 바이트 수
            max_files_to_sample: 샘플링할 최대 파일 수
        """
        self.max_sample_size = max_sample_size
        self.max_files_to_sample = max_files_to_sample
        self.pattern_matcher = LogPatternMatcher()
    
    def scan_bucket_prefix(self, bucket_name: str, prefix: str = "", 
                          max_files: Optional[int] = None) -> ScanResult:
        """S3 버킷/접두사 스캔"""
        start_time = datetime.now()
        
        try:
            # S3 객체 목록 조회
            objects = self._list_s3_objects(bucket_name, prefix, max_files)
            
            # 로그 파일 필터링 및 분석
            log_files = []
            total_size = 0
            
            for obj in objects:
                total_size += obj['Size']
                
                # 로그 파일 여부 확인
                if self._is_potential_log_file(obj['Key']):
                    log_file_info = self._analyze_log_file(bucket_name, obj)
                    if log_file_info:
                        log_files.append(log_file_info)
            
            # 날짜 범위 계산
            date_range = self._calculate_date_range(log_files)
            
            # 로그 타입별 통계
            detected_types = {}
            for log_file in log_files:
                if log_file.detected_log_type:
                    detected_types[log_file.detected_log_type] = \
                        detected_types.get(log_file.detected_log_type, 0) + 1
            
            scan_duration = (datetime.now() - start_time).total_seconds()
            
            return ScanResult(
                bucket_name=bucket_name,
                prefix=prefix,
                total_files=len(objects),
                total_size=total_size,
                log_files=log_files,
                scan_duration=scan_duration,
                date_range=date_range,
                detected_log_types=detected_types
            )
            
        except Exception as e:
            logger.error(f"버킷 스캔 실패 bucket={bucket_name}, prefix={prefix}: {str(e)}")
            raise AWSConnectionError("S3", f"버킷 스캔 실패: {str(e)}", e)
    
    def _list_s3_objects(self, bucket_name: str, prefix: str, 
                        max_files: Optional[int]) -> List[Dict[str, Any]]:
        """S3 객체 목록 조회"""
        objects = []
        continuation_token = None
        
        while True:
            try:
                kwargs = {
                    'Bucket': bucket_name,
                    'Prefix': prefix,
                    'MaxKeys': min(1000, max_files - len(objects)) if max_files else 1000
                }
                
                if continuation_token:
                    kwargs['ContinuationToken'] = continuation_token
                
                response = s3_client.client.list_objects_v2(**kwargs)
                
                if 'Contents' in response:
                    objects.extend(response['Contents'])
                
                # 최대 파일 수 확인
                if max_files and len(objects) >= max_files:
                    objects = objects[:max_files]
                    break
                
                # 다음 페이지 확인
                if not response.get('IsTruncated'):
                    break
                
                continuation_token = response.get('NextContinuationToken')
                
            except Exception as e:
                logger.error(f"S3 객체 목록 조회 실패: {str(e)}")
                raise
        
        return objects
    
    def _is_potential_log_file(self, key: str) -> bool:
        """로그 파일 가능성 확인"""
        file_path = Path(key)
        file_name = file_path.name.lower()
        file_ext = file_path.suffix.lower()
        
        # 확장자 기반 필터링
        if file_ext in self.LOG_EXTENSIONS:
            return True
        
        # 파일명 패턴 기반 필터링
        for pattern in self.LOG_FILENAME_PATTERNS:
            if re.search(pattern, file_name, re.IGNORECASE):
                return True
        
        # 디렉토리 구조 기반 필터링 (logs, access-logs 등)
        path_parts = file_path.parts
        log_indicators = {'logs', 'log', 'access-logs', 'cloudfront', 'alb', 'vpc-flow'}
        if any(part.lower() in log_indicators for part in path_parts):
            return True
        
        return False
    
    def _analyze_log_file(self, bucket_name: str, obj: Dict[str, Any]) -> Optional[LogFileInfo]:
        """로그 파일 분석"""
        key = obj['Key']
        size = obj['Size']
        last_modified = obj['LastModified']
        
        # 파일 타입 결정
        file_type = self._determine_file_type(key)
        
        # 너무 큰 파일은 샘플링만 수행
        if size > 100 * 1024 * 1024:  # 100MB 이상
            logger.info(f"대용량 파일 감지, 샘플링만 수행: {key} ({size / 1024 / 1024:.1f}MB)")
        
        # 샘플 내용 추출 및 로그 타입 탐지
        sample_content = None
        detected_log_type = None
        confidence_score = 0.0
        
        try:
            sample_content = self._extract_sample_content(bucket_name, key, size)
            if sample_content:
                detected_log_type, confidence_score = \
                    self.pattern_matcher.detect_log_type(sample_content)
        except Exception as e:
            logger.warning(f"샘플 내용 추출 실패 {key}: {str(e)}")
        
        # 라인 수 추정
        line_count_estimate = self._estimate_line_count(sample_content, size) if sample_content else None
        
        return LogFileInfo(
            key=key,
            size=size,
            last_modified=last_modified,
            file_type=file_type,
            detected_log_type=detected_log_type,
            confidence_score=confidence_score,
            sample_content=sample_content[:1000] if sample_content else None,  # 처음 1000자만 저장
            line_count_estimate=line_count_estimate
        )
    
    def _determine_file_type(self, key: str) -> FileType:
        """파일 타입 결정"""
        file_ext = Path(key).suffix.lower()
        
        if file_ext in self.COMPRESSED_EXTENSIONS:
            return FileType.COMPRESSED
        elif file_ext in {'.tar', '.zip', '.rar'}:
            return FileType.ARCHIVE
        elif file_ext in {'.log', '.txt', '.json'} or not file_ext:
            return FileType.LOG
        else:
            return FileType.OTHER
    
    def _extract_sample_content(self, bucket_name: str, key: str, file_size: int) -> Optional[str]:
        """샘플 내용 추출"""
        try:
            # 샘플 크기 결정 (최대 8KB 또는 파일 크기의 10%)
            sample_size = min(self.max_sample_size, max(1024, file_size // 10))
            
            # S3에서 부분 내용 읽기
            response = s3_client.client.get_object(
                Bucket=bucket_name,
                Key=key,
                Range=f'bytes=0-{sample_size - 1}'
            )
            
            content_bytes = response['Body'].read()
            
            # 압축 파일 처리
            if key.endswith('.gz'):
                try:
                    content_bytes = gzip.decompress(content_bytes)
                except Exception as e:
                    logger.warning(f"gzip 압축 해제 실패 {key}: {str(e)}")
                    return None
            
            # 텍스트 디코딩
            try:
                content = content_bytes.decode('utf-8')
            except UnicodeDecodeError:
                try:
                    content = content_bytes.decode('latin-1')
                except UnicodeDecodeError:
                    logger.warning(f"텍스트 디코딩 실패 {key}")
                    return None
            
            return content
            
        except Exception as e:
            logger.warning(f"샘플 내용 추출 실패 {key}: {str(e)}")
            return None
    
    def _estimate_line_count(self, sample_content: str, total_size: int) -> Optional[int]:
        """라인 수 추정"""
        if not sample_content:
            return None
        
        try:
            sample_lines = len(sample_content.split('\n'))
            sample_size = len(sample_content.encode('utf-8'))
            
            if sample_size > 0:
                lines_per_byte = sample_lines / sample_size
                estimated_lines = int(total_size * lines_per_byte)
                return estimated_lines
        except Exception as e:
            logger.warning(f"라인 수 추정 실패: {str(e)}")
        
        return None
    
    def _calculate_date_range(self, log_files: List[LogFileInfo]) -> Optional[Tuple[datetime, datetime]]:
        """로그 파일들의 날짜 범위 계산"""
        if not log_files:
            return None
        
        dates = [log_file.last_modified for log_file in log_files]
        return min(dates), max(dates)


class LogMetadataCollector:
    """로그 메타데이터 수집기"""
    
    def __init__(self, scanner: LogFileScanner):
        self.scanner = scanner
    
    def collect_enhanced_metadata(self, scan_result: ScanResult) -> Dict[str, Any]:
        """향상된 메타데이터 수집"""
        metadata = {
            'scan_summary': self._create_scan_summary(scan_result),
            'file_distribution': self._analyze_file_distribution(scan_result),
            'temporal_analysis': self._analyze_temporal_patterns(scan_result),
            'size_analysis': self._analyze_size_patterns(scan_result),
            'quality_assessment': self._assess_log_quality(scan_result),
            'partitioning_recommendations': self._recommend_partitioning_strategy(scan_result)
        }
        
        return metadata
    
    def _create_scan_summary(self, scan_result: ScanResult) -> Dict[str, Any]:
        """스캔 요약 생성"""
        return {
            'total_files': scan_result.total_files,
            'log_files_count': scan_result.log_files_count,
            'total_size_gb': round(scan_result.total_size_gb, 2),
            'scan_duration_seconds': round(scan_result.scan_duration, 2),
            'primary_log_type': scan_result.primary_log_type.value if scan_result.primary_log_type else None,
            'detected_log_types': {k.value: v for k, v in scan_result.detected_log_types.items()},
            'date_range': {
                'start': scan_result.date_range[0].isoformat() if scan_result.date_range else None,
                'end': scan_result.date_range[1].isoformat() if scan_result.date_range else None,
                'days_span': (scan_result.date_range[1] - scan_result.date_range[0]).days if scan_result.date_range else None
            }
        }
    
    def _analyze_file_distribution(self, scan_result: ScanResult) -> Dict[str, Any]:
        """파일 분포 분석"""
        size_buckets = {'small': 0, 'medium': 0, 'large': 0, 'xlarge': 0}
        type_distribution = {}
        
        for log_file in scan_result.log_files:
            # 크기별 분류
            size_mb = log_file.size_mb
            if size_mb < 1:
                size_buckets['small'] += 1
            elif size_mb < 10:
                size_buckets['medium'] += 1
            elif size_mb < 100:
                size_buckets['large'] += 1
            else:
                size_buckets['xlarge'] += 1
            
            # 타입별 분류
            file_type = log_file.file_type.value
            type_distribution[file_type] = type_distribution.get(file_type, 0) + 1
        
        return {
            'size_distribution': size_buckets,
            'type_distribution': type_distribution,
            'average_file_size_mb': round(
                sum(f.size_mb for f in scan_result.log_files) / len(scan_result.log_files), 2
            ) if scan_result.log_files else 0
        }
    
    def _analyze_temporal_patterns(self, scan_result: ScanResult) -> Dict[str, Any]:
        """시간적 패턴 분석"""
        if not scan_result.log_files:
            return {}
        
        # 날짜별 파일 수 분석
        daily_counts = {}
        for log_file in scan_result.log_files:
            date_key = log_file.last_modified.date().isoformat()
            daily_counts[date_key] = daily_counts.get(date_key, 0) + 1
        
        # 패턴 분석
        file_counts = list(daily_counts.values())
        avg_files_per_day = sum(file_counts) / len(file_counts) if file_counts else 0
        
        return {
            'daily_file_counts': daily_counts,
            'average_files_per_day': round(avg_files_per_day, 1),
            'max_files_per_day': max(file_counts) if file_counts else 0,
            'min_files_per_day': min(file_counts) if file_counts else 0,
            'days_with_logs': len(daily_counts)
        }
    
    def _analyze_size_patterns(self, scan_result: ScanResult) -> Dict[str, Any]:
        """크기 패턴 분석"""
        if not scan_result.log_files:
            return {}
        
        sizes_mb = [f.size_mb for f in scan_result.log_files]
        
        return {
            'total_size_gb': round(scan_result.total_size_gb, 2),
            'average_size_mb': round(sum(sizes_mb) / len(sizes_mb), 2),
            'median_size_mb': round(sorted(sizes_mb)[len(sizes_mb) // 2], 2),
            'largest_file_mb': round(max(sizes_mb), 2),
            'smallest_file_mb': round(min(sizes_mb), 2)
        }
    
    def _assess_log_quality(self, scan_result: ScanResult) -> Dict[str, Any]:
        """로그 품질 평가"""
        if not scan_result.log_files:
            return {'overall_score': 0, 'issues': ['No log files found']}
        
        issues = []
        score = 100
        
        # 로그 타입 탐지율 확인
        detected_files = sum(1 for f in scan_result.log_files if f.detected_log_type)
        detection_rate = detected_files / len(scan_result.log_files)
        
        if detection_rate < 0.8:
            issues.append(f"Low log type detection rate: {detection_rate:.1%}")
            score -= 20
        
        # 신뢰도 점수 확인
        avg_confidence = sum(f.confidence_score for f in scan_result.log_files 
                           if f.confidence_score > 0) / max(1, detected_files)
        
        if avg_confidence < 0.7:
            issues.append(f"Low average confidence score: {avg_confidence:.2f}")
            score -= 15
        
        # 파일 크기 일관성 확인
        sizes_mb = [f.size_mb for f in scan_result.log_files]
        if len(sizes_mb) > 1:
            size_variance = max(sizes_mb) / min(sizes_mb) if min(sizes_mb) > 0 else float('inf')
            if size_variance > 100:  # 100배 이상 차이
                issues.append("High file size variance detected")
                score -= 10
        
        # 시간적 일관성 확인
        if scan_result.date_range:
            days_span = (scan_result.date_range[1] - scan_result.date_range[0]).days
            if days_span > 0:
                files_per_day = len(scan_result.log_files) / days_span
                if files_per_day < 0.1:  # 하루에 0.1개 미만
                    issues.append("Sparse log file distribution over time")
                    score -= 10
        
        return {
            'overall_score': max(0, score),
            'detection_rate': round(detection_rate, 2),
            'average_confidence': round(avg_confidence, 2),
            'issues': issues
        }
    
    def _recommend_partitioning_strategy(self, scan_result: ScanResult) -> Dict[str, Any]:
        """파티셔닝 전략 추천"""
        if not scan_result.date_range:
            return {'strategy': 'none', 'reason': 'No date range available'}
        
        days_span = (scan_result.date_range[1] - scan_result.date_range[0]).days
        total_size_gb = scan_result.total_size_gb
        files_count = len(scan_result.log_files)
        
        # 파티셔닝 전략 결정
        if days_span <= 7:
            strategy = 'none'
            reason = 'Data spans less than a week'
        elif days_span <= 90 and total_size_gb < 10:
            strategy = 'daily'
            reason = 'Small dataset with short time range'
        elif days_span <= 365 and total_size_gb < 100:
            strategy = 'daily'
            reason = 'Medium dataset suitable for daily partitions'
        elif days_span <= 365:
            strategy = 'monthly'
            reason = 'Large dataset with yearly span'
        else:
            strategy = 'yearly'
            reason = 'Multi-year dataset requires yearly partitions'
        
        return {
            'strategy': strategy,
            'reason': reason,
            'estimated_partitions': self._estimate_partition_count(strategy, days_span),
            'data_characteristics': {
                'days_span': days_span,
                'total_size_gb': total_size_gb,
                'files_count': files_count,
                'avg_files_per_day': round(files_count / max(1, days_span), 1)
            }
        }
    
    def _estimate_partition_count(self, strategy: str, days_span: int) -> int:
        """파티션 수 추정"""
        if strategy == 'daily':
            return days_span
        elif strategy == 'monthly':
            return max(1, days_span // 30)
        elif strategy == 'yearly':
            return max(1, days_span // 365)
        else:
            return 1