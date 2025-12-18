"""로그 형식 분류기 - 다양한 AWS 로그 타입 자동 분류 및 검증"""

import re
import json
import gzip
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
import logging
from abc import ABC, abstractmethod

from ..models.log_configuration import LogType
from .aws_clients import s3_client

logger = logging.getLogger(__name__)


@dataclass
class LogSample:
    """로그 샘플 데이터"""
    content: str
    source_key: str
    sample_size: int
    encoding: str = "utf-8"
    is_compressed: bool = False


@dataclass
class ClassificationResult:
    """분류 결과"""
    log_type: LogType
    confidence_score: float
    matched_patterns: List[str]
    field_count: int
    sample_lines: List[str]
    validation_errors: List[str] = field(default_factory=list)
    
    @property
    def is_high_confidence(self) -> bool:
        """높은 신뢰도인지 확인"""
        return self.confidence_score >= 0.8
    
    @property
    def is_valid(self) -> bool:
        """유효한 분류 결과인지 확인"""
        return len(self.validation_errors) == 0


@dataclass
class CustomLogFormat:
    """사용자 정의 로그 형식"""
    name: str
    description: str
    patterns: List[str]
    field_separator: str
    field_names: List[str]
    sample_line: str
    created_by: str
    created_at: datetime


class LogClassifier(ABC):
    """로그 분류기 기본 클래스"""
    
    @abstractmethod
    def classify(self, sample: LogSample) -> Optional[ClassificationResult]:
        """로그 샘플 분류"""
        pass
    
    @abstractmethod
    def validate_format(self, sample: LogSample) -> List[str]:
        """로그 형식 검증"""
        pass
    
    @property
    @abstractmethod
    def supported_log_type(self) -> LogType:
        """지원하는 로그 타입"""
        pass


