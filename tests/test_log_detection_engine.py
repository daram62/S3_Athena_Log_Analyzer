"""로그 탐지 및 분류 엔진 테스트"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import json
import gzip

from src.services.log_scanner import (
    LogFileScanner, LogPatternMatcher, LogMetadataCollector,
    ScanResult, LogFileInfo, FileType
)
from src.services.log_classifier import (
    LogFormatClassifier, S3AccessLogClassifier, CloudFrontLogClassifier,
    ALBLogClassifier, VPCFlowLogClassifier, CloudTrailLogClassifier,
    LogSample, ClassificationResult, CustomLogFormat
)
from src.services.log_metadata_analyzer import (
    LogMetadataAnalyzer, TimeRangeAnalysis, VolumeAnalysis,
    QualityMetrics, PartitioningRecommendation, PartitionStrategy,
    LogQuality, MetadataAnalysisResult
)
from src.models.log_configuration import LogType


class TestLogPatternMatcher:
    """로그 패턴 매처 테스트"""
    
    def test_s3_access_log_detection(self):
        """S3 Access 로그 탐지 테스트"""
        s3_log_content = """79a59df900b949e55d96a1e698fbacedfd6e09d98eacf8f8d5218e7cd47ef2be mybucket [06/Feb/2019:00:00:38 +0000] 192.0.2.3 79a59df900b949e55d96a1e698fbacedfd6e09d98eacf8f8d5218e7cd47ef2be 3E57427F3EXAMPLE REST.GET.VERSIONING - "GET /mybucket?versioning HTTP/1.1" 200 - 113 - 7 - "-" "S3Console/0.4" - s9lzHYrFp76ZVxRcpX9+5cjAnEH2ROuNkd2BHfIa6UkFVdtjf5mKR3/eTPFvsiP/XV/VLi31234= SigV2 ECDHE-RSA-AES128-GCM-SHA256 AuthHeader mybucket.s3.amazonaws.com TLSV1.1"""
        
        log_type, confidence = LogPatternMatcher.detect_log_type(s3_log_content)
        
        assert log_type == LogType.S3_ACCESS
        assert confidence > 0.8
    
    def test_cloudfront_log_detection(self):
        """CloudFront 로그 탐지 테스트"""
        cloudfront_log_content = """#Version: 1.0
