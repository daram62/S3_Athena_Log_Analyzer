import React from 'react';
import { ThemeToggle } from './ThemeToggle';
import { HelpCircle, BarChart3, Settings } from 'lucide-react';
import { useLanguage } from '../contexts/LanguageContext';
import './MainHeader.css';

interface MainHeaderProps {
  awsConnectionStatus?: 'connected' | 'disconnected' | 'checking';
  userInfo?: {
    name?: string;
    email?: string;
    role?: string;
  };
  currentPage?: 'setup' | 'workspace' | 'tables';
  onPageChange?: (page: 'setup' | 'workspace' | 'tables') => void;
  onShowGuide?: () => void;
}

export const MainHeader: React.FC<MainHeaderProps> = ({ 
  awsConnectionStatus = 'checking',
  userInfo,
  currentPage = 'setup',
  onPageChange,
  onShowGuide
}) => {
  const { t } = useLanguage();
  
  const getConnectionStatusInfo = () => {
    switch (awsConnectionStatus) {
      case 'connected':
        return { icon: '✅', text: 'AWS 연결됨', className: 'connected' };
      case 'disconnected':
        return { icon: '❌', text: 'AWS 연결 안됨', className: 'disconnected' };
      default:
        return { icon: '🔄', text: t('status.aws.checking'), className: 'checking' };
    }
  };

  const connectionInfo = getConnectionStatusInfo();

  return (
    <header className="main-header">
      <div className="header-content">
        <div className="logo-section">
          <div className="logo-icon" role="img" aria-label="로켓">
            🚀
          </div>
          <div className="logo-text">
            <h1>{t('app.title')}</h1>
            <p className="subtitle">{t('header.subtitle')}</p>
          </div>
        </div>
        
        <div className="header-actions">
          {/* 페이지 네비게이션 버튼 */}
          {onPageChange && awsConnectionStatus === 'connected' && (
            <div className="page-navigation">
              <button
                className={`nav-button ${currentPage === 'setup' ? 'active' : ''}`}
                onClick={() => onPageChange('setup')}
                title="S3 → Athena 자동 셋업"
              >
                <Settings size={18} />
                <span>설정</span>
              </button>
              <button
                className={`nav-button ${currentPage === 'tables' ? 'active' : ''}`}
                onClick={() => onPageChange('tables')}
                title="테이블 관리"
              >
                📊
                <span>테이블</span>
              </button>
              <button
                className={`nav-button ${currentPage === 'workspace' ? 'active' : ''}`}
                onClick={() => onPageChange('workspace')}
                title="로그 분석 워크스페이스"
              >
                <BarChart3 size={18} />
                <span>분석</span>
              </button>
            </div>
          )}
          
          <div className="aws-status">
            <span className={`status-indicator ${connectionInfo.className}`}>
              <span className="status-icon" role="img" aria-label={connectionInfo.text}>
                {connectionInfo.icon}
              </span>
              <span className="status-text">{connectionInfo.text}</span>
            </span>
          </div>
          
          <ThemeToggle />
          {onShowGuide && (
            <button className="guide-button" onClick={onShowGuide} title="사용 가이드">
              <HelpCircle size={18} />
            </button>
          )}
        </div>
      </div>
      
      {awsConnectionStatus === 'disconnected' && (
        <div className="aws-credentials-guide">
          <div className="guide-content">
            <HelpCircle size={16} />
            <span>AWS 자격 증명이 필요합니다. </span>
            <button className="guide-link">
              설정 방법 보기
            </button>
          </div>
        </div>
      )}
    </header>
  );
};