class S3AccessLogClassifier(LogClassifier):
    """S3 Access 로그 분류기"""
    
    # S3 Access 로그의 26개 필드
    EXPECTED_FIELDS = [
        'bucket_owner', 'bucket', 'time', 'remote_ip', 'requester',
        'request_id', 'operation', 'key', 'request_uri', 'http_status',
        'error_code', 'bytes_sent', 'object_size', 'total_time',
        'turn_around_time', 'referer', 'user_agent', 'version_id',
        'host_id', 'signature_version', 'cipher_suite', 'authentication_type',
        'host_header', 'tls_version', 'access_point_arn', 'acl_required'
    ]
    
    # S3 로그 패턴들
    PATTERNS = [
        # 표준 S3 Access 로그 패턴
        r'^([a-f0-9]{64})\s+([\w\-\.]+)\s+\[([^\]]+)\]\s+([^\s]+)\s+([^\s]+)\s+([^\s]+)\s+([^\s]+)\s+([^\s]+)\s+(\"[^\"]*\"|\S+)\s+(\d+|-)\s+([^\s]+)\s+(\d+|-)\s+(\d+|-)\s+(\d+|-)\s+(\d+|-)\s+(\"[^\"]*\"|-)\s+(\"[^\"]*\"|-)\s+([^\s]+)\s+([^\s]+)\s+([^\s]+)\s+([^\s]+)\s+([^\s]+)\s+([^\s]+)\s+([^\s]+)\s+([^\s]+)\s+([^\s]+)',
        
        # 간단한 패턴 (필수 필드만)
        r'^([a-f0-9]{64})\s+([\w\-\.]+)\s+\[([^\]]+)\]',
        
        # 버킷 소유자 + 버킷명 패턴
        r'^[a-f0-9]{64}\s+[\w\-\.]+\s+\[\d{2}\/\w{3}\/\d{4}:\d{2}:\d{2}:\d{2}\s+\+\d{4}\]',
    ]
    
    @property
    def supported_log_type(self) -> LogType:
        return LogType.S3_ACCESS
    
    def classify(self, sample: LogSample) -> Optional[ClassificationResult]:
        """S3 Access 로그 분류"""
        lines = sample.content.strip().split('\n')[:10]  # 처음 10줄 검사
        
        matched_patterns = []
        valid_lines = 0
        sample_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            sample_lines.append(line[:200])  # 샘플용으로 200자까지만
            
            for i, pattern in enumerate(self.PATTERNS):
                if re.match(pattern, line):
                    matched_patterns.append(f"pattern_{i}")
                    valid_lines += 1
                    break
        
        if valid_lines == 0:
            return None
        
        # 신뢰도 계산
        confidence = valid_lines / len([l for l in lines if l.strip()])
        
        # 필드 수 추정
        field_count = self._estimate_field_count(lines)
        
        return ClassificationResult(
            log_type=LogType.S3_ACCESS,
            confidence_score=confidence,
            matched_patterns=matched_patterns,
            field_count=field_count,
            sample_lines=sample_lines[:5]
        )
    
    def validate_format(self, sample: LogSample) -> List[str]:
        """S3 Access 로그 형식 검증"""
        errors = []
        lines = sample.content.strip().split('\n')[:20]  # 처음 20줄 검사
        
        valid_lines = 0
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 기본 패턴 검사
            if not re.match(self.PATTERNS[2], line):  # 가장 관대한 패턴 사용
                errors.append(f"Invalid S3 log format in line: {line[:100]}...")
                continue
            
            # 필드 수 검사
            fields = self._parse_s3_log_line(line)
            if len(fields) < 10:  # 최소 10개 필드는 있어야 함
                errors.append(f"Insufficient fields ({len(fields)}) in line: {line[:100]}...")
            
            valid_lines += 1
        
        if valid_lines == 0:
            errors.append("No valid S3 access log lines found")
        elif valid_lines / len([l for l in lines if l.strip()]) < 0.8:
            errors.append("Less than 80% of lines match S3 access log format")
        
        return errors
    
    def _estimate_field_count(self, lines: List[str]) -> int:
        """필드 수 추정"""
        field_counts = []
        
        for line in lines[:5]:  # 처음 5줄만 검사
            line = line.strip()
            if not line:
                continue
            
            fields = self._parse_s3_log_line(line)
            field_counts.append(len(fields))
        
        return max(field_counts) if field_counts else 0
    
    def _parse_s3_log_line(self, line: str) -> List[str]:
        """S3 로그 라인 파싱"""
        # 간단한 공백 기반 파싱 (실제로는 더 복잡한 파싱 필요)
        # 따옴표로 둘러싸인 필드 고려
        fields = []
        current_field = ""
        in_quotes = False
        
        i = 0
        while i < len(line):
            char = line[i]
            
            if char == '"' and (i == 0 or line[i-1] == ' '):
                in_quotes = True
                current_field += char
            elif char == '"' and in_quotes:
                in_quotes = False
                current_field += char
            elif char == ' ' and not in_quotes:
                if current_field:
                    fields.append(current_field)
                    current_field = ""
            else:
                current_field += char
            
            i += 1
        
        if current_field:
            fields.append(current_field)
        
        return fields