#Fields: date time x-edge-location sc-bytes c-ip cs-method cs(Host) cs-uri-stem sc-status cs(Referer) cs(User-Agent) cs-uri-query cs(Cookie) x-edge-result-type x-edge-request-id x-host-header cs-protocol cs-bytes time-taken x-forwarded-for ssl-protocol ssl-cipher x-edge-response-result-type cs-protocol-version fle-status fle-encrypted-fields c-port time-to-first-byte x-edge-detailed-result-type sc-content-type sc-content-len sc-range-start sc-range-end
2019-12-04	21:02:31	LAX1	392	192.0.2.100	GET	d111111abcdef8.cloudfront.net	/index.html	200	-	Mozilla/5.0%20(Windows%20NT%2010.0;%20Win64;%20x64)%20AppleWebKit/537.36%20(KHTML,%20like%20Gecko)%20Chrome/78.0.3904.108%20Safari/537.36	-	-	Hit	SOX4xwn4XV6Q4rgb7XiVGOHms_BGlTAC4KyHmureZmBNrjGdRLiNIQ==	d111111abcdef8.cloudfront.net	https	23	0.001	-	TLSv1.2	ECDHE-RSA-AES128-GCM-SHA256	Hit	HTTP/2.0	-	-	11040	0.001	Hit	text/html	78	-	-"""
        
        log_type, confidence = LogPatternMatcher.detect_log_type(cloudfront_log_content)
        
        assert log_type == LogType.CLOUDFRONT
        assert confidence > 0.8
    
    def test_alb_log_detection(self):
        """ALB 로그 탐지 테스트"""
        alb_log_content = """http 2018-07-02T22:22:58.364000Z app/my-loadbalancer/50dc6c495c0c9188 192.168.131.39:2817 10.0.0.1:80 0.000 0.001 0.000 200 200 34 366 "GET http://www.example.com:80/ HTTP/1.1" "curl/7.46.0" - - arn:aws:elasticloadbalancing:us-east-2:123456789012:targetgroup/my-targets/73e2d6bc24d8a067 "Root=1-58337262-36d228ad5d99923122bbe354" "-" "-" 0 2018-07-02T22:22:58.364000Z "forward" "-" "-" 10.0.0.1:80 200 "-" "-"""
        
        log_type, confidence = LogPatternMatcher.detect_log_type(alb_log_content)
        
        assert log_type == LogType.ALB
        assert confidence > 0.8
    
    def test_vpc_flow_log_detection(self):
        """VPC Flow 로그 탐지 테스트"""
        vpc_flow_content = """version account-id interface-id srcaddr dstaddr srcport dstport protocol packets bytes windowstart windowend action flowlogstatus
2 123456789010 eni-1235b8ca123456789 172.31.16.139 172.31.16.21 20641 22 6 20 4249 1418530010 1418530070 ACCEPT OK
2 123456789010 eni-1235b8ca123456789 172.31.9.69 172.31.9.12 49761 3389 6 20 4249 1418530010 1418530070 REJECT OK"""
        
        log_type, confidence = LogPatternMatcher.detect_log_type(vpc_flow_content)
        
        assert log_type == LogType.VPC_FLOW
        assert confidence > 0.8
    
    def test_cloudtrail_log_detection(self):
        """CloudTrail 로그 탐지 테스트"""
        cloudtrail_content = """{
    "Records": [
        {
            "eventVersion": "1.05",
            "userIdentity": {
                "type": "IAMUser",
                "principalId": "AIDACKCEVSQ6C2EXAMPLE",
                "arn": "arn:aws:iam::123456789012:user/Mary_Major",
                "accountId": "123456789012",
                "userName": "Mary_Major"
            },
            "eventTime": "2019-06-19T00:46:59Z",
            "eventSource": "s3.amazonaws.com",
            "eventName": "GetObject",
            "awsRegion": "us-west-2"
        }
    ]
}"""
        
        log_type, confidence = LogPatternMatcher.detect_log_type(cloudtrail_content)
        
        assert log_type == LogType.CLOUDTRAIL
        assert confidence > 0.8


class TestLogFileScanner:
    """로그 파일 스캐너 테스트"""
    
    @patch('src.services.log_scanner.s3_client')
    def test_scan_bucket_prefix(self, mock_s3_client):
        """버킷 접두사 스캔 테스트"""
        # Mock S3 응답
        mock_s3_client.client.list_objects_v2.return_value = {
            'Contents': [
                {
                    'Key': 'logs/access.log',
                    'Size': 1024,
                    'LastModified': datetime.now()
                },
                {
                    'Key': 'logs/error.log',
                    'Size': 2048,
                    'LastModified': datetime.now()
                }
            ],
            'IsTruncated': False
        }
        
        mock_s3_client.client.get_object.return_value = {
            'Body': Mock(read=lambda: b'sample log content')
        }
        
        scanner = LogFileScanner()
        result = scanner.scan_bucket_prefix('test-bucket', 'logs/')
        
        assert isinstance(result, ScanResult)
        assert result.bucket_name == 'test-bucket'
        assert result.prefix == 'logs/'
        assert result.total_files == 2
        assert len(result.log_files) <= 2
    
    def test_is_potential_log_file(self):
        """로그 파일 가능성 확인 테스트"""
        scanner = LogFileScanner()
        
        # 로그 파일로 인식되어야 하는 경우
        assert scanner._is_potential_log_file('access.log')
        assert scanner._is_potential_log_file('error.txt')
        assert scanner._is_potential_log_file('application.log.gz')
        assert scanner._is_potential_log_file('logs/2023-01-01.log')
        assert scanner._is_potential_log_file('cloudfront/distribution.log')
        
        # 로그 파일로 인식되지 않아야 하는 경우
        assert not scanner._is_potential_log_file('image.jpg')
        assert not scanner._is_potential_log_file('document.pdf')
        assert not scanner._is_potential_log_file('config.xml')
    
    def test_determine_file_type(self):
        """파일 타입 결정 테스트"""
        scanner = LogFileScanner()
        
        assert scanner._determine_file_type('access.log') == FileType.LOG
        assert scanner._determine_file_type('error.txt') == FileType.LOG
        assert scanner._determine_file_type('logs.gz') == FileType.COMPRESSED
        assert scanner._determine_file_type('archive.zip') == FileType.ARCHIVE
        assert scanner._determine_file_type('data.csv') == FileType.OTHER


