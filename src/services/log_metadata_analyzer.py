"""로그 메타데이터 분석기 - 로그 품질, 파티셔닝 전략, 시간 범위 분석"""

import statistics
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging
import re
from collections import defaultdict, Counter

from .log_scanner import ScanResult, LogFileInfo
from .log_classifier import LogFormatClassifier, LogSampleExtractor, ClassificationResult
from ..models.log_configuration import LogType

logger = logging.getLogger(__name__)


class PartitionStrategy(Enum):
    """파티셔닝 전략"""
    NONE = "none"
    DAILY = "daily"
    MONTHLY = "monthly"
    YEARLY = "yearly"
    HOURLY = "hourly"


class LogQuality(Enum):
    """로그 품질 등급"""
    EXCELLENT = "excellent"  # 90-100점
    GOOD = "good"           # 70-89점
    FAIR = "fair"           # 50-69점
    POOR = "poor"           # 0-49점


@dataclass
class TimeRangeAnalysis:
    """시간 범위 분석 결과"""
    start_date: datetime
    end_date: datetime
    total_days: int
    active_days: int  # 로그가 있는 날짜 수
    gaps: List[Tuple[datetime, datetime]]  # 로그가 없는 기간들
    daily_file_counts: Dict[str, int]  # 날짜별 파일 수
    peak_activity_day: Optional[str]
    avg_files_per_day: float
    
    @property
    def coverage_percentage(self) -> float:
        """로그 커버리지 비율"""
        return (self.active_days / max(1, self.total_days)) * 100
    
    @property
    def has_significant_gaps(self) -> bool:
        """중요한 로그 누락 기간이 있는지 확인"""
        return any((gap[1] - gap[0]).days > 1 for gap in self.gaps)


@dataclass
class VolumeAnalysis:
    """볼륨 분석 결과"""
    total_size_gb: float
    total_files: int
    avg_file_size_mb: float
    median_file_size_mb: float
    largest_file_mb: float
    smallest_file_mb: float
    size_distribution: Dict[str, int]  # 크기 구간별 파일 수
    growth_trend: str  # "increasing", "decreasing", "stable"
    estimated_daily_volume_gb: float
    
    @property
    def size_consistency_score(self) -> float:
        """파일 크기 일관성 점수 (0-100)"""
        if self.smallest_file_mb == 0:
            return 0
        
        ratio = self.largest_file_mb / self.smallest_file_mb
        if ratio <= 2:
            return 100
        elif ratio <= 10:
            return 80
        elif ratio <= 100:
            return 60
        else:
            return 40


@dataclass
class QualityMetrics:
    """품질 메트릭"""
    overall_score: int  # 0-100
    detection_rate: float  # 로그 타입 탐지율
    avg_confidence: float  # 평균 신뢰도
    format_consistency: float  # 형식 일관성
    completeness_score: float  # 완성도 점수
    issues: List[str]
    recommendations: List[str]
    
    @property
    def quality_grade(self) -> LogQuality:
        """품질 등급"""
        if self.overall_score >= 90:
            return LogQuality.EXCELLENT
        elif self.overall_score >= 70:
            return LogQuality.GOOD
        elif self.overall_score >= 50:
            return LogQuality.FAIR
        else:
            return LogQuality.POOR


@dataclass
class PartitioningRecommendation:
    """파티셔닝 추천"""
    strategy: PartitionStrategy
    estimated_partitions: int
    partition_size_gb: float
    reasoning: str
    performance_impact: str
    cost_impact: str
    implementation_complexity: str
    
    @property
    def is_recommended(self) -> bool:
        """추천 여부"""
        return self.strategy != PartitionStrategy.NONE