class CloudFrontLogClassifier(LogClassifier):
    """CloudFront 로그 분류기"""
    
    PATTERNS = [
        r'^#Version:\s+1\.0',
        r'^#Fields:\s+date\s+time\s+x-edge-location',
        r'^\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\s+\w{3}\d+',
        r'^\d{4}-\d{2}-\d{2}\t\d{2}:\d{2}:\d{2}\t\w{3}\d+',
    ]
    
    EXPECTED_FIELDS = [
        'date', 'time', 'x-edge-location', 'sc-bytes', 'c-ip',
        'cs-method', 'cs(Host)', 'cs-uri-stem', 'sc-status', 'cs(Referer)',
        'cs(User-Agent)', 'cs-uri-query', 'cs(Cookie)', 'x-edge-result-type',
        'x-edge-request-id', 'x-host-header', 'cs-protocol', 'cs-bytes',
        'time-taken', 'x-forwarded-for', 'ssl-protocol', 'ssl-cipher',
        'x-edge-response-result-type', 'cs-protocol-version'
    ]
    
    @property
    def supported_log_type(self) -> LogType:
        return LogType.CLOUDFRONT
    
    def classify(self, sample: LogSample) -> Optional[ClassificationResult]:
        """CloudFront 로그 분류"""
        lines = sample.content.strip().split('\n')
        
        # 헤더 라인 확인
        has_version_header = False
        has_fields_header = False
        data_lines = []
        matched_patterns = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if line.startswith('#Version:'):
                has_version_header = True
                matched_patterns.append("version_header")
            elif line.startswith('#Fields:'):
                has_fields_header = True
                matched_patterns.append("fields_header")
            elif not line.startswith('#'):
                data_lines.append(line)
        
        # 데이터 라인 패턴 검사
        valid_data_lines = 0
        sample_lines = []
        
        for line in data_lines[:10]:
            sample_lines.append(line[:200])
            
            # 날짜-시간 패턴 확인
            if re.match(r'^\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}', line) or \
               re.match(r'^\d{4}-\d{2}-\d{2}\t\d{2}:\d{2}:\d{2}', line):
                valid_data_lines += 1
                matched_patterns.append("data_line")
        
        # 신뢰도 계산
        confidence = 0.0
        if has_version_header:
            confidence += 0.3
        if has_fields_header:
            confidence += 0.3
        if valid_data_lines > 0 and data_lines:
            confidence += 0.4 * (valid_data_lines / len(data_lines))
        
        if confidence < 0.3:
            return None
        
        # 필드 수 추정
        field_count = self._estimate_cloudfront_field_count(data_lines)
        
        return ClassificationResult(
            log_type=LogType.CLOUDFRONT,
            confidence_score=confidence,
            matched_patterns=matched_patterns,
            field_count=field_count,
            sample_lines=sample_lines[:5]
        )
    
    def validate_format(self, sample: LogSample) -> List[str]:
        """CloudFront 로그 형식 검증"""
        errors = []
        lines = sample.content.strip().split('\n')
        
        # 헤더 검증
        has_version = any(line.startswith('#Version:') for line in lines)
        has_fields = any(line.startswith('#Fields:') for line in lines)
        
        if not has_version:
            errors.append("Missing CloudFront version header")
        if not has_fields:
            errors.append("Missing CloudFront fields header")
        
        # 데이터 라인 검증
        data_lines = [line for line in lines if not line.startswith('#') and line.strip()]
        valid_data_lines = 0
        
        for line in data_lines:
            if re.match(r'^\d{4}-\d{2}-\d{2}[\s\t]\d{2}:\d{2}:\d{2}', line):
                valid_data_lines += 1
            else:
                errors.append(f"Invalid CloudFront data line format: {line[:100]}...")
        
        if data_lines and valid_data_lines / len(data_lines) < 0.8:
            errors.append("Less than 80% of data lines match CloudFront format")
        
        return errors
    
    def _estimate_cloudfront_field_count(self, data_lines: List[str]) -> int:
        """CloudFront 필드 수 추정"""
        if not data_lines:
            return 0
        
        # 탭 또는 공백으로 구분된 필드 수 계산
        field_counts = []
        for line in data_lines[:5]:
            if '\t' in line:
                field_counts.append(len(line.split('\t')))
            else:
                field_counts.append(len(line.split()))
        
        return max(field_counts) if field_counts else 0


