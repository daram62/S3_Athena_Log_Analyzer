import React, { useState, useEffect } from 'react';
import {
  BarChart3,
  TrendingUp,
  AlertTriangle,
  Activity,
  Users,
  Globe,
  Clock,
  Download,
  RefreshCw,
  Bell,
  X,
  CheckCircle,
  XCircle,
  Info,
  Zap
} from 'lucide-react';
import { useLanguage } from '../contexts/LanguageContext';
import './InsightsDashboard.css';

interface MetricCard {
  id: string;
  title: string;
  value: string | number;
  change: number;
  changeType: 'increase' | 'decrease' | 'neutral';
  icon: React.ReactNode;
  color: string;
}

interface ChartData {
  label: string;
  value: number;
  color?: string;
}

interface Alert {
  id: string;
  type: 'error' | 'warning' | 'info' | 'success';
  title: string;
  message: string;
  timestamp: Date;
  isRead: boolean;
}

interface InsightData {
  metrics: MetricCard[];
  trafficChart: ChartData[];
  errorChart: ChartData[];
  topPages: ChartData[];
  alerts: Alert[];
}

// 실제 샘플 로그 분석 결과 기반 데이터
// ALB: 127건, S3: 123건, CloudFront: 152건, VPC: 147건
const MOCK_DATA: InsightData = {
  metrics: [
    {
      id: '1',
      title: '총 요청 수',
      value: '549',
      change: 15.3,
      changeType: 'increase',
      icon: <Activity size={24} />,
      color: '#4ecdc4'
    },
    {
      id: '2',
      title: '고유 클라이언트 IP',
      value: '47',
      change: 8.3,
      changeType: 'increase',
      icon: <Users size={24} />,
      color: '#45b7d1'
    },
    {
      id: '3',
      title: '에러율',
      value: '11.8%',
      change: 3.2,
      changeType: 'increase',
      icon: <AlertTriangle size={24} />,
      color: '#f39c12'
    },
    {
      id: '4',
      title: '평균 응답시간',
      value: '312ms',
      change: -5.4,
      changeType: 'decrease',
      icon: <Clock size={24} />,
      color: '#e74c3c'
    }
  ],
  trafficChart: [
    { label: '11/18', value: 89 },
    { label: '11/19', value: 102 },
    { label: '11/20', value: 95 },
    { label: '11/21', value: 87 },
    { label: '11/22', value: 76 },
    { label: '11/23', value: 68 },
    { label: '11/24', value: 32 }
  ],
  errorChart: [
    { label: '404 Not Found', value: 7, color: '#e74c3c' },
    { label: '500 Server Error', value: 4, color: '#c0392b' },
    { label: '502 Bad Gateway', value: 4, color: '#d35400' },
    { label: '503 Unavailable', value: 5, color: '#e67e22' },
    { label: '504 Timeout', value: 4, color: '#f39c12' },
    { label: '403 Forbidden', value: 7, color: '#9b59b6' }
  ],
  topPages: [
    { label: '/api/v1/users', value: 28 },
    { label: '/api/v1/orders', value: 18 },
    { label: '/api/v1/products', value: 12 },
    { label: '/api/v1/reports/daily', value: 9 },
    { label: '/api/v1/admin/settings', value: 7 },
    { label: '/health', value: 6 },
    { label: '/api/v1/search', value: 5 }
  ],
  alerts: [
    {
      id: '1',
      type: 'error',
      title: 'Lambda 응답 오류 감지',
      message: '/api/v1/batch 엔드포인트에서 LambdaInvalidResponse 오류가 4회 발생했습니다.',
      timestamp: new Date(Date.now() - 10 * 60 * 1000),
      isRead: false
    },
    {
      id: '2',
      type: 'warning',
      title: '타임아웃 발생',
      message: '/api/v1/timeout 엔드포인트에서 30초 타임아웃이 4회 발생했습니다.',
      timestamp: new Date(Date.now() - 25 * 60 * 1000),
      isRead: false
    },
    {
      id: '3',
      type: 'warning',
      title: '503 Service Unavailable',
      message: '/api/v1/heavy 엔드포인트에서 서버 과부하로 인한 503 오류가 발생했습니다.',
      timestamp: new Date(Date.now() - 45 * 60 * 1000),
      isRead: false
    },
    {
      id: '4',
      type: 'info',
      title: '권한 없는 접근 시도',
      message: '/api/v1/admin/secret 엔드포인트에 대한 403 Forbidden 응답이 2회 발생했습니다.',
      timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000),
      isRead: true
    }
  ]
};