@dataclass
class MetadataAnalysisResult:
    """메타데이터 분석 결과"""
    scan_result: ScanResult
    time_analysis: TimeRangeAnalysis
    volume_analysis: VolumeAnalysis
    quality_metrics: QualityMetrics
    partitioning_recommendation: PartitioningRecommendation
    log_type_distribution: Dict[LogType, float]  # 로그 타입별 비율
    analysis_timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            'analysis_timestamp': self.analysis_timestamp.isoformat(),
            'time_analysis': {
                'start_date': self.time_analysis.start_date.isoformat(),
                'end_date': self.time_analysis.end_date.isoformat(),
                'total_days': self.time_analysis.total_days,
                'active_days': self.time_analysis.active_days,
                'coverage_percentage': self.time_analysis.coverage_percentage,
                'gaps_count': len(self.time_analysis.gaps),
                'has_significant_gaps': self.time_analysis.has_significant_gaps,
                'avg_files_per_day': self.time_analysis.avg_files_per_day,
                'peak_activity_day': self.time_analysis.peak_activity_day
            },
            'volume_analysis': {
                'total_size_gb': self.volume_analysis.total_size_gb,
                'total_files': self.volume_analysis.total_files,
                'avg_file_size_mb': self.volume_analysis.avg_file_size_mb,
                'median_file_size_mb': self.volume_analysis.median_file_size_mb,
                'size_consistency_score': self.volume_analysis.size_consistency_score,
                'growth_trend': self.volume_analysis.growth_trend,
                'estimated_daily_volume_gb': self.volume_analysis.estimated_daily_volume_gb
            },
            'quality_metrics': {
                'overall_score': self.quality_metrics.overall_score,
                'quality_grade': self.quality_metrics.quality_grade.value,
                'detection_rate': self.quality_metrics.detection_rate,
                'avg_confidence': self.quality_metrics.avg_confidence,
                'format_consistency': self.quality_metrics.format_consistency,
                'completeness_score': self.quality_metrics.completeness_score,
                'issues_count': len(self.quality_metrics.issues),
                'recommendations_count': len(self.quality_metrics.recommendations)
            },
            'partitioning_recommendation': {
                'strategy': self.partitioning_recommendation.strategy.value,
                'estimated_partitions': self.partitioning_recommendation.estimated_partitions,
                'partition_size_gb': self.partitioning_recommendation.partition_size_gb,
                'is_recommended': self.partitioning_recommendation.is_recommended,
                'reasoning': self.partitioning_recommendation.reasoning
            },
            'log_type_distribution': {
                log_type.value: percentage 
                for log_type, percentage in self.log_type_distribution.items()
            }
        }