class ALBLogClassifier(LogClassifier):
    """ALB 로그 분류기"""
    
    PATTERNS = [
        r'^https?\s+\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z\s+app/',
        r'^h2\s+\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z\s+app/',
        r'^\w+\s+\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z\s+',
    ]
    
    EXPECTED_FIELDS = [
        'type', 'time', 'elb', 'client:port', 'target:port',
        'request_processing_time', 'target_processing_time', 'response_processing_time',
        'elb_status_code', 'target_status_code', 'received_bytes', 'sent_bytes',
        'request', 'user_agent', 'ssl_cipher', 'ssl_protocol',
        'target_group_arn', 'trace_id', 'domain_name', 'chosen_cert_arn',
        'matched_rule_priority', 'request_creation_time', 'actions_executed',
        'redirect_url', 'error_reason', 'target:port_list', 'target_status_code_list',
        'classification', 'classification_reason'
    ]
    
    @property
    def supported_log_type(self) -> LogType:
        return LogType.ALB
    
    def classify(self, sample: LogSample) -> Optional[ClassificationResult]:
        """ALB 로그 분류"""
        lines = sample.content.strip().split('\n')[:10]
        
        matched_patterns = []
        valid_lines = 0
        sample_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            sample_lines.append(line[:200])
            
            for i, pattern in enumerate(self.PATTERNS):
                if re.match(pattern, line):
                    matched_patterns.append(f"pattern_{i}")
                    valid_lines += 1
                    break
        
        if valid_lines == 0:
            return None
        
        confidence = valid_lines / len([l for l in lines if l.strip()])
        field_count = self._estimate_alb_field_count(lines)
        
        return ClassificationResult(
            log_type=LogType.ALB,
            confidence_score=confidence,
            matched_patterns=matched_patterns,
            field_count=field_count,
            sample_lines=sample_lines[:5]
        )
    
    def validate_format(self, sample: LogSample) -> List[str]:
        """ALB 로그 형식 검증"""
        errors = []
        lines = sample.content.strip().split('\n')[:20]
        
        valid_lines = 0
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # ALB 로그는 특정 패턴으로 시작해야 함
            if not any(re.match(pattern, line) for pattern in self.PATTERNS):
                errors.append(f"Invalid ALB log format in line: {line[:100]}...")
                continue
            
            # 필드 수 검사 (ALB는 최소 20개 필드)
            fields = line.split(' ')
            if len(fields) < 20:
                errors.append(f"Insufficient fields ({len(fields)}) in ALB log line")
            
            valid_lines += 1
        
        if valid_lines == 0:
            errors.append("No valid ALB log lines found")
        elif valid_lines / len([l for l in lines if l.strip()]) < 0.8:
            errors.append("Less than 80% of lines match ALB log format")
        
        return errors
    
    def _estimate_alb_field_count(self, lines: List[str]) -> int:
        """ALB 필드 수 추정"""
        field_counts = []
        
        for line in lines[:5]:
            line = line.strip()
            if not line:
                continue
            
            # ALB 로그는 공백으로 구분되지만 따옴표 내 공백은 제외
            fields = self._parse_alb_log_line(line)
            field_counts.append(len(fields))
        
        return max(field_counts) if field_counts else 0
    
    def _parse_alb_log_line(self, line: str) -> List[str]:
        """ALB 로그 라인 파싱"""
        fields = []
        current_field = ""
        in_quotes = False
        
        for char in line:
            if char == '"':
                in_quotes = not in_quotes
                current_field += char
            elif char == ' ' and not in_quotes:
                if current_field:
                    fields.append(current_field)
                    current_field = ""
            else:
                current_field += char
        
        if current_field:
            fields.append(current_field)
        
        return fields


class VPCFlowLogClassifier(LogClassifier):
    """VPC Flow 로그 분류기"""
    
    PATTERNS = [
        r'^2\s+\d+\s+eni-[a-f0-9]+\s+',
        r'^version\s+account-id\s+interface-id',
        r'^\d+\s+\d+\s+eni-\w+\s+[\d\.]+\s+[\d\.]+',
    ]
    
    EXPECTED_FIELDS = [
        'version', 'account-id', 'interface-id', 'srcaddr', 'dstaddr',
        'srcport', 'dstport', 'protocol', 'packets', 'bytes',
        'windowstart', 'windowend', 'action', 'flowlogstatus'
    ]
    
    @property
    def supported_log_type(self) -> LogType:
        return LogType.VPC_FLOW
    
    def classify(self, sample: LogSample) -> Optional[ClassificationResult]:
        """VPC Flow 로그 분류"""
        lines = sample.content.strip().split('\n')
        
        # 헤더 라인 확인
        has_header = False
        data_lines = []
        matched_patterns = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if line.startswith('version account-id'):
                has_header = True
                matched_patterns.append("header")
            elif not line.startswith('version') or has_header:
                data_lines.append(line)
        
        # 데이터 라인 패턴 검사
        valid_data_lines = 0
        sample_lines = []
        
        for line in data_lines[:10]:
            sample_lines.append(line[:200])
            
            for i, pattern in enumerate(self.PATTERNS):
                if re.match(pattern, line):
                    matched_patterns.append(f"pattern_{i}")
                    valid_data_lines += 1
                    break
        
        if valid_data_lines == 0:
            return None
        
        confidence = valid_data_lines / len(data_lines) if data_lines else 0
        if has_header:
            confidence += 0.2
        
        field_count = self._estimate_vpc_field_count(data_lines)
        
        return ClassificationResult(
            log_type=LogType.VPC_FLOW,
            confidence_score=confidence,
            matched_patterns=matched_patterns,
            field_count=field_count,
            sample_lines=sample_lines[:5]
        )
    
    def validate_format(self, sample: LogSample) -> List[str]:
        """VPC Flow 로그 형식 검증"""
        errors = []
        lines = sample.content.strip().split('\n')
        
        # 헤더 확인 (선택사항)
        data_lines = [line for line in lines if line.strip() and not line.startswith('version account-id')]
        
        valid_lines = 0
        for line in data_lines:
            line = line.strip()
            if not line:
                continue
            
            # VPC Flow 로그 패턴 확인
            if not any(re.match(pattern, line) for pattern in self.PATTERNS):
                errors.append(f"Invalid VPC Flow log format in line: {line[:100]}...")
                continue
            
            # 필드 수 검사 (최소 14개 필드)
            fields = line.split()
            if len(fields) < 14:
                errors.append(f"Insufficient fields ({len(fields)}) in VPC Flow log line")
            
            valid_lines += 1
        
        if valid_lines == 0:
            errors.append("No valid VPC Flow log lines found")
        elif data_lines and valid_lines / len(data_lines) < 0.8:
            errors.append("Less than 80% of lines match VPC Flow log format")
        
        return errors
    
    def _estimate_vpc_field_count(self, lines: List[str]) -> int:
        """VPC Flow 필드 수 추정"""
        field_counts = []
        
        for line in lines[:5]:
            line = line.strip()
            if not line:
                continue
            
            fields = line.split()
            field_counts.append(len(fields))
        
        return max(field_counts) if field_counts else 0