class TestLogFormatClassifier:
    """로그 형식 분류기 테스트"""
    
    def test_s3_access_classifier(self):
        """S3 Access 로그 분류기 테스트"""
        classifier = S3AccessLogClassifier()
        
        s3_sample = LogSample(
            content="""79a59df900b949e55d96a1e698fbacedfd6e09d98eacf8f8d5218e7cd47ef2be mybucket [06/Feb/2019:00:00:38 +0000] 192.0.2.3 79a59df900b949e55d96a1e698fbacedfd6e09d98eacf8f8d5218e7cd47ef2be 3E57427F3EXAMPLE REST.GET.VERSIONING - "GET /mybucket?versioning HTTP/1.1" 200 - 113 - 7 - "-" "S3Console/0.4" - s9lzHYrFp76ZVxRcpX9+5cjAnEH2ROuNkd2BHfIa6UkFVdtjf5mKR3/eTPFvsiP/XV/VLi31234= SigV2 ECDHE-RSA-AES128-GCM-SHA256 AuthHeader mybucket.s3.amazonaws.com TLSV1.1""",
            source_key="access.log",
            sample_size=1000
        )
        
        result = classifier.classify(s3_sample)
        
        assert result is not None
        assert result.log_type == LogType.S3_ACCESS
        assert result.confidence_score > 0.8
        assert len(result.matched_patterns) > 0
        
        # 검증 테스트
        errors = classifier.validate_format(s3_sample)
        assert len(errors) == 0
    
    def test_cloudfront_classifier(self):
        """CloudFront 로그 분류기 테스트"""
        classifier = CloudFrontLogClassifier()
        
        cf_sample = LogSample(
            content="""#Version: 1.0
#Fields: date time x-edge-location sc-bytes c-ip cs-method cs(Host) cs-uri-stem sc-status cs(Referer) cs(User-Agent)
2019-12-04	21:02:31	LAX1	392	192.0.2.100	GET	d111111abcdef8.cloudfront.net	/index.html	200	-	Mozilla/5.0""",
            source_key="cloudfront.log",
            sample_size=1000
        )
        
        result = classifier.classify(cf_sample)
        
        assert result is not None
        assert result.log_type == LogType.CLOUDFRONT
        assert result.confidence_score > 0.8
        
        # 검증 테스트
        errors = classifier.validate_format(cf_sample)
        assert len(errors) == 0
    
    def test_cloudtrail_classifier(self):
        """CloudTrail 로그 분류기 테스트"""
        classifier = CloudTrailLogClassifier()
        
        ct_sample = LogSample(
            content="""{
    "Records": [
        {
            "eventVersion": "1.05",
            "userIdentity": {"type": "IAMUser"},
            "eventTime": "2019-06-19T00:46:59Z",
            "eventSource": "s3.amazonaws.com",
            "eventName": "GetObject"
        }
    ]
}""",
            source_key="cloudtrail.json",
            sample_size=1000
        )
        
        result = classifier.classify(ct_sample)
        
        assert result is not None
        assert result.log_type == LogType.CLOUDTRAIL
        assert result.confidence_score > 0.8
        
        # 검증 테스트
        errors = classifier.validate_format(ct_sample)
        assert len(errors) == 0
    
    def test_integrated_classifier(self):
        """통합 분류기 테스트"""
        classifier = LogFormatClassifier()
        
        # S3 로그 샘플
        s3_sample = LogSample(
            content="bucket_owner bucket [timestamp] ip requester request_id operation key request_uri status error bytes",
            source_key="s3.log",
            sample_size=100
        )
        
        result = classifier.classify_log_sample(s3_sample)
        assert result is not None
        
        # 지원하는 로그 타입 확인
        supported_types = classifier.get_supported_log_types()
        assert LogType.S3_ACCESS in supported_types
        assert LogType.CLOUDFRONT in supported_types
        assert LogType.ALB in supported_types
        assert LogType.VPC_FLOW in supported_types
        assert LogType.CLOUDTRAIL in supported_types
    
    def test_custom_format_support(self):
        """사용자 정의 형식 지원 테스트"""
        classifier = LogFormatClassifier()
        
        custom_format = CustomLogFormat(
            name="custom_app_log",
            description="Custom application log format",
            patterns=[r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} \[INFO\]'],
            field_separator=" ",
            field_names=["timestamp", "level", "message"],
            sample_line="2023-01-01 12:00:00 [INFO] Application started",
            created_by="test_user",
            created_at=datetime.now()
        )
        
        classifier.add_custom_format(custom_format)
        assert "custom_app_log" in classifier.custom_formats


