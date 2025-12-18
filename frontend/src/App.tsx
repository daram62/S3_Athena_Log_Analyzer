import React, { useState, useEffect } from 'react';
import { ThemeProvider } from './contexts/ThemeContext';
import { LanguageProvider, useLanguage } from './contexts/LanguageContext';
import { MainHeader } from './components/MainHeader';
import { S3LocationSelector } from './components/S3LocationSelector';
import { DatabaseConfiguration } from './components/DatabaseConfiguration';

import { DatabaseCreation } from './components/DatabaseCreation';
import { QueryInterface } from './components/QueryInterface';
import TableManagement from './components/TableManagement';
import { GuidedTour } from './components/GuidedTour';
// 대시보드는 QueryInterface 내부에서 로그 타입에 따라 표시됨
// Part1Demo는 Setup 탭에 통합됨
import './styles/globals.css';
import './App.css';
import './utils/accessibilityTest';

interface AWSConnectionStatus {
  status: 'connected' | 'disconnected' | 'checking';
  userInfo?: {
    name?: string;
    email?: string;
    role?: string;
  };
}

function AppContent() {
  const { t } = useLanguage();
  const [currentPage, setCurrentPage] = useState<'setup' | 'workspace' | 'tables'>('setup');
  const [analysisContext, setAnalysisContext] = useState<{
    databaseName: string;
    tableName: string;
    logType: string;
  } | null>(null);
  const [awsStatus, setAwsStatus] = useState<AWSConnectionStatus>({
    status: 'checking'
  });
  const [selectedBucket, setSelectedBucket] = useState<string>('');
  const [selectedFolder, setSelectedFolder] = useState<string>('');
  const [databaseConfig, setDatabaseConfig] = useState<any>(null);
  const [verificationResult, setVerificationResult] = useState<any>(null);
  const [creationResult, setCreationResult] = useState<any>(null);
  const [showGuide, setShowGuide] = useState<boolean>(false);
  const [pendingGuide, setPendingGuide] = useState<boolean>(() => {
    // 첫 방문 시 가이드 대기
    const hasSeenGuide = localStorage.getItem('hasSeenUserGuide');
    return !hasSeenGuide;
  });

  // AWS 연결 완료 후 가이드 표시
  useEffect(() => {
    if (pendingGuide && awsStatus.status === 'connected') {
      // DOM이 완전히 렌더링된 후 가이드 시작
      setTimeout(() => {
        setShowGuide(true);
        setPendingGuide(false);
      }, 500);
    }
  }, [pendingGuide, awsStatus.status]);

  const handleCloseGuide = () => {
    setShowGuide(false);
    localStorage.setItem('hasSeenUserGuide', 'true');
  };

  // AWS 연결 상태 확인 (시뮬레이션)
  useEffect(() => {
    const checkAWSConnection = async () => {
      try {
        // 실제로는 백엔드 API 호출
        // const response = await fetch('/api/aws/status');
        
        // 시뮬레이션: 2초 후 연결 상태 설정
        setTimeout(() => {
          setAwsStatus({
            status: 'connected',
            userInfo: {
              name: 'AWS Support Engineer',
              email: 'engineer@example.com',
              role: 'Support Engineer'
            }
          });
        }, 2000);
      } catch (error) {
        setAwsStatus({
          status: 'disconnected'
        });
      }
    };

    checkAWSConnection();
  }, []);

  return (
    <div className="app">
        <GuidedTour 
          isActive={showGuide} 
          onComplete={handleCloseGuide}
          onPageChange={setCurrentPage}
          currentPage={currentPage}
          onSelectBucket={(bucket) => {
            setSelectedBucket(bucket);
            setSelectedFolder('');
          }}
        />
        <a href="#main-content" className="skip-link">
          메인 콘텐츠로 건너뛰기
        </a>
        <MainHeader 
          awsConnectionStatus={awsStatus.status}
          userInfo={awsStatus.userInfo}
          currentPage={currentPage}
          onPageChange={setCurrentPage}
          onShowGuide={() => setShowGuide(true)}
        />
        
        <main id="main-content" className="main-content">
          {currentPage === 'tables' ? (
            <TableManagement 
              onNavigateToAnalysis={(databaseName, tableName, logType) => {
                setAnalysisContext({ databaseName, tableName, logType });
                setCurrentPage('workspace');
              }}
            />
          ) : currentPage === 'workspace' ? (
            <QueryInterface 
              databaseName={analysisContext?.databaseName || databaseConfig?.databaseName || creationResult?.database}
              tableName={analysisContext?.tableName || databaseConfig?.tableName || creationResult?.table}
              logType={analysisContext?.logType}
            />
          ) : (
            <div className="setup-container">
            <div className="welcome-section">
              <h2>{t('app.title')}</h2>
              <p>
                {t('app.subtitle')}
              </p>
            </div>

            {awsStatus.status === 'connected' && (
              <div className="setup-steps">
                <div className="step-indicator">
                  <div className={`step ${selectedBucket ? 'active completed' : 'active'}`}>
                    <div className="step-number">{selectedBucket ? '✓' : '1'}</div>
                    <div className="step-label">{t('step.s3.selection')}</div>
                  </div>
                  <div className="step-connector"></div>
                  <div className={`step ${selectedBucket && !verificationResult ? 'active' : verificationResult?.success ? 'completed' : ''}`}>
                    <div className="step-number">{verificationResult?.success ? '✓' : '2'}</div>
                    <div className="step-label">{t('step.log.verification')}</div>
                  </div>
                  <div className="step-connector"></div>
                  <div className={`step ${verificationResult?.success && !creationResult ? 'active' : creationResult?.success ? 'completed' : ''}`}>
                    <div className="step-number">{creationResult?.success ? '✓' : '3'}</div>
                    <div className="step-label">{t('step.table.creation')}</div>
                  </div>
                </div>

                <div className="setup-grid">
                  <div className="setup-card s3-location-card">
                    <div className="card-header">
                      <span className="card-icon" role="img" aria-label="폴더">📁</span>
                      <h3>{t('card.s3.location')}</h3>
                    </div>
                    <div className="card-content">
                      <S3LocationSelector 
                        onLocationChange={(bucket, folder) => {
                          console.log('Location changed:', { bucket, folder });
                          setSelectedBucket(bucket);
                          setSelectedFolder(folder);
                          // 위치가 변경되면 검증 결과 초기화
                          setVerificationResult(null);
                        }}
                        disabled={awsStatus.status !== 'connected'}
                      />
                    </div>
                  </div>

                  <div className="setup-card database-config-card">
                    <div className="card-header">
                      <span className="card-icon" role="img" aria-label="데이터베이스">🗄️</span>
                      <h3>{t('card.database.config')}</h3>
                    </div>
                    <div className="card-content">
                      <DatabaseConfiguration
                        selectedBucket={selectedBucket}
                        detectedLogType={verificationResult?.log_type}
                        onConfigurationChange={(config) => {
                          console.log('Database config changed:', config);
                          setDatabaseConfig(config);
                        }}
                        disabled={awsStatus.status !== 'connected'}
                      />
                    </div>
                  </div>
                </div>



                {/* 데이터베이스 생성 섹션 */}
                {(verificationResult?.success || selectedBucket) && (
                  <div className="creation-section">
                    <DatabaseCreation
                      selectedBucket={selectedBucket || 'test-bucket'}
                      selectedFolder={selectedFolder || 'test-folder/'}
                      databaseConfig={databaseConfig || { 
                        databaseName: 'test_db', 
                        tableName: 'test_table', 
                        isValid: true 
                      }}
                      verificationResult={verificationResult || { success: true }}
                      onCreationComplete={(result) => {
                        console.log('Creation completed:', result);
                        setCreationResult(result);
                      }}
                      onNavigateToWorkspace={() => setCurrentPage('workspace')}
                      disabled={awsStatus.status !== 'connected'}
                    />
                  </div>
                )}


              </div>
            )}

            {awsStatus.status === 'checking' && (
              <div className="loading-section">
                <div className="loading-spinner"></div>
                <p>{t('status.aws.checking')}</p>
              </div>
            )}

            {awsStatus.status === 'disconnected' && (
              <div className="error-section">
                <div className="error-icon">❌</div>
                <h3>{t('status.aws.connection.required')}</h3>
                <p>
                  {t('status.aws.connection.description')}
                </p>
                <button className="btn-primary">
                  {t('button.aws.guide')}
                </button>
              </div>
            )}
            </div>
          )}
        </main>
      </div>
  );
}

function App() {
  return (
    <LanguageProvider>
      <ThemeProvider>
        <AppContent />
      </ThemeProvider>
    </LanguageProvider>
  );
}

export default App;