class CloudTrailLogClassifier(LogClassifier):
    """CloudTrail 로그 분류기 (JSON 형식)"""
    
    REQUIRED_FIELDS = ['Records', 'eventVersion', 'eventSource', 'eventName']
    
    @property
    def supported_log_type(self) -> LogType:
        return LogType.CLOUDTRAIL
    
    def classify(self, sample: LogSample) -> Optional[ClassificationResult]:
        """CloudTrail 로그 분류"""
        try:
            content = sample.content.strip()
            
            # 불완전한 JSON일 수 있으므로 부분 매칭도 시도
            matched_patterns = []
            confidence = 0.0
            
            # Records 키워드 확인 (JSON 파싱 전)
            if '"Records"' in content and '[' in content:
                matched_patterns.append("records_keyword")
                confidence += 0.3
            
            # CloudTrail 특징적인 필드 확인
            cloudtrail_keywords = ['eventVersion', 'eventSource', 'eventName', 'userIdentity']
            found_keywords = sum(1 for kw in cloudtrail_keywords if f'"{kw}"' in content)
            if found_keywords >= 2:
                matched_patterns.append("cloudtrail_fields")
                confidence += 0.3 * (found_keywords / len(cloudtrail_keywords))
            
            # amazonaws.com 확인
            if '.amazonaws.com' in content:
                matched_patterns.append("aws_domain")
                confidence += 0.2
            
            # JSON 파싱 시도 (완전한 JSON인 경우)
            try:
                data = json.loads(content)
                
                # Records 배열 확인
                if isinstance(data, dict) and 'Records' in data:
                    matched_patterns.append("valid_json_records")
                    confidence += 0.3
                    
                    records = data['Records']
                    if isinstance(records, list) and len(records) > 0:
                        # 첫 번째 레코드 검사
                        first_record = records[0]
                        
                        # 필수 필드 확인
                        required_found = 0
                        for field in self.REQUIRED_FIELDS[1:]:  # Records 제외
                            if field in first_record:
                                required_found += 1
                        
                        if required_found >= 2:
                            matched_patterns.append("required_fields")
                            confidence += 0.2
            except (json.JSONDecodeError, ValueError):
                # 불완전한 JSON이지만 키워드 매칭으로 충분히 판단 가능
                pass
            
            if confidence < 0.5:
                return None
            
            # 샘플 라인 생성
            sample_lines = [content[:200]]
            
            return ClassificationResult(
                log_type=LogType.CLOUDTRAIL,
                confidence_score=min(confidence, 1.0),
                matched_patterns=matched_patterns,
                field_count=len(self.REQUIRED_FIELDS),
                sample_lines=sample_lines
            )
            
        except Exception as e:
            logger.warning(f"CloudTrail 분류 오류: {str(e)}")
            return None
    
    def validate_format(self, sample: LogSample) -> List[str]:
        """CloudTrail 로그 형식 검증"""
        errors = []
        
        try:
            data = json.loads(sample.content.strip())
            
            # 기본 구조 검증
            if not isinstance(data, dict):
                errors.append("CloudTrail log must be a JSON object")
                return errors
            
            if 'Records' not in data:
                errors.append("Missing 'Records' field in CloudTrail log")
                return errors
            
            records = data['Records']
            if not isinstance(records, list):
                errors.append("'Records' field must be an array")
                return errors
            
            if len(records) == 0:
                errors.append("'Records' array is empty")
                return errors
            
            # 각 레코드 검증
            for i, record in enumerate(records[:5]):  # 처음 5개만 검사
                if not isinstance(record, dict):
                    errors.append(f"Record {i} is not a JSON object")
                    continue
                
                # 필수 필드 확인
                for field in self.REQUIRED_FIELDS[1:]:
                    if field not in record:
                        errors.append(f"Missing required field '{field}' in record {i}")
                
                # eventSource 형식 확인
                if 'eventSource' in record:
                    event_source = record['eventSource']
                    if not isinstance(event_source, str) or not event_source.endswith('.amazonaws.com'):
                        errors.append(f"Invalid eventSource format in record {i}: {event_source}")
        
        except (json.JSONDecodeError, ValueError) as e:
            errors.append(f"Invalid JSON format: {str(e)}")
        
        return errors