class TestLogMetadataAnalyzer:
    """로그 메타데이터 분석기 테스트"""
    
    def create_sample_scan_result(self) -> ScanResult:
        """샘플 스캔 결과 생성"""
        log_files = []
        base_date = datetime.now() - timedelta(days=30)
        
        for i in range(10):
            log_files.append(LogFileInfo(
                key=f"logs/access-{i}.log",
                size=1024 * 1024 * (i + 1),  # 1MB ~ 10MB
                last_modified=base_date + timedelta(days=i * 3),
                file_type=FileType.LOG,
                detected_log_type=LogType.S3_ACCESS,
                confidence_score=0.9,
                sample_content="sample log content"
            ))
        
        return ScanResult(
            bucket_name="test-bucket",
            prefix="logs/",
            total_files=10,
            total_size=sum(f.size for f in log_files),
            log_files=log_files,
            scan_duration=5.0,
            date_range=(base_date, base_date + timedelta(days=27)),
            detected_log_types={LogType.S3_ACCESS: 10}
        )
    
    def test_analyze_logs(self):
        """로그 분석 테스트"""
        analyzer = LogMetadataAnalyzer()
        scan_result = self.create_sample_scan_result()
        
        analysis_result = analyzer.analyze_logs(scan_result)
        
        assert isinstance(analysis_result, MetadataAnalysisResult)
        assert analysis_result.scan_result == scan_result
        assert isinstance(analysis_result.time_analysis, TimeRangeAnalysis)
        assert isinstance(analysis_result.volume_analysis, VolumeAnalysis)
        assert isinstance(analysis_result.quality_metrics, QualityMetrics)
        assert isinstance(analysis_result.partitioning_recommendation, PartitioningRecommendation)
    
    def test_time_range_analysis(self):
        """시간 범위 분석 테스트"""
        analyzer = LogMetadataAnalyzer()
        scan_result = self.create_sample_scan_result()
        
        time_analysis = analyzer._analyze_time_range(scan_result)
        
        assert time_analysis.total_days > 0
        assert time_analysis.active_days > 0
        assert time_analysis.coverage_percentage <= 100
        assert isinstance(time_analysis.daily_file_counts, dict)
    
    def test_volume_analysis(self):
        """볼륨 분석 테스트"""
        analyzer = LogMetadataAnalyzer()
        scan_result = self.create_sample_scan_result()
        
        volume_analysis = analyzer._analyze_volume_patterns(scan_result)
        
        assert volume_analysis.total_size_gb > 0
        assert volume_analysis.total_files == 10
        assert volume_analysis.avg_file_size_mb > 0
        assert volume_analysis.size_consistency_score >= 0
        assert volume_analysis.growth_trend in ["increasing", "decreasing", "stable"]
    
    def test_quality_analysis(self):
        """품질 분석 테스트"""
        analyzer = LogMetadataAnalyzer()
        scan_result = self.create_sample_scan_result()
        
        quality_metrics = analyzer._analyze_log_quality(scan_result, detailed_analysis=True)
        
        assert 0 <= quality_metrics.overall_score <= 100
        assert 0 <= quality_metrics.detection_rate <= 1
        assert 0 <= quality_metrics.avg_confidence <= 1
        assert 0 <= quality_metrics.format_consistency <= 1
        assert isinstance(quality_metrics.issues, list)
        assert isinstance(quality_metrics.recommendations, list)
        assert quality_metrics.quality_grade in [LogQuality.EXCELLENT, LogQuality.GOOD, LogQuality.FAIR, LogQuality.POOR]
    
    def test_partitioning_recommendation(self):
        """파티셔닝 추천 테스트"""
        analyzer = LogMetadataAnalyzer()
        scan_result = self.create_sample_scan_result()
        
        time_analysis = analyzer._analyze_time_range(scan_result)
        volume_analysis = analyzer._analyze_volume_patterns(scan_result)
        
        partitioning_rec = analyzer._recommend_partitioning(
            scan_result, time_analysis, volume_analysis
        )
        
        assert partitioning_rec.strategy in [
            PartitionStrategy.NONE, PartitionStrategy.DAILY, 
            PartitionStrategy.MONTHLY, PartitionStrategy.YEARLY
        ]
        assert partitioning_rec.estimated_partitions >= 1
        assert partitioning_rec.partition_size_gb >= 0
        assert len(partitioning_rec.reasoning) > 0
    
    def test_analysis_result_serialization(self):
        """분석 결과 직렬화 테스트"""
        analyzer = LogMetadataAnalyzer()
        scan_result = self.create_sample_scan_result()
        
        analysis_result = analyzer.analyze_logs(scan_result)
        result_dict = analysis_result.to_dict()
        
        assert isinstance(result_dict, dict)
        assert 'analysis_timestamp' in result_dict
        assert 'time_analysis' in result_dict
        assert 'volume_analysis' in result_dict
        assert 'quality_metrics' in result_dict
        assert 'partitioning_recommendation' in result_dict
        assert 'log_type_distribution' in result_dict