export const InsightsDashboard: React.FC = () => {
  const { t } = useLanguage();
  const [data, setData] = useState<InsightData>(MOCK_DATA);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [selectedTimeRange, setSelectedTimeRange] = useState('24h');
  const [showAlerts, setShowAlerts] = useState(true);

  // 데이터 새로고침
  const refreshData = async () => {
    setIsRefreshing(true);
    
    // 실제로는 API 호출
    setTimeout(() => {
      // 데이터 업데이트 시뮬레이션
      setData(prev => ({
        ...prev,
        metrics: prev.metrics.map(metric => ({
          ...metric,
          change: metric.change + (Math.random() - 0.5) * 5
        }))
      }));
      setIsRefreshing(false);
    }, 2000);
  };

  // 실시간 업데이트 시뮬레이션
  useEffect(() => {
    const interval = setInterval(() => {
      setData(prev => ({
        ...prev,
        metrics: prev.metrics.map(metric => ({
          ...metric,
          change: metric.change + (Math.random() - 0.5) * 2
        }))
      }));
    }, 30000); // 30초마다 업데이트

    return () => clearInterval(interval);
  }, []);

  // 알림 읽음 처리
  const markAlertAsRead = (alertId: string) => {
    setData(prev => ({
      ...prev,
      alerts: prev.alerts.map(alert =>
        alert.id === alertId ? { ...alert, isRead: true } : alert
      )
    }));
  };

  // 알림 삭제
  const dismissAlert = (alertId: string) => {
    setData(prev => ({
      ...prev,
      alerts: prev.alerts.filter(alert => alert.id !== alertId)
    }));
  };

  // 차트 데이터 내보내기
  const exportData = (type: string) => {
    const dataToExport = type === 'traffic' ? data.trafficChart : 
                        type === 'errors' ? data.errorChart : 
                        data.topPages;
    
    const csv = [
      ['Label', 'Value'],
      ...dataToExport.map(item => [item.label, item.value])
    ].map(row => row.join(',')).join('\n');
    
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${type}_data.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const getAlertIcon = (type: string) => {
    switch (type) {
      case 'error': return <XCircle size={20} />;
      case 'warning': return <AlertTriangle size={20} />;
      case 'info': return <Info size={20} />;
      case 'success': return <CheckCircle size={20} />;
      default: return <Bell size={20} />;
    }
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

  const unreadAlertsCount = data.alerts.filter(alert => !alert.isRead).length;

  return (
    <div className="insights-dashboard">
      <div className="dashboard-header">
        <div className="header-title">
          <BarChart3 className="header-icon" size={28} />
          <h2>인사이트 대시보드</h2>
          <span className="live-indicator">
            <span className="live-dot"></span>
            실시간
          </span>
        </div>
        
        <div className="header-controls">
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
            className="refresh-button"
            onClick={refreshData}
            disabled={isRefreshing}
          >
            <RefreshCw size={16} className={isRefreshing ? 'spinning' : ''} />
            새로고침
          </button>
          
          <button
            className={`alerts-toggle ${showAlerts ? 'active' : ''}`}
            onClick={() => setShowAlerts(!showAlerts)}
          >
            <Bell size={16} />
            알림 {unreadAlertsCount > 0 && (
              <span className="alert-badge">{unreadAlertsCount}</span>
            )}
          </button>
        </div>
      </div>

      {/* 실시간 알림 */}
      {showAlerts && data.alerts.filter(alert => !alert.isRead).length > 0 && (
        <div className="alerts-section">
          <div className="alerts-header">
            <h3>
              <Zap size={20} />
              실시간 알림
            </h3>
          </div>
          <div className="alerts-list">
            {data.alerts
              .filter(alert => !alert.isRead)
              .slice(0, 3)
              .map(alert => (
                <div key={alert.id} className={`alert-item ${alert.type}`}>
                  <div className="alert-icon">
                    {getAlertIcon(alert.type)}
                  </div>
                  <div className="alert-content">
                    <div className="alert-title">{alert.title}</div>
                    <div className="alert-message">{alert.message}</div>
                    <div className="alert-time">{formatTimeAgo(alert.timestamp)}</div>
                  </div>
                  <div className="alert-actions">
                    <button
                      className="alert-action-button"
                      onClick={() => markAlertAsRead(alert.id)}
                      title="읽음으로 표시"
                    >
                      <CheckCircle size={16} />
                    </button>
                    <button
                      className="alert-action-button"
                      onClick={() => dismissAlert(alert.id)}
                      title="알림 삭제"
                    >
                      <X size={16} />
                    </button>
                  </div>
                </div>
              ))}
          </div>
        </div>
      )}

      {/* 메트릭 카드 */}
      <div className="metrics-grid">
        {data.metrics.map(metric => (
          <div key={metric.id} className="metric-card">
            <div className="metric-header">
              <div className="metric-icon" style={{ color: metric.color }}>
                {metric.icon}
              </div>
              <div className="metric-title">{metric.title}</div>
            </div>
            <div className="metric-value">{metric.value}</div>
            <div className={`metric-change ${metric.changeType}`}>
              <TrendingUp size={16} />
              {metric.change > 0 ? '+' : ''}{metric.change.toFixed(1)}%
              <span className="change-period">vs 이전 기간</span>
            </div>
          </div>
        ))}
      </div>

      {/* 차트 섹션 */}
      <div className="charts-grid">
        {/* 트래픽 차트 */}
        <div className="chart-card">
          <div className="chart-header">
            <h3>
              <Activity size={20} />
              시간대별 트래픽
            </h3>
            <button
              className="export-button"
              onClick={() => exportData('traffic')}
            >
              <Download size={14} />
              내보내기
            </button>
          </div>
          <div className="chart-container">
            <div className="bar-chart">
              {data.trafficChart.map((item, index) => (
                <div key={index} className="bar-item">
                  <div
                    className="bar"
                    style={{
                      height: `${(item.value / Math.max(...data.trafficChart.map(d => d.value))) * 100}%`,
                      backgroundColor: '#4ecdc4'
                    }}
                  >
                    <div className="bar-value">{item.value.toLocaleString()}</div>
                  </div>
                  <div className="bar-label">{item.label}</div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* 에러 차트 */}
        <div className="chart-card">
          <div className="chart-header">
            <h3>
              <AlertTriangle size={20} />
              에러 상태 코드
            </h3>
            <button
              className="export-button"
              onClick={() => exportData('errors')}
            >
              <Download size={14} />
              내보내기
            </button>
          </div>
          <div className="chart-container">
            <div className="pie-chart">
              <div className="pie-chart-visual">
                {/* 간단한 도넛 차트 시뮬레이션 */}
                <div className="pie-center">
                  <div className="pie-total">
                    {data.errorChart.reduce((sum, item) => sum + item.value, 0)}
                  </div>
                  <div className="pie-label">총 에러</div>
                </div>
              </div>
              <div className="pie-legend">
                {data.errorChart.map((item, index) => (
                  <div key={index} className="legend-item">
                    <div
                      className="legend-color"
                      style={{ backgroundColor: item.color }}
                    ></div>
                    <span className="legend-label">{item.label}</span>
                    <span className="legend-value">{item.value}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* 인기 페이지 */}
        <div className="chart-card full-width">
          <div className="chart-header">
            <h3>
              <Globe size={20} />
              인기 페이지
            </h3>
            <button
              className="export-button"
              onClick={() => exportData('pages')}
            >
              <Download size={14} />
              내보내기
            </button>
          </div>
          <div className="chart-container">
            <div className="horizontal-bar-chart">
              {data.topPages.map((item, index) => (
                <div key={index} className="horizontal-bar-item">
                  <div className="bar-info">
                    <span className="bar-rank">#{index + 1}</span>
                    <span className="bar-label">{item.label}</span>
                    <span className="bar-value">{item.value.toLocaleString()}</span>
                  </div>
                  <div className="bar-track">
                    <div
                      className="bar-fill"
                      style={{
                        width: `${(item.value / Math.max(...data.topPages.map(d => d.value))) * 100}%`
                      }}
                    ></div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};