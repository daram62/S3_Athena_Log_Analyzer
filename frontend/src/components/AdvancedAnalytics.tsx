import React, { useState, useEffect } from 'react';
import {
  TrendingUp,
  GitCompare,
  Settings,
  Save,
  Share2,
  Plus,
  Trash2,
  Edit3,
  Eye,
  Calendar,
  Filter,
  Download,
  Bell,
  AlertCircle,
  CheckCircle,
  Clock,
  Target,
  Zap
} from 'lucide-react';
import { useLanguage } from '../contexts/LanguageContext';
import './AdvancedAnalytics.css';

interface LogPattern {
  id: string;
  name: string;
  pattern: string;
  description: string;
  matches: number;
  trend: 'up' | 'down' | 'stable';
  severity: 'low' | 'medium' | 'high';
  lastSeen: Date;
}

interface CustomDashboard {
  id: string;
  name: string;
  description: string;
  widgets: DashboardWidget[];
  isPublic: boolean;
  createdAt: Date;
  updatedAt: Date;
}

interface DashboardWidget {
  id: string;
  type: 'metric' | 'chart' | 'table' | 'alert';
  title: string;
  query: string;
  position: { x: number; y: number; w: number; h: number };
  config: any;
}

interface MonitoringRule {
  id: string;
  name: string;
  description: string;
  condition: string;
  threshold: number;
  operator: '>' | '<' | '=' | '!=' | '>=' | '<=';
  isActive: boolean;
  alertChannels: string[];
  lastTriggered?: Date;
  triggerCount: number;
}

const MOCK_PATTERNS: LogPattern[] = [
  {
    id: '1',
    name: 'SQL Injection 시도',
    pattern: '/\\b(union|select|insert|update|delete|drop)\\b.*\\b(from|where|order by)\\b/i',
    description: 'SQL 인젝션 공격 패턴 감지',
    matches: 23,
    trend: 'up',
    severity: 'high',
    lastSeen: new Date(Date.now() - 5 * 60 * 1000)
  },
  {
    id: '2',
    name: '비정상적인 트래픽 급증',
    pattern: 'requests_per_minute > 1000',
    description: '분당 요청 수가 1000을 초과하는 경우',
    matches: 156,
    trend: 'stable',
    severity: 'medium',
    lastSeen: new Date(Date.now() - 15 * 60 * 1000)
  },
  {
    id: '3',
    name: '404 에러 집중',
    pattern: 'status_code = 404 AND count > 50',
    description: '특정 경로에서 404 에러가 집중적으로 발생',
    matches: 89,
    trend: 'down',
    severity: 'low',
    lastSeen: new Date(Date.now() - 30 * 60 * 1000)
  }
];

const MOCK_DASHBOARDS: CustomDashboard[] = [
  {
    id: '1',
    name: '보안 모니터링',
    description: '보안 관련 메트릭과 알림을 모니터링하는 대시보드',
    widgets: [
      {
        id: '1',
        type: 'metric',
        title: '의심스러운 IP',
        query: 'SELECT COUNT(DISTINCT remote_ip) FROM logs WHERE suspicious = true',
        position: { x: 0, y: 0, w: 6, h: 3 },
        config: { color: '#e74c3c' }
      },
      {
        id: '2',
        type: 'chart',
        title: '공격 시도 트렌드',
        query: 'SELECT date_trunc(\'hour\', timestamp), COUNT(*) FROM logs WHERE attack_detected = true GROUP BY 1',
        position: { x: 6, y: 0, w: 6, h: 6 },
        config: { chartType: 'line' }
      }
    ],
    isPublic: false,
    createdAt: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000),
    updatedAt: new Date(Date.now() - 2 * 60 * 60 * 1000)
  },
  {
    id: '2',
    name: '성능 분석',
    description: '애플리케이션 성능 메트릭 종합 분석',
    widgets: [
      {
        id: '3',
        type: 'metric',
        title: '평균 응답시간',
        query: 'SELECT AVG(response_time) FROM logs WHERE timestamp >= now() - interval \'1 hour\'',
        position: { x: 0, y: 0, w: 4, h: 3 },
        config: { color: '#3498db', unit: 'ms' }
      }
    ],
    isPublic: true,
    createdAt: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000),
    updatedAt: new Date(Date.now() - 1 * 60 * 60 * 1000)
  }
];