class TestLogMetadataCollector:
    """로그 메타데이터 수집기 테스트"""
    
    def test_collect_enhanced_metadata(self):
        """향상된 메타데이터 수집 테스트"""
        scanner = LogFileScanner()
        collector = LogMetadataCollector(scanner)
        
        # 샘플 스캔 결과 생성
        log_files = [
            LogFileInfo(
                key="logs/access.log",
                size=1024 * 1024,
                last_modified=datetime.now(),
                file_type=FileType.LOG,
                detected_log_type=LogType.S3_ACCESS,
                confidence_score=0.9
            )
        ]
        
        scan_result = ScanResult(
            bucket_name="test-bucket",
            prefix="logs/",
            total_files=1,
            total_size=1024 * 1024,
            log_files=log_files,
            scan_duration=1.0,
            date_range=(datetime.now() - timedelta(days=1), datetime.now()),
            detected_log_types={LogType.S3_ACCESS: 1}
        )
        
        metadata = collector.collect_enhanced_metadata(scan_result)
        
        assert 'scan_summary' in metadata
        assert 'file_distribution' in metadata
        assert 'temporal_analysis' in metadata
        assert 'size_analysis' in metadata
        assert 'quality_assessment' in metadata
        assert 'partitioning_recommendations' in metadata


@pytest.fixture
def sample_log_contents():
    """샘플 로그 내용"""
    return {
        's3_access': """79a59df900b949e55d96a1e698fbacedfd6e09d98eacf8f8d5218e7cd47ef2be mybucket [06/Feb/2019:00:00:38 +0000] 192.0.2.3 79a59df900b949e55d96a1e698fbacedfd6e09d98eacf8f8d5218e7cd47ef2be 3E57427F3EXAMPLE REST.GET.VERSIONING - "GET /mybucket?versioning HTTP/1.1" 200 - 113 - 7 - "-" "S3Console/0.4" - s9lzHYrFp76ZVxRcpX9+5cjAnEH2ROuNkd2BHfIa6UkFVdtjf5mKR3/eTPFvsiP/XV/VLi31234= SigV2 ECDHE-RSA-AES128-GCM-SHA256 AuthHeader mybucket.s3.amazonaws.com TLSV1.1""",
        
        'cloudfront': """#Version: 1.0
#Fields: date time x-edge-location sc-bytes c-ip cs-method cs(Host) cs-uri-stem sc-status cs(Referer) cs(User-Agent)
2019-12-04	21:02:31	LAX1	392	192.0.2.100	GET	d111111abcdef8.cloudfront.net	/index.html	200	-	Mozilla/5.0""",
        
        'alb': 'http 2018-07-02T22:22:58.364000Z app/my-loadbalancer/50dc6c495c0c9188 192.168.131.39:2817 10.0.0.1:80 0.000 0.001 0.000 200 200 34 366 "GET http://www.example.com:80/ HTTP/1.1" "curl/7.46.0" - - arn:aws:elasticloadbalancing:us-east-2:123456789012:targetgroup/my-targets/73e2d6bc24d8a067 "Root=1-58337262-36d228ad5d99923122bbe354" "-" "-" 0 2018-07-02T22:22:58.364000Z "forward" "-" "-" 10.0.0.1:80 200 "-" "-"',
        
        'vpc_flow': """version account-id interface-id srcaddr dstaddr srcport dstport protocol packets bytes windowstart windowend action flowlogstatus
2 123456789010 eni-1235b8ca123456789 172.31.16.139 172.31.16.21 20641 22 6 20 4249 1418530010 1418530070 ACCEPT OK""",
        
        'cloudtrail': """{
    "Records": [
        {
            "eventVersion": "1.05",
            "userIdentity": {"type": "IAMUser"},
            "eventTime": "2019-06-19T00:46:59Z",
            "eventSource": "s3.amazonaws.com",
            "eventName": "GetObject"
        }
    ]
}"""
    }


