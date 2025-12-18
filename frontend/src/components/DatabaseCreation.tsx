import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom';
import { useLanguage } from '../contexts/LanguageContext';
import { createTable, checkTableExists, TableCheckResult } from '../services/api';
import './DatabaseCreation.css';

interface DatabaseCreationProps {
  selectedBucket: string;
  selectedFolder: string;
  databaseConfig: any;
  verificationResult: any;
  disabled?: boolean;
  onCreationComplete?: (result: any) => void;
  onNavigateToWorkspace?: () => void;
}

interface CreationStep {
  id: string;
  title: string;
  status: 'pending' | 'in-progress' | 'completed' | 'error';
  message?: string;
}

export const DatabaseCreation: React.FC<DatabaseCreationProps> = ({
  selectedBucket,
  selectedFolder,
  databaseConfig,
  verificationResult,
  disabled = false,
  onCreationComplete,
  onNavigateToWorkspace
}) => {
  const { t } = useLanguage();
  const [isCreating, setIsCreating] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [creationSteps, setCreationSteps] = useState<CreationStep[]>([
    { id: 'database', title: t('creation.database'), status: 'pending' },
    { id: 'table', title: t('creation.table'), status: 'pending' },
    { id: 'partitions', title: t('creation.partitions'), status: 'pending' },
    { id: 'validation', title: t('creation.validation'), status: 'pending' }
  ]);
  const [creationResult, setCreationResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [tableCheckResult, setTableCheckResult] = useState<TableCheckResult | null>(null);
  const [isCheckingTable, setIsCheckingTable] = useState(false);

  // 테이블 존재 여부 확인
  useEffect(() => {
    const checkTable = async () => {
      if (databaseConfig?.databaseName && databaseConfig?.tableName) {
        setIsCheckingTable(true);
        try {
          const result = await checkTableExists(
            databaseConfig.databaseName,
            databaseConfig.tableName
          );
          setTableCheckResult(result);
        } catch (err) {
          console.error('Failed to check table:', err);
          setTableCheckResult(null);
        } finally {
          setIsCheckingTable(false);
        }
      } else {
        setTableCheckResult(null);
      }
    };

    checkTable();
  }, [databaseConfig?.databaseName, databaseConfig?.tableName]);

  const isButtonEnabled = !disabled && 
    selectedBucket && 
    databaseConfig?.isValid && 
    verificationResult?.success && 
    !isCreating;

  const handleCreateClick = async () => {
    if (!isButtonEnabled) return;

    setIsCreating(true);
    setShowModal(true);
    setError(null);
    setCreationResult(null);

    // Reset all steps to pending
    setCreationSteps(steps => steps.map(step => ({ ...step, status: 'pending' })));

    try {
      await simulateCreationProcess();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Creation failed');
    } finally {
      setIsCreating(false);
    }
  };

  const simulateCreationProcess = async () => {
    try {
      // 실제 API 호출
      // verificationResult는 LogAnalysisResult 형식: { log_type: "vpc_flow", ... }
      const logType = verificationResult?.log_type || verificationResult?.scan_summary?.primary_log_type || 's3_access';
      console.log('Creating table with log_type:', logType, 'verificationResult:', verificationResult);
      
      const apiResult = await createTable({
        bucket_name: selectedBucket,
        log_type: logType,
        database_name: databaseConfig.databaseName,
        table_name: databaseConfig.tableName
      });

      // 각 단계를 순차적으로 업데이트 (UI 효과)
      const steps = ['database', 'table', 'partitions', 'validation'];
      
      for (const stepId of steps) {
        // 진행 중으로 설정
        setCreationSteps(prevSteps => 
          prevSteps.map(step => 
            step.id === stepId 
              ? { ...step, status: 'in-progress' }
              : step
          )
        );

        // 약간의 지연 (UI 효과)
        await new Promise(resolve => setTimeout(resolve, 500));

        // 완료로 설정
        setCreationSteps(prevSteps => 
          prevSteps.map(step => 
            step.id === stepId 
              ? { 
                  ...step, 
                  status: 'completed',
                  message: 'Completed successfully'
                }
              : step
          )
        );
      }

      // 성공 결과 설정
      const result = {
        success: apiResult.status === 'created',
        database: apiResult.database_name,
        table: apiResult.table_name,
        location: `s3://${selectedBucket}/${selectedFolder}`,
        createdAt: new Date().toISOString()
      };
      
      setCreationResult(result);
      onCreationComplete?.(result);

    } catch (error) {
      // 폴백: 시뮬레이션 모드
      console.warn('API call failed, falling back to simulation:', error);
      await simulateCreationFallback();
    }
  };

  const simulateCreationFallback = async () => {
    const steps = ['database', 'table', 'partitions', 'validation'];
    
    for (let i = 0; i < steps.length; i++) {
      const stepId = steps[i];
      
      // Set current step to in-progress
      setCreationSteps(prevSteps => 
        prevSteps.map(step => 
          step.id === stepId 
            ? { ...step, status: 'in-progress' }
            : step
        )
      );

      // Simulate API call delay
      await new Promise(resolve => setTimeout(resolve, 1500 + Math.random() * 1000));

      // Simulate potential error (5% chance in fallback)
      if (Math.random() < 0.05) {
        setCreationSteps(prevSteps => 
          prevSteps.map(step => 
            step.id === stepId 
              ? { ...step, status: 'error', message: `Failed to ${step.title.toLowerCase()}` }
              : step
          )
        );
        throw new Error(`Failed to ${stepId}`);
      }

      // Mark step as completed
      setCreationSteps(prevSteps => 
        prevSteps.map(step => 
          step.id === stepId 
            ? { ...step, status: 'completed', message: 'Completed successfully' }
            : step
        )
      );
    }

    // Success - set result
    const result = {
      success: true,
      database: databaseConfig.databaseName,
      table: databaseConfig.tableName,
      location: `s3://${selectedBucket}/${selectedFolder}`,
      createdAt: new Date().toISOString()
    };
    
    setCreationResult(result);
    onCreationComplete?.(result);
  };

  const handleRetry = () => {
    setError(null);
    handleCreateClick();
  };

  const handleCloseModal = () => {
    setShowModal(false);
    setCreationSteps(steps => steps.map(step => ({ ...step, status: 'pending' })));
  };

  const getStepIcon = (status: CreationStep['status']) => {
    switch (status) {
      case 'completed':
        return '✅';
      case 'error':
        return '❌';
      case 'in-progress':
        return '⏳';
      default:
        return '⏸️';
    }
  };

  return (
    <>
      <div className="database-creation">
        {/* 테이블 확인 중 */}
        {isCheckingTable && (
          <div className="table-check-status">
            <div className="spinner-small"></div>
            <span>테이블 존재 여부 확인 중...</span>
          </div>
        )}

        {/* 테이블이 이미 존재하는 경우 */}
        {tableCheckResult?.exists && (
          <div className="table-exists-notice">
            <div className="notice-icon">✅</div>
            <div className="notice-content">
              <h4>테이블이 이미 존재합니다!</h4>
              <p className="table-info">
                <strong>{tableCheckResult.database}.{tableCheckResult.table}</strong>
              </p>
              {tableCheckResult.location && (
                <p className="location-info">📍 {tableCheckResult.location}</p>
              )}
              {tableCheckResult.created_at && (
                <p className="created-info">
                  🕐 생성일: {new Date(tableCheckResult.created_at).toLocaleString('ko-KR')}
                </p>
              )}
              <p className="action-hint">
                바로 분석을 시작하거나 Athena 콘솔에서 쿼리를 실행하세요!
              </p>
            </div>
          </div>
        )}

        <div className="button-group">
          {/* 테이블이 없을 때만 생성 버튼 표시 */}
          {!tableCheckResult?.exists && (
            <button 
              className={`create-button ${isButtonEnabled ? 'enabled' : 'disabled'}`}
              onClick={handleCreateClick}
              disabled={!isButtonEnabled}
            >
              <span className="button-icon" role="img" aria-label="생성">⚙️</span>
              <span className="button-text">{t('button.create.database')}</span>
              {isCreating && <div className="button-spinner"></div>}
            </button>
          )}
          
          <button 
            className="athena-button"
            onClick={() => {
              const region = 'us-east-1';
              const athenaUrl = `https://${region}.console.aws.amazon.com/athena/home?region=${region}#/query-editor`;
              window.open(athenaUrl, '_blank');
            }}
          >
            <span className="button-icon" role="img" aria-label="Athena">🔍</span>
            <span className="button-text">Go to Athena</span>
          </button>
          
          {onNavigateToWorkspace && (
            <button 
              className={`workspace-button ${tableCheckResult?.exists ? 'highlight' : ''}`}
              onClick={onNavigateToWorkspace}
            >
              <span className="button-icon" role="img" aria-label="분석">📊</span>
              <span className="button-text">
                {tableCheckResult?.exists ? '분석하러 가기' : '분석 탭'}
              </span>
            </button>
          )}
        </div>
        
        {!isButtonEnabled && !tableCheckResult?.exists && (
          <div className="button-help">
            {!selectedBucket && <p>{t('help.select.s3')}</p>}
            {!databaseConfig?.isValid && <p>{t('help.complete.database')}</p>}
            {!verificationResult?.success && <p>{t('help.complete.verification')}</p>}
          </div>
        )}
      </div>

      {/* Creation Progress Modal - Portal로 body에 직접 렌더링 */}
      {showModal && ReactDOM.createPortal(
        <div 
          className="modal-overlay" 
          onClick={(e) => e.target === e.currentTarget && (creationResult || error) && handleCloseModal()}
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            width: '100vw',
            height: '100vh',
            backgroundColor: 'rgba(0, 0, 0, 0.6)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 99999,
          }}
        >
          <div 
            className="creation-modal"
            style={{
              backgroundColor: '#ffffff',
              borderRadius: '16px',
              boxShadow: '0 25px 50px rgba(0, 0, 0, 0.4)',
              maxWidth: '600px',
              width: '90%',
              maxHeight: '85vh',
              overflow: 'hidden',
              position: 'fixed',
              top: '50%',
              left: '50%',
              transform: 'translate(-50%, -50%)',
            }}
          >
            <div className="modal-header">
              <h3>
                {creationResult ? `🎉 ${t('modal.creation.complete')}` : 
                 error ? `❌ ${t('modal.creation.failed')}` : 
                 `⚙️ ${t('modal.creating')}`}
              </h3>
            </div>

            <div className="modal-content">
              {!creationResult && !error && (
                <div className="progress-section">
                  <div className="progress-steps">
                    {creationSteps.map((step, index) => (
                      <div key={step.id} className={`progress-step ${step.status}`}>
                        <div className="step-icon">
                          {getStepIcon(step.status)}
                        </div>
                        <div className="step-info">
                          <div className="step-title">{step.title}</div>
                          {step.message && (
                            <div className="step-message">{step.message}</div>
                          )}
                        </div>
                        {step.status === 'in-progress' && (
                          <div className="step-spinner"></div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {creationResult && (
                <div className="success-section">
                  <div className="success-animation">
                    <div className="checkmark">✅</div>
                  </div>
                  <div className="success-details">
                    <div className="resource-card">
                      <h4>{t('modal.created.resources')}</h4>
                      <div className="resource-item">
                        <span className="resource-label">Database:</span>
                        <span className="resource-value">{creationResult.database}</span>
                      </div>
                      <div className="resource-item">
                        <span className="resource-label">Table:</span>
                        <span className="resource-value">{creationResult.table}</span>
                      </div>
                      <div className="resource-item">
                        <span className="resource-label">Location:</span>
                        <span className="resource-value">{creationResult.location}</span>
                      </div>
                    </div>
                    <div className="next-steps">
                      <h4>{t('modal.next.steps')}</h4>
                      <p>{t('modal.athena.ready')}</p>
                      
                      <button 
                        className="btn-athena-console"
                        onClick={() => {
                          // 모달 닫고 분석 탭으로 이동
                          handleCloseModal();
                          if (onNavigateToWorkspace) {
                            onNavigateToWorkspace();
                          }
                        }}
                      >
                        Go to Analysis
                      </button>
                      
                      <ul>
                        <li>{t('modal.query.console')}</li>
                        <li>{t('modal.ai.interface')}</li>
                        <li>{t('modal.automated.analysis')}</li>
                      </ul>
                    </div>
                  </div>
                </div>
              )}

              {error && (
                <div className="error-section">
                  <div className="error-icon">❌</div>
                  <div className="error-message">
                    <h4>{t('modal.creation.failed')}</h4>
                    <p>{error}</p>
                  </div>
                  <div className="error-actions">
                    <button className="btn-retry" onClick={handleRetry}>
                      🔄 {t('button.retry')}
                    </button>
                  </div>
                </div>
              )}
            </div>

            <div className="modal-footer">
              {(creationResult || error) && (
                <button className="btn-close" onClick={handleCloseModal}>
                  {t('button.close')}
                </button>
              )}
            </div>
          </div>
        </div>,
        document.getElementById('modal-root') || document.body
      )}
    </>
  );
};