import React, { useState, useEffect } from 'react';
import {
  BarChart3,
  TrendingUp,
  AlertTriangle,
  Activity,
  Clock,
  Download,
  Bell,
  X,
  CheckCircle,
  XCircle,
  Info,
  Zap,
  Server,
  Globe,
  Users
} from 'lucide-react';
import './ALBDashboard.css';

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

interface ALBData {
  metrics: MetricCard[];
  trafficChart: ChartData[];
  statusChart: ChartData[];
  methodChart: ChartData[];
  topEndpoints: ChartData[];
  targetGroups: ChartData[];
  alerts: Alert[];
}

// ALB Access Logs 분석 결과 (127건)
// Status: 200 85건, 201 15건, 204 5건, 404 7건, 500 4건, 502 4건, 503 5건, 504 2건
const ALB_DATA: ALBData = {
  metrics: [
    {
      id: '1',
      title: '총 요청 수',
      value: '127',
      change: 12.3,
      changeType: 'increase',
      icon: <Activity size={24} />,
      color: '#4ecdc4'
    },
    {
      id: '2',
      title: '성공률',
      value: '82.7%',
      change: 2.1,
      changeType: 'increase',
      icon: <CheckCircle size={24} />,
      color: '#2ecc71'
    },
    {
      id: '3',
      title: '에러율',
      value: '17.3%',
      change: -1.5,
      changeType: 'decrease',
      icon: <AlertTriangle size={24} />,
      color: '#e74c3c'
    },
    {
      id: '4',
      title: '평균 응답시간',
      value: '312ms',
      change: -8.2,
      changeType: 'decrease',
      icon: <Clock size={24} />,
      color: '#3498db'
    },
    {
      id: '5',
      title: '총 전송량',
      value: '4.2MB',
      change: 15.7,
      changeType: 'increase',
      icon: <Server size={24} />,
      color: '#9b59b6'
    },
    {
      id: '6',
      title: '고유 클라이언트',
      value: '24',
      change: 5.3,
      changeType: 'increase',
      icon: <Users size={24} />,
      color: '#f39c12'
    }
  ],
  trafficChart: [
    { label: '11/18', value: 20 },
    { label: '11/19', value: 14 },
    { label: '11/20', value: 22 },
    { label: '11/21', value: 18 },
    { label: '11/22', value: 15 },
    { label: '11/23', value: 19 },
    { label: '11/24', value: 12 },
    { label: '11/25', value: 7 }
  ],
  statusChart: [
    { label: '200 OK', value: 85, color: '#2ecc71' },
    { label: '201 Created', value: 15, color: '#27ae60' },
    { label: '204 No Content', value: 5, color: '#1abc9c' },
    { label: '404 Not Found', value: 7, color: '#f39c12' },
    { label: '500 Internal', value: 4, color: '#e74c3c' },
    { label: '502 Bad Gateway', value: 4, color: '#c0392b' },
    { label: '503 Unavailable', value: 5, color: '#d35400' },
    { label: '504 Timeout', value: 2, color: '#e67e22' }
  ],
  methodChart: [
    { label: 'GET', value: 78, color: '#3498db' },
    { label: 'POST', value: 32, color: '#2ecc71' },
    { label: 'PUT', value: 8, color: '#f39c12' },
    { label: 'DELETE', value: 9, color: '#e74c3c' }
  ],
  topEndpoints: [
    { label: '/api/v1/users', value: 28 },
    { label: '/api/v1/orders', value: 18 },
    { label: '/api/v1/products/*', value: 15 },
    { label: '/api/v1/reports/daily', value: 9 },
    { label: '/api/v1/reports/monthly', value: 7 },
    { label: '/health', value: 6 },
    { label: '/metrics', value: 5 },
    { label: '/api/v1/admin/settings', value: 5 }
  ],
  targetGroups: [
    { label: '10.0.1.50:8080', value: 22, color: '#3498db' },
    { label: '10.0.1.51:8080', value: 20, color: '#2ecc71' },
    { label: '10.0.1.52:8080', value: 18, color: '#9b59b6' },
    { label: '10.0.2.50:8080', value: 24, color: '#f39c12' },
    { label: '10.0.2.51:8080', value: 28, color: '#e74c3c' },
    { label: 'Lambda (실패)', value: 4, color: '#95a5a6' }
  ],
  alerts: [
    {
      id: '1',
      type: 'error',
      title: '502 Bad Gateway 발생',
      message: '/api/v1/batch 엔드포인트에서 LambdaInvalidResponse 오류가 4회 발생했습니다.',
      timestamp: new Date(Date.now() - 15 * 60 * 1000),
      isRead: false
    },
    {
      id: '2',
      type: 'error',
      title: '500 Internal Server Error',
      message: '/api/v1/process 엔드포인트에서 서버 오류가 4회 발생했습니다. 평균 응답시간 3.8초',
      timestamp: new Date(Date.now() - 30 * 60 * 1000),
      isRead: false
    },
    {
      id: '3',
      type: 'warning',
      title: '404 Not Found 증가',
      message: '/api/v1/invalid, /api/v1/users/99999 등 존재하지 않는 리소스 요청이 7회 감지되었습니다.',
      timestamp: new Date(Date.now() - 1 * 60 * 60 * 1000),
      isRead: false
    },
    {
      id: '4',
      type: 'info',
      title: '트래픽 정상',
      message: '대부분의 요청이 정상 처리되고 있습니다. 성공률 82.7%',
      timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000),
      isRead: true
    }
  ]
};