const MOCK_MONITORING_RULES: MonitoringRule[] = [
  {
    id: '1',
    name: '높은 에러율 알림',
    description: '5분간 에러율이 5%를 초과할 때 알림',
    condition: 'error_rate_5min',
    threshold: 5,
    operator: '>',
    isActive: true,
    alertChannels: ['email', 'slack'],
    lastTriggered: new Date(Date.now() - 2 * 60 * 60 * 1000),
    triggerCount: 3
  },
  {
    id: '2',
    name: '응답시간 지연 알림',
    description: '평균 응답시간이 1초를 초과할 때 알림',
    condition: 'avg_response_time',
    threshold: 1000,
    operator: '>',
    isActive: true,
    alertChannels: ['email'],
    triggerCount: 0
  },
  {
    id: '3',
    name: '트래픽 급증 알림',
    description: '분당 요청 수가 평소보다 200% 증가할 때 알림',
    condition: 'traffic_spike',
    threshold: 200,
    operator: '>',
    isActive: false,
    alertChannels: ['slack', 'webhook'],
    triggerCount: 1
  }
];

export const AdvancedAnalytics: React.FC = () => {
  const { t } = useLanguage();
  const [activeSection, setActiveSection] = useState<'patterns' | 'dashboards' | 'monitoring'>('patterns');
  const [patterns, setPatterns] = useState<LogPattern[]>(MOCK_PATTERNS);
  const [dashboards, setDashboards] = useState<CustomDashboard[]>(MOCK_DASHBOARDS);
  const [monitoringRules, setMonitoringRules] = useState<MonitoringRule[]>(MOCK_MONITORING_RULES);
  const [selectedTimeRange, setSelectedTimeRange] = useState('24h');
  const [isCreatingDashboard, setIsCreatingDashboard] = useState(false);
  const [isCreatingRule, setIsCreatingRule] = useState(false);

  // 패턴 비교 기능
  const comparePatterns = (pattern1Id: string, pattern2Id: string) => {
    const p1 = patterns.find(p => p.id === pattern1Id);
    const p2 = patterns.find(p => p.id === pattern2Id);
    
    if (p1 && p2) {
      console.log('패턴 비교:', p1.name, 'vs', p2.name);
      // 실제로는 비교 결과를 모달로 표시
    }
  };

  // 대시보드 공유
  const shareDashboard = (dashboardId: string) => {
    const dashboard = dashboards.find(d => d.id === dashboardId);
    if (dashboard) {
      const shareUrl = `${window.location.origin}/dashboard/${dashboardId}`;
      navigator.clipboard.writeText(shareUrl);
      // 토스트 알림 표시
      console.log('대시보드 공유 링크가 클립보드에 복사되었습니다.');
    }
  };

  // 모니터링 규칙 토글
  const toggleMonitoringRule = (ruleId: string) => {
    setMonitoringRules(prev =>
      prev.map(rule =>
        rule.id === ruleId ? { ...rule, isActive: !rule.isActive } : rule
      )
    );
  };

  // 데이터 내보내기
  const exportData = (type: string) => {
    let data: any[] = [];
    let filename = '';
    
    switch (type) {
      case 'patterns':
        data = patterns;
        filename = 'log_patterns.json';
        break;
      case 'dashboards':
        data = dashboards;
        filename = 'custom_dashboards.json';
        break;
      case 'rules':
        data = monitoringRules;
        filename = 'monitoring_rules.json';
        break;
    }
    
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  };

  const formatTimeAgo = (date: Date) => {
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    
    if (diffMins < 60) {
      return `${diffMins}분 전`;
    } else if (diffHours < 24) {
      return `${diffHours}시간 전`;
    } else {
      return `${Math.floor(diffHours / 24)}일 전`;
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'high': return '#e74c3c';
      case 'medium': return '#f39c12';
      case 'low': return '#27ae60';
      default: return '#95a5a6';
    }
  };

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'up': return <TrendingUp size={16} style={{ color: '#e74c3c' }} />;
      case 'down': return <TrendingUp size={16} style={{ color: '#27ae60', transform: 'rotate(180deg)' }} />;
      case 'stable': return <Target size={16} style={{ color: '#95a5a6' }} />;
      default: return null;
    }
  };

  return (
    <div className="advanced-analytics">
      <div className="analytics-header">
        <div className="header-title">
          <Settings className="header-icon" size={28} />
          <h2>고급 분석 도구</h2>
        </div>
        
        <div className="section-tabs">
          <button
            className={`section-tab ${activeSection === 'patterns' ? 'active' : ''}`}
            onClick={() => setActiveSection('patterns')}
          >
            <GitCompare size={16} />
            로그 패턴 분석
          </button>
          <button
            className={`section-tab ${activeSection === 'dashboards' ? 'active' : ''}`}
            onClick={() => setActiveSection('dashboards')}
          >
            <Eye size={16} />
            커스텀 대시보드
          </button>
          <button
            className={`section-tab ${activeSection === 'monitoring' ? 'active' : ''}`}
            onClick={() => setActiveSection('monitoring')}
          >
            <Bell size={16} />
            실시간 모니터링
          </button>
        </div>
      </div>

      <div className="analytics-content">
        {/* 로그 패턴 분석 섹션 */}
        {activeSection === 'patterns' && (
          <div className="patterns-section">
            <div className="section-header">
              <h3>로그 패턴 비교 및 트렌드 분석</h3>
              <div className="section-actions">
                <div className="time-range-selector">
                  {['1h', '6h', '24h', '7d', '30d'].map(range => (
                    <button
                      key={range}
                      className={`time-range-button ${selectedTimeRange === range ? 'active' : ''}`}
                      onClick={() => setSelectedTimeRange(range)}
                    >
                      {range}
                    </button>
                  ))}
                </div>
                <button
                  className="export-button"
                  onClick={() => exportData('patterns')}
                >
                  <Download size={14} />
                  내보내기
                </button>
              </div>
            </div>
            
            <div className="patterns-grid">
              {patterns.map(pattern => (
                <div key={pattern.id} className="pattern-card">
                  <div className="pattern-header">
                    <div className="pattern-info">
                      <h4>{pattern.name}</h4>
                      <div className="pattern-meta">
                        <span 
                          className="severity-badge"
                          style={{ backgroundColor: getSeverityColor(pattern.severity) }}
                        >
                          {pattern.severity.toUpperCase()}
                        </span>
                        <span className="trend-indicator">
                          {getTrendIcon(pattern.trend)}
                        </span>
                      </div>
                    </div>
                    <div className="pattern-stats">
                      <div className="stat-item">
                        <span className="stat-value">{pattern.matches}</span>
                        <span className="stat-label">매치</span>
                      </div>
                    </div>
                  </div>
                  
                  <div className="pattern-description">
                    {pattern.description}
                  </div>
                  
                  <div className="pattern-code">
                    <code>{pattern.pattern}</code>
                  </div>
                  
                  <div className="pattern-footer">
                    <span className="last-seen">
                      <Clock size={12} />
                      {formatTimeAgo(pattern.lastSeen)}
                    </span>
                    <div className="pattern-actions">
                      <button className="action-button">
                        <Edit3 size={14} />
                        편집
                      </button>
                      <button className="action-button">
                        <GitCompare size={14} />
                        비교
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 커스텀 대시보드 섹션 */}
        {activeSection === 'dashboards' && (
          <div className="dashboards-section">
            <div className="section-header">
              <h3>커스텀 대시보드 관리</h3>
              <div className="section-actions">
                <button
                  className="create-button"
                  onClick={() => setIsCreatingDashboard(true)}
                >
                  <Plus size={14} />
                  새 대시보드
                </button>
                <button
                  className="export-button"
                  onClick={() => exportData('dashboards')}
                >
                  <Download size={14} />
                  내보내기
                </button>
              </div>
            </div>
            
            <div className="dashboards-grid">
              {dashboards.map(dashboard => (
                <div key={dashboard.id} className="dashboard-card">
                  <div className="dashboard-header">
                    <div className="dashboard-info">
                      <h4>{dashboard.name}</h4>
                      <p className="dashboard-description">{dashboard.description}</p>
                    </div>
                    <div className="dashboard-status">
                      {dashboard.isPublic && (
                        <span className="public-badge">
                          <Share2 size={12} />
                          공개
                        </span>
                      )}
                    </div>
                  </div>
                  
                  <div className="dashboard-stats">
                    <div className="stat-item">
                      <span className="stat-value">{dashboard.widgets.length}</span>
                      <span className="stat-label">위젯</span>
                    </div>
                    <div className="stat-item">
                      <span className="stat-value">{formatTimeAgo(dashboard.updatedAt)}</span>
                      <span className="stat-label">업데이트</span>
                    </div>
                  </div>
                  
                  <div className="dashboard-preview">
                    <div className="widget-preview">
                      {dashboard.widgets.slice(0, 4).map(widget => (
                        <div key={widget.id} className="mini-widget">
                          <div className="widget-type">{widget.type}</div>
                          <div className="widget-title">{widget.title}</div>
                        </div>
                      ))}
                      {dashboard.widgets.length > 4 && (
                        <div className="more-widgets">
                          +{dashboard.widgets.length - 4}
                        </div>
                      )}
                    </div>
                  </div>
                  
                  <div className="dashboard-actions">
                    <button className="action-button primary">
                      <Eye size={14} />
                      보기
                    </button>
                    <button className="action-button">
                      <Edit3 size={14} />
                      편집
                    </button>
                    <button
                      className="action-button"
                      onClick={() => shareDashboard(dashboard.id)}
                    >
                      <Share2 size={14} />
                      공유
                    </button>
                    <button className="action-button danger">
                      <Trash2 size={14} />
                      삭제
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 실시간 모니터링 섹션 */}
        {activeSection === 'monitoring' && (
          <div className="monitoring-section">
            <div className="section-header">
              <h3>실시간 모니터링 및 알림 설정</h3>
              <div className="section-actions">
                <button
                  className="create-button"
                  onClick={() => setIsCreatingRule(true)}
                >
                  <Plus size={14} />
                  새 규칙
                </button>
                <button
                  className="export-button"
                  onClick={() => exportData('rules')}
                >
                  <Download size={14} />
                  내보내기
                </button>
              </div>
            </div>
            
            <div className="monitoring-rules">
              {monitoringRules.map(rule => (
                <div key={rule.id} className={`rule-card ${rule.isActive ? 'active' : 'inactive'}`}>
                  <div className="rule-header">
                    <div className="rule-info">
                      <h4>{rule.name}</h4>
                      <p className="rule-description">{rule.description}</p>
                    </div>
                    <div className="rule-toggle">
                      <label className="toggle-switch">
                        <input
                          type="checkbox"
                          checked={rule.isActive}
                          onChange={() => toggleMonitoringRule(rule.id)}
                        />
                        <span className="toggle-slider"></span>
                      </label>
                    </div>
                  </div>
                  
                  <div className="rule-condition">
                    <div className="condition-display">
                      <span className="condition-field">{rule.condition}</span>
                      <span className="condition-operator">{rule.operator}</span>
                      <span className="condition-threshold">{rule.threshold}</span>
                    </div>
                  </div>
                  
                  <div className="rule-stats">
                    <div className="stat-item">
                      <span className="stat-value">{rule.triggerCount}</span>
                      <span className="stat-label">트리거 횟수</span>
                    </div>
                    {rule.lastTriggered && (
                      <div className="stat-item">
                        <span className="stat-value">{formatTimeAgo(rule.lastTriggered)}</span>
                        <span className="stat-label">마지막 트리거</span>
                      </div>
                    )}
                  </div>
                  
                  <div className="rule-channels">
                    <span className="channels-label">알림 채널:</span>
                    <div className="channels-list">
                      {rule.alertChannels.map(channel => (
                        <span key={channel} className="channel-badge">
                          {channel}
                        </span>
                      ))}
                    </div>
                  </div>
                  
                  <div className="rule-actions">
                    <button className="action-button">
                      <Edit3 size={14} />
                      편집
                    </button>
                    <button className="action-button">
                      <Zap size={14} />
                      테스트
                    </button>
                    <button className="action-button danger">
                      <Trash2 size={14} />
                      삭제
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};