class LogFormatClassifier:
    """통합 로그 형식 분류기"""
    
    def __init__(self):
        self.classifiers = [
            S3AccessLogClassifier(),
            CloudFrontLogClassifier(),
            ALBLogClassifier(),
            VPCFlowLogClassifier(),
            CloudTrailLogClassifier(),
        ]
        self.custom_formats: Dict[str, CustomLogFormat] = {}
    
    def classify_log_sample(self, sample: LogSample) -> Optional[ClassificationResult]:
        """로그 샘플 분류"""
        best_result = None
        best_confidence = 0.0
        
        # 기본 분류기들 시도
        for classifier in self.classifiers:
            try:
                result = classifier.classify(sample)
                if result and result.confidence_score > best_confidence:
                    best_result = result
                    best_confidence = result.confidence_score
            except Exception as e:
                logger.warning(f"분류기 {classifier.__class__.__name__} 오류: {str(e)}")
        
        # 사용자 정의 형식 시도
        if best_confidence < 0.8:  # 기본 분류기 신뢰도가 낮으면
            custom_result = self._try_custom_formats(sample)
            if custom_result and custom_result.confidence_score > best_confidence:
                best_result = custom_result
        
        return best_result
    
    def validate_log_format(self, sample: LogSample, expected_type: LogType) -> List[str]:
        """특정 로그 타입으로 검증"""
        for classifier in self.classifiers:
            if classifier.supported_log_type == expected_type:
                return classifier.validate_format(sample)
        
        return [f"No validator found for log type: {expected_type}"]
    
    def add_custom_format(self, custom_format: CustomLogFormat) -> None:
        """사용자 정의 로그 형식 추가"""
        self.custom_formats[custom_format.name] = custom_format
        logger.info(f"사용자 정의 로그 형식 추가: {custom_format.name}")
    
    def get_supported_log_types(self) -> List[LogType]:
        """지원하는 로그 타입 목록"""
        return [classifier.supported_log_type for classifier in self.classifiers]
    
    def get_format_examples(self) -> Dict[LogType, str]:
        """로그 타입별 예시"""
        examples = {
            LogType.S3_ACCESS: 'bucket_owner bucket [timestamp] remote_ip requester request_id operation key "request_uri" http_status error_code bytes_sent object_size total_time turn_around_time "referer" "user_agent" version_id host_id signature_version cipher_suite authentication_type host_header tls_version access_point_arn acl_required',
            
            LogType.CLOUDFRONT: '#Version: 1.0\n#Fields: date time x-edge-location sc-bytes c-ip cs-method cs(Host) cs-uri-stem sc-status cs(Referer) cs(User-Agent)\n2023-01-01 12:00:00 LAX3 1234 192.168.1.1 GET example.com /index.html 200 - Mozilla/5.0',
            
            LogType.ALB: 'http 2023-01-01T12:00:00.123456Z app/my-loadbalancer/50dc6c495c0c9188 192.168.1.1:12345 10.0.0.1:80 0.000 0.001 0.000 200 200 0 29 "GET http://example.com:80/ HTTP/1.1" "Mozilla/5.0" - -',
            
            LogType.VPC_FLOW: 'version account-id interface-id srcaddr dstaddr srcport dstport protocol packets bytes windowstart windowend action flowlogstatus\n2 123456789012 eni-1235b8ca 172.31.16.139 172.31.16.21 20641 22 6 20 4249 1418530010 1418530070 ACCEPT OK',
            
            LogType.CLOUDTRAIL: '{"Records": [{"eventVersion": "1.05", "userIdentity": {"type": "IAMUser"}, "eventTime": "2023-01-01T12:00:00Z", "eventSource": "s3.amazonaws.com", "eventName": "GetObject"}]}'
        }
        return examples
    
    def _try_custom_formats(self, sample: LogSample) -> Optional[ClassificationResult]:
        """사용자 정의 형식으로 분류 시도"""
        best_result = None
        best_confidence = 0.0
        
        for format_name, custom_format in self.custom_formats.items():
            try:
                confidence = self._match_custom_format(sample, custom_format)
                if confidence > best_confidence:
                    best_confidence = confidence
                    best_result = ClassificationResult(
                        log_type=LogType.S3_ACCESS,  # 임시로 S3_ACCESS 사용
                        confidence_score=confidence,
                        matched_patterns=[f"custom_{format_name}"],
                        field_count=len(custom_format.field_names),
                        sample_lines=[sample.content[:200]]
                    )
            except Exception as e:
                logger.warning(f"사용자 정의 형식 {format_name} 매칭 오류: {str(e)}")
        
        return best_result
    
    def _match_custom_format(self, sample: LogSample, custom_format: CustomLogFormat) -> float:
        """사용자 정의 형식 매칭"""
        lines = sample.content.strip().split('\n')[:10]
        
        matched_lines = 0
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            for pattern in custom_format.patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    matched_lines += 1
                    break
        
        return matched_lines / len([l for l in lines if l.strip()]) if lines else 0.0