class LogMetadataAnalyzer:
    """로그 메타데이터 분석기"""
    
    def __init__(self):
        self.classifier = LogFormatClassifier()
        self.sample_extractor = LogSampleExtractor()
    
    def analyze_logs(self, scan_result: ScanResult, 
                    detailed_analysis: bool = True) -> MetadataAnalysisResult:
        """로그 메타데이터 종합 분석"""
        logger.info(f"로그 메타데이터 분석 시작: {scan_result.bucket_name}/{scan_result.prefix}")
        
        # 시간 범위 분석
        time_analysis = self._analyze_time_range(scan_result)
        
        # 볼륨 분석
        volume_analysis = self._analyze_volume_patterns(scan_result)
        
        # 품질 분석
        quality_metrics = self._analyze_log_quality(scan_result, detailed_analysis)
        
        # 파티셔닝 추천
        partitioning_recommendation = self._recommend_partitioning(
            scan_result, time_analysis, volume_analysis
        )
        
        # 로그 타입 분포
        log_type_distribution = self._calculate_log_type_distribution(scan_result)
        
        result = MetadataAnalysisResult(
            scan_result=scan_result,
            time_analysis=time_analysis,
            volume_analysis=volume_analysis,
            quality_metrics=quality_metrics,
            partitioning_recommendation=partitioning_recommendation,
            log_type_distribution=log_type_distribution
        )
        
        logger.info(f"로그 메타데이터 분석 완료: 품질 점수 {quality_metrics.overall_score}/100")
        return result
    
    def _analyze_time_range(self, scan_result: ScanResult) -> TimeRangeAnalysis:
        """시간 범위 분석"""
        if not scan_result.log_files or not scan_result.date_range:
            return TimeRangeAnalysis(
                start_date=datetime.now(),
                end_date=datetime.now(),
                total_days=0,
                active_days=0,
                gaps=[],
                daily_file_counts={},
                peak_activity_day=None,
                avg_files_per_day=0.0
            )
        
        start_date, end_date = scan_result.date_range
        total_days = (end_date - start_date).days + 1
        
        # 날짜별 파일 수 계산
        daily_counts = defaultdict(int)
        for log_file in scan_result.log_files:
            date_key = log_file.last_modified.date().isoformat()
            daily_counts[date_key] += 1
        
        active_days = len(daily_counts)
        
        # 로그 누락 기간 찾기
        gaps = self._find_log_gaps(start_date, end_date, set(daily_counts.keys()))
        
        # 피크 활동 날짜
        peak_day = max(daily_counts.keys(), key=lambda k: daily_counts[k]) if daily_counts else None
        
        # 평균 파일 수
        avg_files_per_day = len(scan_result.log_files) / max(1, total_days)
        
        return TimeRangeAnalysis(
            start_date=start_date,
            end_date=end_date,
            total_days=total_days,
            active_days=active_days,
            gaps=gaps,
            daily_file_counts=dict(daily_counts),
            peak_activity_day=peak_day,
            avg_files_per_day=avg_files_per_day
        )
    
    def _find_log_gaps(self, start_date: datetime, end_date: datetime, 
                      active_dates: set) -> List[Tuple[datetime, datetime]]:
        """로그 누락 기간 찾기"""
        gaps = []
        current_date = start_date.date()
        end_date_only = end_date.date()
        
        gap_start = None
        
        while current_date <= end_date_only:
            date_str = current_date.isoformat()
            
            if date_str not in active_dates:
                if gap_start is None:
                    gap_start = datetime.combine(current_date, datetime.min.time())
            else:
                if gap_start is not None:
                    gap_end = datetime.combine(current_date - timedelta(days=1), datetime.max.time())
                    gaps.append((gap_start, gap_end))
                    gap_start = None
            
            current_date += timedelta(days=1)
        
        # 마지막 갭 처리
        if gap_start is not None:
            gap_end = datetime.combine(end_date_only, datetime.max.time())
            gaps.append((gap_start, gap_end))
        
        return gaps
    
    def _analyze_volume_patterns(self, scan_result: ScanResult) -> VolumeAnalysis:
        """볼륨 패턴 분석"""
        if not scan_result.log_files:
            return VolumeAnalysis(
                total_size_gb=0,
                total_files=0,
                avg_file_size_mb=0,
                median_file_size_mb=0,
                largest_file_mb=0,
                smallest_file_mb=0,
                size_distribution={},
                growth_trend="stable",
                estimated_daily_volume_gb=0
            )
        
        # 파일 크기 통계
        sizes_mb = [log_file.size / (1024 * 1024) for log_file in scan_result.log_files]
        
        total_size_gb = scan_result.total_size_gb
        total_files = len(scan_result.log_files)
        avg_file_size_mb = statistics.mean(sizes_mb)
        median_file_size_mb = statistics.median(sizes_mb)
        largest_file_mb = max(sizes_mb)
        smallest_file_mb = min(sizes_mb)
        
        # 크기 분포
        size_distribution = self._calculate_size_distribution(sizes_mb)
        
        # 성장 트렌드 분석
        growth_trend = self._analyze_growth_trend(scan_result.log_files)
        
        # 일일 예상 볼륨
        if scan_result.date_range:
            days = (scan_result.date_range[1] - scan_result.date_range[0]).days + 1
            estimated_daily_volume_gb = total_size_gb / max(1, days)
        else:
            estimated_daily_volume_gb = 0
        
        return VolumeAnalysis(
            total_size_gb=total_size_gb,
            total_files=total_files,
            avg_file_size_mb=avg_file_size_mb,
            median_file_size_mb=median_file_size_mb,
            largest_file_mb=largest_file_mb,
            smallest_file_mb=smallest_file_mb,
            size_distribution=size_distribution,
            growth_trend=growth_trend,
            estimated_daily_volume_gb=estimated_daily_volume_gb
        )
    
    def _calculate_size_distribution(self, sizes_mb: List[float]) -> Dict[str, int]:
        """파일 크기 분포 계산"""
        distribution = {
            "tiny": 0,      # < 1MB
            "small": 0,     # 1-10MB
            "medium": 0,    # 10-100MB
            "large": 0,     # 100MB-1GB
            "xlarge": 0     # > 1GB
        }
        
        for size in sizes_mb:
            if size < 1:
                distribution["tiny"] += 1
            elif size < 10:
                distribution["small"] += 1
            elif size < 100:
                distribution["medium"] += 1
            elif size < 1024:
                distribution["large"] += 1
            else:
                distribution["xlarge"] += 1
        
        return distribution
    
    def _analyze_growth_trend(self, log_files: List[LogFileInfo]) -> str:
        """성장 트렌드 분석"""
        if len(log_files) < 10:
            return "stable"
        
        # 시간순 정렬
        sorted_files = sorted(log_files, key=lambda f: f.last_modified)
        
        # 첫 번째와 마지막 절반의 평균 크기 비교
        mid_point = len(sorted_files) // 2
        first_half_avg = statistics.mean(f.size for f in sorted_files[:mid_point])
        second_half_avg = statistics.mean(f.size for f in sorted_files[mid_point:])
        
        ratio = second_half_avg / first_half_avg if first_half_avg > 0 else 1
        
        if ratio > 1.2:
            return "increasing"
        elif ratio < 0.8:
            return "decreasing"
        else:
            return "stable"
    
    def _analyze_log_quality(self, scan_result: ScanResult, 
                           detailed_analysis: bool) -> QualityMetrics:
        """로그 품질 분석"""
        issues = []
        recommendations = []
        
        # 기본 메트릭 계산
        total_files = len(scan_result.log_files)
        detected_files = sum(1 for f in scan_result.log_files if f.detected_log_type)
        detection_rate = detected_files / max(1, total_files)
        
        # 평균 신뢰도
        confidence_scores = [f.confidence_score for f in scan_result.log_files 
                           if f.confidence_score > 0]
        avg_confidence = statistics.mean(confidence_scores) if confidence_scores else 0
        
        # 형식 일관성 (같은 로그 타입의 비율)
        if scan_result.detected_log_types:
            max_type_count = max(scan_result.detected_log_types.values())
            format_consistency = max_type_count / max(1, total_files)
        else:
            format_consistency = 0
        
        # 완성도 점수 (시간 커버리지 기반)
        if scan_result.date_range and total_files > 0:
            days = (scan_result.date_range[1] - scan_result.date_range[0]).days + 1
            active_days = len(set(f.last_modified.date() for f in scan_result.log_files))
            completeness_score = active_days / max(1, days)
        else:
            completeness_score = 0
        
        # 상세 분석
        if detailed_analysis:
            issues, recommendations = self._perform_detailed_quality_analysis(
                scan_result, detection_rate, avg_confidence, format_consistency
            )
        
        # 전체 점수 계산
        overall_score = self._calculate_overall_quality_score(
            detection_rate, avg_confidence, format_consistency, completeness_score, issues
        )
        
        return QualityMetrics(
            overall_score=overall_score,
            detection_rate=detection_rate,
            avg_confidence=avg_confidence,
            format_consistency=format_consistency,
            completeness_score=completeness_score,
            issues=issues,
            recommendations=recommendations
        )
    
    def _perform_detailed_quality_analysis(self, scan_result: ScanResult,
                                         detection_rate: float, avg_confidence: float,
                                         format_consistency: float) -> Tuple[List[str], List[str]]:
        """상세 품질 분석"""
        issues = []
        recommendations = []
        
        # 탐지율 검사
        if detection_rate < 0.5:
            issues.append(f"낮은 로그 타입 탐지율: {detection_rate:.1%}")
            recommendations.append("로그 파일 형식을 확인하고 표준 AWS 로그 형식인지 검토하세요")
        
        # 신뢰도 검사
        if avg_confidence < 0.6:
            issues.append(f"낮은 평균 신뢰도: {avg_confidence:.2f}")
            recommendations.append("로그 파일 내용을 샘플링하여 형식 일관성을 확인하세요")
        
        # 형식 일관성 검사
        if format_consistency < 0.8:
            issues.append(f"낮은 형식 일관성: {format_consistency:.1%}")
            recommendations.append("여러 로그 타입이 혼재되어 있습니다. 로그 타입별로 분리를 고려하세요")
        
        # 파일 크기 일관성 검사
        if scan_result.log_files:
            sizes = [f.size for f in scan_result.log_files]
            if len(sizes) > 1:
                size_variance = max(sizes) / min(sizes) if min(sizes) > 0 else float('inf')
                if size_variance > 1000:  # 1000배 이상 차이
                    issues.append("파일 크기 편차가 매우 큽니다")
                    recommendations.append("로그 로테이션 정책을 검토하고 일관된 크기로 관리하세요")
        
        # 시간적 일관성 검사
        if scan_result.date_range:
            days = (scan_result.date_range[1] - scan_result.date_range[0]).days + 1
            files_per_day = len(scan_result.log_files) / days
            
            if files_per_day < 0.1:
                issues.append("로그 파일 생성 빈도가 낮습니다")
                recommendations.append("로그 생성 설정을 확인하고 정기적인 로그 생성이 되는지 검토하세요")
            elif files_per_day > 100:
                issues.append("로그 파일 생성 빈도가 매우 높습니다")
                recommendations.append("로그 집계 또는 압축을 통해 파일 수를 줄이는 것을 고려하세요")
        
        return issues, recommendations
    
    def _calculate_overall_quality_score(self, detection_rate: float, avg_confidence: float,
                                       format_consistency: float, completeness_score: float,
                                       issues: List[str]) -> int:
        """전체 품질 점수 계산"""
        # 기본 점수 (각 메트릭별 가중치)
        score = (
            detection_rate * 30 +           # 탐지율 30%
            avg_confidence * 25 +           # 신뢰도 25%
            format_consistency * 25 +       # 형식 일관성 25%
            completeness_score * 20         # 완성도 20%
        )
        
        # 이슈별 감점
        issue_penalty = min(len(issues) * 5, 30)  # 이슈당 5점 감점, 최대 30점
        
        final_score = max(0, int(score * 100) - issue_penalty)
        return min(100, final_score)
    
    def _recommend_partitioning(self, scan_result: ScanResult, 
                              time_analysis: TimeRangeAnalysis,
                              volume_analysis: VolumeAnalysis) -> PartitioningRecommendation:
        """파티셔닝 전략 추천"""
        total_size_gb = volume_analysis.total_size_gb
        total_days = time_analysis.total_days
        daily_volume_gb = volume_analysis.estimated_daily_volume_gb
        
        # 파티셔닝 전략 결정 로직
        if total_size_gb < 1 or total_days <= 7:
            strategy = PartitionStrategy.NONE
            reasoning = "데이터 크기가 작거나 기간이 짧아 파티셔닝이 불필요합니다"
            estimated_partitions = 1
            partition_size_gb = total_size_gb
            
        elif daily_volume_gb > 10:  # 일일 10GB 이상
            if total_days <= 30:
                strategy = PartitionStrategy.DAILY
                reasoning = "대용량 일일 데이터로 인해 일별 파티셔닝을 권장합니다"
            else:
                strategy = PartitionStrategy.MONTHLY
                reasoning = "대용량 데이터와 긴 기간으로 인해 월별 파티셔닝을 권장합니다"
                
        elif total_days <= 90:
            strategy = PartitionStrategy.DAILY
            reasoning = "중간 규모 데이터셋으로 일별 파티셔닝이 적합합니다"
            
        elif total_days <= 365:
            if daily_volume_gb > 1:
                strategy = PartitionStrategy.DAILY
                reasoning = "일일 데이터 볼륨이 충분하여 일별 파티셔닝을 권장합니다"
            else:
                strategy = PartitionStrategy.MONTHLY
                reasoning = "연간 데이터로 월별 파티셔닝이 효율적입니다"
                
        else:  # 1년 이상
            if daily_volume_gb > 5:
                strategy = PartitionStrategy.MONTHLY
                reasoning = "다년간 대용량 데이터로 월별 파티셔닝을 권장합니다"
            else:
                strategy = PartitionStrategy.YEARLY
                reasoning = "다년간 소용량 데이터로 연별 파티셔닝이 적합합니다"
        
        # 파티션 수 및 크기 계산
        if strategy == PartitionStrategy.DAILY:
            estimated_partitions = time_analysis.active_days
            partition_size_gb = daily_volume_gb
        elif strategy == PartitionStrategy.MONTHLY:
            estimated_partitions = max(1, total_days // 30)
            partition_size_gb = daily_volume_gb * 30
        elif strategy == PartitionStrategy.YEARLY:
            estimated_partitions = max(1, total_days // 365)
            partition_size_gb = daily_volume_gb * 365
        else:
            estimated_partitions = 1
            partition_size_gb = total_size_gb
        
        # 성능 및 비용 영향 평가
        performance_impact = self._assess_performance_impact(strategy, estimated_partitions)
        cost_impact = self._assess_cost_impact(strategy, total_size_gb)
        complexity = self._assess_implementation_complexity(strategy)
        
        return PartitioningRecommendation(
            strategy=strategy,
            estimated_partitions=estimated_partitions,
            partition_size_gb=round(partition_size_gb, 2),
            reasoning=reasoning,
            performance_impact=performance_impact,
            cost_impact=cost_impact,
            implementation_complexity=complexity
        )
    
    def _assess_performance_impact(self, strategy: PartitionStrategy, 
                                 partition_count: int) -> str:
        """성능 영향 평가"""
        if strategy == PartitionStrategy.NONE:
            return "파티셔닝 없음 - 전체 스캔 필요"
        elif partition_count < 10:
            return "낮음 - 효율적인 파티션 프루닝 가능"
        elif partition_count < 100:
            return "중간 - 적절한 쿼리 성능 향상 예상"
        else:
            return "높음 - 많은 파티션으로 인한 메타데이터 오버헤드 가능"
    
    def _assess_cost_impact(self, strategy: PartitionStrategy, total_size_gb: float) -> str:
        """비용 영향 평가"""
        if strategy == PartitionStrategy.NONE:
            return "파티셔닝 비용 없음"
        elif total_size_gb < 10:
            return "낮음 - 소규모 데이터셋"
        elif total_size_gb < 100:
            return "중간 - 적절한 비용 대비 성능 향상"
        else:
            return "높음 - 대용량 데이터 처리 비용 절감 효과 큼"
    
    def _assess_implementation_complexity(self, strategy: PartitionStrategy) -> str:
        """구현 복잡도 평가"""
        complexity_map = {
            PartitionStrategy.NONE: "없음",
            PartitionStrategy.DAILY: "중간 - 일별 파티션 관리 필요",
            PartitionStrategy.MONTHLY: "낮음 - 월별 파티션 관리",
            PartitionStrategy.YEARLY: "낮음 - 연별 파티션 관리",
            PartitionStrategy.HOURLY: "높음 - 시간별 파티션 관리 복잡"
        }
        return complexity_map.get(strategy, "알 수 없음")
    
    def _calculate_log_type_distribution(self, scan_result: ScanResult) -> Dict[LogType, float]:
        """로그 타입 분포 계산"""
        if not scan_result.log_files:
            return {}
        
        type_counts = Counter()
        total_files = len(scan_result.log_files)
        
        for log_file in scan_result.log_files:
            if log_file.detected_log_type:
                type_counts[log_file.detected_log_type] += 1
        
        # 백분율로 변환
        distribution = {}
        for log_type, count in type_counts.items():
            distribution[log_type] = (count / total_files) * 100
        
        return distribution


class LogQualityAssessment:
    """로그 품질 평가 도구"""
    
    @staticmethod
    def generate_quality_report(analysis_result: MetadataAnalysisResult) -> Dict[str, Any]:
        """품질 보고서 생성"""
        quality = analysis_result.quality_metrics
        
        report = {
            'summary': {
                'overall_grade': quality.quality_grade.value,
                'score': quality.overall_score,
                'total_files': analysis_result.volume_analysis.total_files,
                'total_size_gb': analysis_result.volume_analysis.total_size_gb,
                'time_span_days': analysis_result.time_analysis.total_days
            },
            'strengths': [],
            'weaknesses': [],
            'recommendations': quality.recommendations,
            'detailed_metrics': {
                'detection_rate': f"{quality.detection_rate:.1%}",
                'avg_confidence': f"{quality.avg_confidence:.2f}",
                'format_consistency': f"{quality.format_consistency:.1%}",
                'completeness_score': f"{quality.completeness_score:.1%}"
            }
        }
        
        # 강점 식별
        if quality.detection_rate >= 0.9:
            report['strengths'].append("높은 로그 타입 탐지율")
        if quality.avg_confidence >= 0.8:
            report['strengths'].append("높은 분류 신뢰도")
        if quality.format_consistency >= 0.9:
            report['strengths'].append("일관된 로그 형식")
        if quality.completeness_score >= 0.8:
            report['strengths'].append("양호한 시간적 완성도")
        
        # 약점 식별
        if quality.detection_rate < 0.7:
            report['weaknesses'].append("낮은 로그 타입 탐지율")
        if quality.avg_confidence < 0.6:
            report['weaknesses'].append("낮은 분류 신뢰도")
        if quality.format_consistency < 0.7:
            report['weaknesses'].append("불일치하는 로그 형식")
        if quality.completeness_score < 0.6:
            report['weaknesses'].append("불완전한 시간적 커버리지")
        
        return report
    
    @staticmethod
    def suggest_improvements(analysis_result: MetadataAnalysisResult) -> List[str]:
        """개선 제안"""
        suggestions = []
        quality = analysis_result.quality_metrics
        volume = analysis_result.volume_analysis
        
        # 품질 기반 제안
        if quality.detection_rate < 0.8:
            suggestions.append("로그 형식을 표준 AWS 로그 형식으로 통일하세요")
        
        if quality.format_consistency < 0.8:
            suggestions.append("서로 다른 로그 타입을 별도 경로로 분리하세요")
        
        # 볼륨 기반 제안
        if volume.size_consistency_score < 60:
            suggestions.append("로그 로테이션 정책을 검토하여 일관된 파일 크기를 유지하세요")
        
        if volume.total_size_gb > 100:
            suggestions.append("로그 압축을 활성화하여 스토리지 비용을 절감하세요")
        
        # 파티셔닝 제안
        if analysis_result.partitioning_recommendation.is_recommended:
            strategy = analysis_result.partitioning_recommendation.strategy.value
            suggestions.append(f"{strategy} 파티셔닝을 구현하여 쿼리 성능을 향상시키세요")
        
        return suggestions