export const ALBDashboard: React.FC = () => {
  const [data, setData] = useState<ALBData>(ALB_DATA);
  const [showAlerts] = useState(true);

  useEffect(() => {
    const interval = setInterval(() => {
      setData(prev => ({
        ...prev,
        metrics: prev.metrics.map(metric => ({
          ...metric,
          change: metric.change + (Math.random() - 0.5) * 1.5
        }))
      }));
    }, 30000);
    return () => clearInterval(interval);
  }, []);

  const markAlertAsRead = (alertId: string) => {
    setData(prev => ({
      ...prev,
      alerts: prev.alerts.map(alert =>
        alert.id === alertId ? { ...alert, isRead: true } : alert
      )
    }));
  };

  const dismissAlert = (alertId: string) => {
    setData(prev => ({
      ...prev,
      alerts: prev.alerts.filter(alert => alert.id !== alertId)
    }));
  };

  const exportData = (type: string) => {
    let dataToExport: ChartData[] = [];
    switch(type) {
      case 'traffic': dataToExport = data.trafficChart; break;
      case 'status': dataToExport = data.statusChart; break;
      case 'method': dataToExport = data.methodChart; break;
      case 'endpoints': dataToExport = data.topEndpoints; break;
      case 'targets': dataToExport = data.targetGroups; break;
    }
    
    const csv = [
      ['Label', 'Value'],
      ...dataToExport.map(item => [item.label, item.value])
    ].map(row => row.join(',')).join('\n');
    
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `alb_${type}_data.csv`;
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
    
    if (diffMins < 60) return `${diffMins}분 전`;
    if (diffHours < 24) return `${diffHours}시간 전`;
    return `${Math.floor(diffHours / 24)}일 전`;
  };

  const unreadAlertsCount = data.alerts.filter(alert => !alert.isRead).length;
  const totalRequests = data.methodChart.reduce((sum, item) => sum + item.value, 0);

  return (
    <div className="alb-dashboard">
      <div className="dashboard-header">
        <div className="header-title">
          <img src="/image/ALB.png" alt="ALB" className="header-service-icon" />
          <h2>ALB Access Logs 대시보드</h2>
          <span className="live-indicator">
            <span className="live-dot"></span>
            실시간
          </span>
        </div>
        

      </div>

      {/* 실시간 알림 */}
      {showAlerts && data.alerts.filter(alert => !alert.isRead).length > 0 && (
        <div className="alerts-section">
          <div className="alerts-header">
            <h3><Zap size={20} /> 실시간 알림</h3>
          </div>
          <div className="alerts-list">
            {data.alerts.filter(alert => !alert.isRead).slice(0, 3).map(alert => (
              <div key={alert.id} className={`alert-item ${alert.type}`}>
                <div className="alert-icon">{getAlertIcon(alert.type)}</div>
                <div className="alert-content">
                  <div className="alert-title">{alert.title}</div>
                  <div className="alert-message">{alert.message}</div>
                  <div className="alert-time">{formatTimeAgo(alert.timestamp)}</div>
                </div>
                <div className="alert-actions">
                  <button className="alert-action-button" onClick={() => dismissAlert(alert.id)} title="알림 삭제">
                    <X size={16} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 메트릭 카드 */}
      <div className="metrics-grid six-columns">
        {data.metrics.map(metric => (
          <div key={metric.id} className="metric-card">
            <div className="metric-header">
              <div className="metric-icon" style={{ color: metric.color }}>{metric.icon}</div>
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
        {/* 일별 트래픽 */}
        <div className="chart-card">
          <div className="chart-header">
            <h3><Activity size={20} /> 일별 요청 추이</h3>
            <button className="export-button" onClick={() => exportData('traffic')}>
              <Download size={14} /> 내보내기
            </button>
          </div>
          <div className="chart-container">
            <div className="bar-chart">
              {data.trafficChart.map((item, index) => (
                <div key={index} className="bar-item">
                  <div
                    className="bar"
                    style={{
                      height: `${(item.value / Math.max(...data.trafficChart.map(d => d.value))) * 100}%`
                    }}
                  >
                    <div className="bar-value">{item.value}</div>
                  </div>
                  <div className="bar-label">{item.label}</div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* HTTP 상태 코드 */}
        <div className="chart-card">
          <div className="chart-header">
            <h3><BarChart3 size={20} /> HTTP 상태 코드</h3>
            <button className="export-button" onClick={() => exportData('status')}>
              <Download size={14} /> 내보내기
            </button>
          </div>
          <div className="chart-container">
            <div className="status-chart">
              {data.statusChart.map((item, index) => (
                <div key={index} className="status-row">
                  <div className="status-info">
                    <div className="status-color" style={{ backgroundColor: item.color }}></div>
                    <span className="status-label">{item.label}</span>
                  </div>
                  <div className="status-bar-wrapper">
                    <div className="status-bar-track">
                      <div
                        className="status-bar-fill"
                        style={{
                          width: `${(item.value / Math.max(...data.statusChart.map(d => d.value))) * 100}%`,
                          backgroundColor: item.color
                        }}
                      ></div>
                    </div>
                    <span className="status-value">{item.value}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* HTTP 메서드 */}
        <div className="chart-card">
          <div className="chart-header">
            <h3><Globe size={20} /> HTTP 메서드</h3>
            <button className="export-button" onClick={() => exportData('method')}>
              <Download size={14} /> 내보내기
            </button>
          </div>
          <div className="chart-container">
            <div className="method-chart">
              {data.methodChart.map((item, index) => (
                <div key={index} className="method-item">
                  <div className="method-info">
                    <div className="method-color" style={{ backgroundColor: item.color }}></div>
                    <span className="method-label">{item.label}</span>
                  </div>
                  <div className="method-stats">
                    <span className="method-value">{item.value}</span>
                    <span className="method-percent">({((item.value / totalRequests) * 100).toFixed(1)}%)</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* 타겟 그룹 */}
        <div className="chart-card">
          <div className="chart-header">
            <h3><Server size={20} /> 타겟 그룹 분포</h3>
            <button className="export-button" onClick={() => exportData('targets')}>
              <Download size={14} /> 내보내기
            </button>
          </div>
          <div className="chart-container">
            <div className="target-chart">
              {data.targetGroups.map((item, index) => (
                <div key={index} className="target-row">
                  <div className="target-info">
                    <span className="target-label">{item.label}</span>
                  </div>
                  <div className="target-bar-wrapper">
                    <div className="target-bar-track">
                      <div
                        className="target-bar-fill"
                        style={{
                          width: `${(item.value / Math.max(...data.targetGroups.map(d => d.value))) * 100}%`,
                          backgroundColor: item.color
                        }}
                      ></div>
                    </div>
                    <span className="target-value">{item.value}건</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* 인기 엔드포인트 */}
        <div className="chart-card full-width">
          <div className="chart-header">
            <h3><Globe size={20} /> 인기 엔드포인트 TOP 8</h3>
            <button className="export-button" onClick={() => exportData('endpoints')}>
              <Download size={14} /> 내보내기
            </button>
          </div>
          <div className="chart-container">
            <div className="endpoints-grid">
              {data.topEndpoints.map((item, index) => (
                <div key={index} className="endpoint-item">
                  <div className="endpoint-rank">#{index + 1}</div>
                  <div className="endpoint-info">
                    <div className="endpoint-path">{item.label}</div>
                    <div className="endpoint-bar-track">
                      <div
                        className="endpoint-bar-fill"
                        style={{
                          width: `${(item.value / Math.max(...data.topEndpoints.map(d => d.value))) * 100}%`
                        }}
                      ></div>
                    </div>
                  </div>
                  <div className="endpoint-value">{item.value}건</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