class LogSampleExtractor:
    """로그 샘플 추출기"""
    
    def __init__(self, max_sample_size: int = 16384):
        self.max_sample_size = max_sample_size
    
    def extract_sample(self, bucket_name: str, key: str) -> Optional[LogSample]:
        """S3에서 로그 샘플 추출"""
        try:
            # 파일 크기 확인
            response = s3_client.client.head_object(Bucket=bucket_name, Key=key)
            file_size = response['ContentLength']
            
            # 샘플 크기 결정
            sample_size = min(self.max_sample_size, file_size)
            
            # 샘플 내용 읽기
            response = s3_client.client.get_object(
                Bucket=bucket_name,
                Key=key,
                Range=f'bytes=0-{sample_size - 1}'
            )
            
            content_bytes = response['Body'].read()
            is_compressed = False
            
            # 압축 파일 처리
            if key.endswith('.gz'):
                try:
                    content_bytes = gzip.decompress(content_bytes)
                    is_compressed = True
                except Exception as e:
                    logger.warning(f"gzip 압축 해제 실패 {key}: {str(e)}")
                    return None
            
            # 텍스트 디코딩
            encoding = 'utf-8'
            try:
                content = content_bytes.decode('utf-8')
            except UnicodeDecodeError:
                try:
                    content = content_bytes.decode('latin-1')
                    encoding = 'latin-1'
                except UnicodeDecodeError:
                    logger.warning(f"텍스트 디코딩 실패 {key}")
                    return None
            
            return LogSample(
                content=content,
                source_key=key,
                sample_size=len(content_bytes),
                encoding=encoding,
                is_compressed=is_compressed
            )
            
        except Exception as e:
            logger.error(f"로그 샘플 추출 실패 {key}: {str(e)}")
            return None