import React, { useState, useEffect } from 'react';
import { 
  Shield, 
  Database, 
  ArrowRight, 
  Info, 
  CheckCircle, 
  AlertTriangle,
  Zap,
  Lock
} from 'lucide-react';

interface ModeCapability {
  name: string;
  description: string;
  icon: string;
  available: boolean;
}

interface ModeConfig {
  mode: 'guide' | 'metadata';
  displayName: string;
  description: string;
  securityLevel: string;
  capabilities: ModeCapability[];
  restrictions: string[];
  awsPermissionsRequired: boolean;
}

interface UserPreference {
  preferredMode: 'guide' | 'metadata';
  lastUsedMode: 'guide' | 'metadata';
  firstVisit: boolean;
  modeSwitchCount: number;
}

interface ModeRecommendation {
  recommendedMode: 'guide' | 'metadata';
  reason: string;
  confidence: number;
  upgradeBenefits: string[];
}

interface ModeSelectorProps {
  onModeSelect: (mode: 'guide' | 'metadata') => void;
  awsAuthStatus: boolean;
  userPreferences?: UserPreference;
}

const ModeSelector: React.FC<ModeSelectorProps> = ({
  onModeSelect,
  awsAuthStatus,
  userPreferences
}) => {
  const [selectedMode, setSelectedMode] = useState<'guide' | 'metadata'>('guide');
  const [showModeComparison, setShowModeComparison] = useState(false);
  const [recommendation, setRecommendation] = useState<ModeRecommendation | null>(null);

  // 모드 설정 정보
  const modeConfigs: Record<'guide' | 'metadata', ModeConfig> = {
    guide: {
      mode: 'guide',
      displayName: '🔒 Guide Mode',
      description: 'AWS 권한 없이 안전하게 DDL 템플릿과 설정 가이드를 제공합니다',
      securityLevel: '최고 보안',
      capabilities: [
        { name: 'ddl_templates', description: '로그 타입별 DDL 템플릿', icon: '📄', available: true },
        { name: 'setup_guides', description: '단계별 설정 가이드', icon: '📋', available: true },
        { name: 'query_templates', description: '분석 쿼리 템플릿', icon: '🔍', available: true },
        { name: 'offline_mode', description: '완전 오프라인 작업', icon: '🔌', available: true }
      ],
      restrictions: [
        'AWS 계정 연결 불가',
        '자동 테이블 생성 불가',
        '실시간 버킷 스캔 불가'
      ],
      awsPermissionsRequired: false
    },
    metadata: {
      mode: 'metadata',
      displayName: '📊 Metadata Mode',
      description: '제한된 AWS 권한으로 메타데이터를 분석하여 자동 DDL 생성 및 테이블 생성을 지원합니다',
      securityLevel: '제한적 권한',
      capabilities: [
        { name: 'auto_ddl', description: '자동 DDL 생성', icon: '⚡', available: true },
        { name: 'table_creation', description: 'Athena 테이블 자동 생성', icon: '🏗️', available: true },
        { name: 'bucket_analysis', description: 'S3 버킷 구조 분석', icon: '🔍', available: true },
        { name: 'metadata_scan', description: '안전한 메타데이터 스캔', icon: '📊', available: true }
      ],
      restrictions: [
        '실제 로그 내용 접근 금지',
        'S3 GetObject 권한 불필요',
        '1시간 세션 제한'
      ],
      awsPermissionsRequired: true
    }
  };

  // 초기 모드 결정
  useEffect(() => {
    const initialMode = determineInitialMode();
    setSelectedMode(initialMode);
    
    // 추천 생성
    const rec = generateRecommendation(initialMode);
    setRecommendation(rec);
  }, [awsAuthStatus, userPreferences]);

  const determineInitialMode = (): 'guide' | 'metadata' => {
    // 사용자 선호도가 있으면 우선 적용
    if (userPreferences?.preferredMode) {
      return userPreferences.preferredMode;
    }
    
    // 첫 방문자는 Guide Mode
    if (!userPreferences || userPreferences.firstVisit) {
      return 'guide';
    }
    
    // 기본값은 Guide Mode
    return 'guide';
  };

  const generateRecommendation = (currentMode: 'guide' | 'metadata'): ModeRecommendation | null => {
    // Guide Mode 사용자에게 Metadata Mode 추천
    if (currentMode === 'guide' && awsAuthStatus) {
      return {
        recommendedMode: 'metadata',
        reason: 'AWS 인증이 감지되었습니다. 더 강력한 자동화 기능을 사용해보세요!',
        confidence: 0.8,
        upgradeBenefits: [
          '🚀 자동 DDL 생성 및 테이블 생성',
          '📊 실시간 S3 버킷 구조 분석',
          '⚡ 원클릭 Athena 테이블 설정',
          '🔍 지능형 로그 타입 감지'
        ]
      };
    }

    // Metadata Mode 사용자가 권한 문제가 있으면 Guide Mode 추천
    if (currentMode === 'metadata' && !awsAuthStatus) {
      return {
        recommendedMode: 'guide',
        reason: 'AWS 권한이 필요합니다. Guide Mode에서 안전하게 시작해보세요.',
        confidence: 0.9,
        upgradeBenefits: [
          '🔒 AWS 권한 불필요',
          '📄 즉시 사용 가능한 DDL 템플릿',
          '📋 상세한 설정 가이드',
          '🔌 완전 오프라인 작업 가능'
        ]
      };
    }

    return null;
  };

  const handleModeSelect = (mode: 'guide' | 'metadata') => {
    setSelectedMode(mode);
    onModeSelect(mode);
  };

  const ModeCard: React.FC<{ config: ModeConfig; isSelected: boolean }> = ({ config, isSelected }) => (
    <div 
      className={`mode-card ${isSelected ? 'selected' : ''} ${!config.awsPermissionsRequired || awsAuthStatus ? 'available' : 'disabled'}`}
      onClick={() => handleModeSelect(config.mode)}
    >
      <div className="mode-header">
        <h3 className="mode-title">{config.displayName}</h3>
        <div className={`security-badge ${config.mode}`}>
          {config.mode === 'guide' ? <Lock size={16} /> : <Shield size={16} />}
          {config.securityLevel}
        </div>
      </div>
      
      <p className="mode-description">{config.description}</p>
      
      <div className="capabilities">
        <h4>주요 기능</h4>
        <ul>
          {config.capabilities.map((capability, index) => (
            <li key={index} className="capability-item">
              <span className="capability-icon">{capability.icon}</span>
              <span className="capability-text">{capability.description}</span>
              {capability.available && <CheckCircle size={16} className="available-icon" />}
            </li>
          ))}
        </ul>
      </div>

      <div className="restrictions">
        <h4>제한사항</h4>
        <ul>
          {config.restrictions.map((restriction, index) => (
            <li key={index} className="restriction-item">
              <AlertTriangle size={14} className="restriction-icon" />
              <span>{restriction}</span>
            </li>
          ))}
        </ul>
      </div>

      {config.awsPermissionsRequired && !awsAuthStatus && (
        <div className="auth-required">
          <Info size={16} />
          <span>AWS 인증이 필요합니다</span>
        </div>
      )}
    </div>
  );

  return (
    <div className="mode-selector">
      {/* 하이브리드 접근법: 기본 Guide Mode + 업그레이드 배너 */}
      {!showModeComparison && (
        <div className="hybrid-mode-banner">
          <div className="current-mode-info">
            <div className="mode-badge guide">
              <Lock size={20} />
              <span>Guide Mode - 안전하고 빠른 DDL 생성</span>
            </div>
            <p className="mode-subtitle">
              AWS 권한 없이 즉시 시작하세요. 로그 타입별 DDL 템플릿과 설정 가이드를 제공합니다.
            </p>
          </div>
          
          {recommendation && recommendation.recommendedMode === 'metadata' && (
            <div className="upgrade-prompt">
              <div className="upgrade-content">
                <Zap className="upgrade-icon" />
                <div className="upgrade-text">
                  <h4>더 강력한 기능을 원하세요?</h4>
                  <p>{recommendation.reason}</p>
                </div>
                <button 
                  className="upgrade-button"
                  onClick={() => setShowModeComparison(true)}
                >
                  Metadata Mode 체험하기 <ArrowRight size={16} />
                </button>
              </div>
              
              <div className="upgrade-benefits">
                {recommendation.upgradeBenefits.map((benefit, index) => (
                  <div key={index} className="benefit-item">
                    <CheckCircle size={14} />
                    <span>{benefit}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
          
          <div className="mode-actions">
            <button 
              className="btn-primary"
              onClick={() => handleModeSelect('guide')}
            >
              Guide Mode로 시작하기
            </button>
            <button 
              className="btn-secondary"
              onClick={() => setShowModeComparison(true)}
            >
              모드 비교하기
            </button>
          </div>
        </div>
      )}

      {/* 모드 비교 화면 */}
      {showModeComparison && (
        <div className="mode-comparison">
          <div className="comparison-header">
            <h2>운영 모드 선택</h2>
            <p>보안 요구사항과 필요한 기능에 따라 적절한 모드를 선택하세요.</p>
          </div>
          
          <div className="mode-cards">
            <ModeCard 
              config={modeConfigs.guide} 
              isSelected={selectedMode === 'guide'} 
            />
            <ModeCard 
              config={modeConfigs.metadata} 
              isSelected={selectedMode === 'metadata'} 
            />
          </div>
          
          <div className="comparison-actions">
            <button 
              className="btn-primary"
              onClick={() => handleModeSelect(selectedMode)}
              disabled={modeConfigs[selectedMode].awsPermissionsRequired && !awsAuthStatus}
            >
              {selectedMode === 'guide' ? '🔒 Guide Mode로 시작' : '📊 Metadata Mode로 시작'}
            </button>
            <button 
              className="btn-secondary"
              onClick={() => setShowModeComparison(false)}
            >
              간단히 시작하기 (Guide Mode)
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default ModeSelector;