class TestIntegration:
    """통합 테스트"""
    
    def test_end_to_end_log_detection_workflow(self, sample_log_contents):
        """전체 로그 탐지 워크플로우 테스트"""
        # 1. 패턴 매칭
        for log_type_name, content in sample_log_contents.items():
            detected_type, confidence = LogPatternMatcher.detect_log_type(content)
            assert detected_type is not None
            assert confidence > 0.3
        
        # 2. 분류기 테스트
        classifier = LogFormatClassifier()
        
        for log_type_name, content in sample_log_contents.items():
            sample = LogSample(
                content=content,
                source_key=f"{log_type_name}.log",
                sample_size=len(content)
            )
            
            result = classifier.classify_log_sample(sample)
            if result:  # 일부 샘플은 분류되지 않을 수 있음
                assert result.confidence_score > 0
                assert len(result.sample_lines) > 0
        
        # 3. 메타데이터 분석
        analyzer = LogMetadataAnalyzer()
        
        # 샘플 스캔 결과 생성
        log_files = []
        for i, (log_type_name, content) in enumerate(sample_log_contents.items()):
            log_files.append(LogFileInfo(
                key=f"logs/{log_type_name}.log",
                size=len(content),
                last_modified=datetime.now() - timedelta(days=i),
                file_type=FileType.LOG,
                detected_log_type=LogType.S3_ACCESS,  # 임시로 S3_ACCESS 사용
                confidence_score=0.8,
                sample_content=content[:100]
            ))
        
        scan_result = ScanResult(
            bucket_name="test-bucket",
            prefix="logs/",
            total_files=len(log_files),
            total_size=sum(f.size for f in log_files),
            log_files=log_files,
            scan_duration=2.0,
            date_range=(datetime.now() - timedelta(days=5), datetime.now()),
            detected_log_types={LogType.S3_ACCESS: len(log_files)}
        )
        
        analysis_result = analyzer.analyze_logs(scan_result, detailed_analysis=True)
        
        assert analysis_result.quality_metrics.overall_score >= 0
        assert analysis_result.partitioning_recommendation.strategy in PartitionStrategy
        assert len(analysis_result.log_type_distribution) >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])