import React, { useState, useEffect } from 'react';
import { analyzeLogs } from '../services/api';
import './LogVerification.css';

interface VerificationProgress {
  stage: string;
  progress_percentage: number;
  current_task: string;
  estimated_remaining_seconds?: number;
  files_processed: number;
  total_files: number;
}

interface VerificationResult {
  success: boolean;
  scan_summary: {
    total_files: number;
    log_files_count: number;
    total_size_gb: number;
    primary_log_type: string | null;
    detected_log_types: Record<string, number>;
    date_range: {
      start: string | null;
      end: string | null;
    };
  };
  metadata_analysis: {
    quality_score: number;
    completeness_percentage: number;
    recommendations: string[];
    partitioning_strategy: string;
    estimated_query_performance: string;
  };
  execution_info: {
    execution_time_seconds: number;
    error_message?: string;
  };
}

interface LogVerificationProps {
  selectedBucket: string;
  selectedFolder: string;
  onVerificationComplete?: (result: VerificationResult) => void;
  disabled?: boolean;
  autoVerify?: boolean; // 자동 검증 옵션
}

export const LogVerification: React.FC<LogVerificationProps> = ({
  selectedBucket,
  selectedFolder,
  onVerificationComplete,
  disabled = false,
  autoVerify = false
}) => {
  const [isVerifying, setIsVerifying] = useState(false);
  const [progress, setProgress] = useState<VerificationProgress | null>(null);
  const [result, setResult] = useState<VerificationResult | null>(null);
  const [error, setError] = useState<string>('');
  const [showResult, setShowResult] = useState(false);

  // 자동 검증: 버킷과 폴더가 선택되면 자동으로 검증 시작
  useEffect(() => {
    if (autoVerify && selectedBucket && selectedFolder && !isVerifying && !result) {
      console.log('Auto-verifying logs for:', { selectedBucket, selectedFolder });
      startVerification();
    }
  }, [selectedBucket, selectedFolder, autoVerify]);

  const startVerification = async () => {
    if (!selectedBucket) {
      setError('Please select a bucket first.');
      return;
    }

    setIsVerifying(true);
    setProgress(null);
    setResult(null);
    setError('');
    setShowResult(false);

    try {
      // 실제 API 호출
      const analysisResult = await analyzeLogs({
        bucket_name: selectedBucket,
        prefix: selectedFolder || '',
        max_samples: 10
      });

      // API 결과를 VerificationResult 형식으로 변환
      const verificationResult: VerificationResult = {
        success: true,
        scan_summary: {
          total_files: analysisResult.sample_count,
          log_files_count: analysisResult.sample_count,
          total_size_gb: 0, // API에서 제공하지 않음
          primary_log_type: analysisResult.log_type,
          detected_log_types: {
            [analysisResult.log_type]: analysisResult.sample_count
          },
          date_range: {
            start: null,
            end: null
          }
        },
        metadata_analysis: {
          quality_score: Math.round(analysisResult.confidence * 100),
          completeness_percentage: Math.round(analysisResult.confidence * 100),
          recommendations: [
            `로그 타입: ${analysisResult.log_type}`,
            `신뢰도: ${(analysisResult.confidence * 100).toFixed(0)}%`,
            `파티션 전략: ${analysisResult.partition_strategy}`
          ],
          partitioning_strategy: analysisResult.partition_strategy,
          estimated_query_performance: analysisResult.confidence > 0.8 ? '우수' : '보통'
        },
        execution_info: {
          execution_time_seconds: 0 // API에서 제공하지 않음
        }
      };

      setResult(verificationResult);
      setShowResult(true);
      
      if (onVerificationComplete) {
        onVerificationComplete(verificationResult);
      }
    } catch (err: any) {
      setError(err.message || '로그 분석 중 오류가 발생했습니다.');
      setResult({
        success: false,
        scan_summary: {
          total_files: 0,
          log_files_count: 0,
          total_size_gb: 0,
          primary_log_type: null,
          detected_log_types: {},
          date_range: { start: null, end: null }
        },
        metadata_analysis: {
          quality_score: 0,
          completeness_percentage: 0,
          recommendations: [],
          partitioning_strategy: '',
          estimated_query_performance: ''
        },
        execution_info: {
          execution_time_seconds: 0,
          error_message: err.message
        }
      });
      setShowResult(true);
    } finally {
      setIsVerifying(false);
    }
  };



  const getStageDisplayName = (stage: string): string => {
    const stageNames: Record<string, string> = {
      'scanning': '스캔 중',
      'classifying': '분류 중',
      'analyzing': '분석 중',
      'completed': '완료'
    };
    return stageNames[stage] || stage;
  };

  const getStatusColor = (qualityScore: number): string => {
    if (qualityScore >= 80) return 'success';
    if (qualityScore >= 60) return 'warning';
    return 'error';
  };

  const formatFileSize = (sizeGB: number): string => {
    if (sizeGB < 0.001) {
      return `${(sizeGB * 1024 * 1024).toFixed(1)} KB`;
    } else if (sizeGB < 1) {
      return `${(sizeGB * 1024).toFixed(1)} MB`;
    } else {
      return `${sizeGB.toFixed(2)} GB`;
    }
  };

  const formatDateRange = (dateRange: { start: string | null; end: string | null }): string => {
    if (!dateRange.start || !dateRange.end) {
      return '날짜 정보 없음';
    }
    
    const start = new Date(dateRange.start).toLocaleDateString('ko-KR');
    const end = new Date(dateRange.end).toLocaleDateString('ko-KR');
    
    if (start === end) {
      return start;
    }
    return `${start} ~ ${end}`;
  };

  return (
    <div className="log-verification">
      {/* 검증 버튼 */}
      <div className="verification-action">
        <button
          className={`btn-verify ${isVerifying ? 'verifying' : ''}`}
          onClick={startVerification}
          disabled={disabled || !selectedBucket || isVerifying}
        >
          <span className="btn-icon" role="img" aria-label="검색">🔍</span>
          <span className="btn-text">
            {isVerifying ? 'Verifying...' : 'Verify Log Files'}
          </span>
          {isVerifying && <div className="btn-spinner"></div>}
        </button>
      </div>

      {/* 오류 메시지 */}
      {error && (
        <div className="error-message">
          <span className="error-icon">⚠️</span>
          <div className="error-content">
            <strong>검증 오류</strong>
            <p>{error}</p>
            <button 
              className="retry-button"
              onClick={startVerification}
              disabled={isVerifying}
            >
              다시 시도
            </button>
          </div>
        </div>
      )}

      {/* 진행 상황 표시 */}
      {isVerifying && progress && (
        <div className="verification-progress">
          <div className="progress-header">
            <div className="progress-stage">
              <span className="stage-icon">
                {progress.stage === 'scanning' && '📂'}
                {progress.stage === 'classifying' && '🔍'}
                {progress.stage === 'analyzing' && '📊'}
                {progress.stage === 'completed' && '✅'}
              </span>
              <span className="stage-name">{getStageDisplayName(progress.stage)}</span>
            </div>
            <div className="progress-percentage">
              {Math.round(progress.progress_percentage)}%
            </div>
          </div>

          <div className="progress-bar-container">
            <div 
              className="progress-bar"
              style={{ width: `${progress.progress_percentage}%` }}
            >
              <div className="progress-bar-glow"></div>
            </div>
          </div>

          <div className="progress-details">
            <div className="current-task">
              <span className="task-pulse"></span>
              {progress.current_task}
            </div>
            
            {progress.total_files > 0 && (
              <div className="file-progress">
                {progress.files_processed} / {progress.total_files} 파일 처리됨
              </div>
            )}

            {progress.estimated_remaining_seconds && (
              <div className="time-remaining">
                예상 남은 시간: {Math.ceil(progress.estimated_remaining_seconds)}초
              </div>
            )}
          </div>
        </div>
      )}

      {/* 검증 결과 */}
      {showResult && result && (
        <div className={`verification-result ${result.success ? 'success' : 'error'}`}>
          {result.success ? (
            <>
              {/* 결과 헤더 */}
              <div className="result-header">
                <div className="result-icon success">✅</div>
                <div className="result-title">
                  <h3>로그 검증 완료</h3>
                  <p>분석 시간: {result.execution_info.execution_time_seconds.toFixed(1)}초</p>
                </div>
              </div>

              {/* 품질 점수 */}
              <div className="quality-score-card">
                <div className="score-header">
                  <span className="score-icon">⭐</span>
                  <h4>로그 품질 점수</h4>
                </div>
                <div className={`score-value ${getStatusColor(result.metadata_analysis.quality_score)}`}>
                  {result.metadata_analysis.quality_score}/100
                </div>
                <div className="score-description">
                  완성도: {result.metadata_analysis.completeness_percentage}%
                </div>
              </div>

              {/* 스캔 요약 */}
              <div className="scan-summary">
                <h4>
                  <span role="img" aria-label="요약">📋</span>
                  스캔 요약
                </h4>
                <div className="summary-grid">
                  <div className="summary-item">
                    <div className="summary-label">총 파일 수</div>
                    <div className="summary-value">
                      {result.scan_summary.total_files.toLocaleString()}개
                    </div>
                  </div>
                  <div className="summary-item">
                    <div className="summary-label">로그 파일</div>
                    <div className="summary-value">
                      {result.scan_summary.log_files_count.toLocaleString()}개
                    </div>
                  </div>
                  <div className="summary-item">
                    <div className="summary-label">총 크기</div>
                    <div className="summary-value">
                      {formatFileSize(result.scan_summary.total_size_gb)}
                    </div>
                  </div>
                  <div className="summary-item">
                    <div className="summary-label">날짜 범위</div>
                    <div className="summary-value">
                      {formatDateRange(result.scan_summary.date_range)}
                    </div>
                  </div>
                </div>
              </div>

              {/* 로그 타입 분포 */}
              {Object.keys(result.scan_summary.detected_log_types).length > 0 && (
                <div className="log-types">
                  <h4>
                    <span role="img" aria-label="타입">🏷️</span>
                    감지된 로그 타입
                  </h4>
                  <div className="log-type-list">
                    {Object.entries(result.scan_summary.detected_log_types).map(([type, count]) => (
                      <div key={type} className="log-type-item">
                        <div className="log-type-name">{type}</div>
                        <div className="log-type-count">{count}개</div>
                      </div>
                    ))}
                  </div>
                  {result.scan_summary.primary_log_type && (
                    <div className="primary-log-type">
                      주요 로그 타입: <strong>{result.scan_summary.primary_log_type}</strong>
                    </div>
                  )}
                </div>
              )}

              {/* 권장사항 */}
              {result.metadata_analysis.recommendations.length > 0 && (
                <div className="recommendations">
                  <h4>
                    <span role="img" aria-label="권장사항">💡</span>
                    권장사항
                  </h4>
                  <ul className="recommendation-list">
                    {result.metadata_analysis.recommendations.map((recommendation, index) => (
                      <li key={index} className="recommendation-item">
                        {recommendation}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* 성능 정보 */}
              <div className="performance-info">
                <div className="performance-item">
                  <span className="performance-label">파티셔닝 전략:</span>
                  <span className="performance-value">
                    {result.metadata_analysis.partitioning_strategy}
                  </span>
                </div>
                <div className="performance-item">
                  <span className="performance-label">예상 쿼리 성능:</span>
                  <span className="performance-value">
                    {result.metadata_analysis.estimated_query_performance}
                  </span>
                </div>
              </div>
            </>
          ) : (
            <>
              {/* 실패 결과 */}
              <div className="result-header">
                <div className="result-icon error">❌</div>
                <div className="result-title">
                  <h3>로그 검증 실패</h3>
                  <p>{result.execution_info.error_message}</p>
                </div>
              </div>

              <div className="error-suggestions">
                <h4>해결 방법</h4>
                <ul>
                  <li>S3 버킷에 대한 읽기 권한이 있는지 확인하세요</li>
                  <li>선택한 폴더에 로그 파일이 존재하는지 확인하세요</li>
                  <li>AWS 자격 증명이 올바르게 설정되어 있는지 확인하세요</li>
                  <li>네트워크 연결 상태를 확인하세요</li>
                </ul>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
};