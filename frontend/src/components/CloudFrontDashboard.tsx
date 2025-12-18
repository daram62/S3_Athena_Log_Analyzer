import React, { useState, useEffect } from 'react';
import {
  TrendingUp,
  AlertTriangle,
  Activity,
  Globe,
  Clock,
  Download,
  Bell,
  X,
  CheckCircle,
  XCircle,
  Info,
  Zap,
  Server,
  HardDrive,
  MapPin
} from 'lucide-react';
import './CloudFrontDashboard.css';

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

interface CloudFrontData {
  metrics: MetricCard[];
  trafficChart: ChartData[];
  cacheChart: ChartData[];
  edgeLocations: ChartData[];
  contentTypes: ChartData[];
  topResources: ChartData[];
  alerts: Alert[];
}

// CloudFront 로그 분석 결과 (127건)
// Hit: 78건 (61.4%), Miss: 30건 (23.6%), Error: 17건 (13.4%), Redirect: 7건 (5.5%)
// 총 전송량: ~450MB, 평균 응답시간: 0.065초
const CLOUDFRONT_DATA: CloudFrontData = {
  metrics: [
    {
      id: '1',
      title: '총 요청 수',
      value: '127',
      change: 12.5,
      changeType: 'increase',
      icon: <Activity size={24} />,
      color: '#4ecdc4'
    },
    {
      id: '2',
      title: '캐시 적중률',
      value: '61.4%',
      change: 5.2,
      changeType: 'increase',
      icon: <Zap size={24} />,
      color: '#2ecc71'
    },
    {
      id: '3',
      title: '에러율',
      value: '13.4%',
      change: -2.1,
      changeType: 'decrease',
      icon: <AlertTriangle size={24} />,
      color: '#e74c3c'
    },
    {
      id: '4',
      title: '평균 응답시간',
      value: '65ms',
      change: -8.3,
      changeType: 'decrease',
      icon: <Clock size={24} />,
      color: '#3498db'
    },
    {
      id: '5',
      title: '총 전송량',
      value: '453MB',
      change: 18.7,
      changeType: 'increase',
      icon: <HardDrive size={24} />,
      color: '#9b59b6'
    },
    {
      id: '6',
      title: '고유 클라이언트',
      value: '18',
      change: 3.4,
      changeType: 'increase',
      icon: <Globe size={24} />,
      color: '#f39c12'
    }
  ],
  trafficChart: [
    { label: '11/18', value: 11 },
    { label: '11/19', value: 24 },
    { label: '11/20', value: 22 },
    { label: '11/21', value: 18 },
    { label: '11/22', value: 14 },
    { label: '11/23', value: 17 },
    { label: '11/24', value: 13 },
    { label: '11/25', value: 8 }
  ],
  cacheChart: [
    { label: 'Hit', value: 78, color: '#2ecc71' },
    { label: 'Miss', value: 30, color: '#f39c12' },
    { label: 'Error', value: 12, color: '#e74c3c' },
    { label: 'Redirect', value: 7, color: '#3498db' }
  ],
  edgeLocations: [
    { label: 'ICN (서울)', value: 28, color: '#4ecdc4' },
    { label: 'NRT (도쿄)', value: 18, color: '#45b7d1' },
    { label: 'LAX (LA)', value: 17, color: '#96ceb4' },
    { label: 'SIN (싱가포르)', value: 15, color: '#ffeaa7' },
    { label: 'LHR (런던)', value: 9, color: '#dfe6e9' },
    { label: 'FRA (프랑크푸르트)', value: 9, color: '#a29bfe' },
    { label: 'SEA (시애틀)', value: 7, color: '#fd79a8' },
    { label: 'JFK (뉴욕)', value: 7, color: '#00b894' },
    { label: 'SYD (시드니)', value: 6, color: '#e17055' },
    { label: 'HKG (홍콩)', value: 6, color: '#74b9ff' },
    { label: '기타', value: 5, color: '#b2bec3' }
  ],
  contentTypes: [
    { label: 'video/mp4', value: 15, color: '#e74c3c' },
    { label: 'image/jpeg', value: 14, color: '#3498db' },
    { label: 'application/javascript', value: 14, color: '#f1c40f' },
    { label: 'text/css', value: 11, color: '#2ecc71' },
    { label: 'image/png', value: 11, color: '#9b59b6' },
    { label: 'application/json', value: 10, color: '#1abc9c' },
    { label: 'font/woff2', value: 9, color: '#e67e22' },
    { label: 'application/pdf', value: 8, color: '#34495e' },
    { label: 'application/zip', value: 3, color: '#7f8c8d' },
    { label: 'text/html', value: 8, color: '#16a085' },
    { label: 'image/x-icon', value: 5, color: '#8e44ad' }
  ],
  topResources: [
    { label: '/videos/demo.mp4', value: 9 },
    { label: '/videos/intro.mp4', value: 8 },
    { label: '/js/jquery.min.js', value: 8 },
    { label: '/images/avatar.png', value: 8 },
    { label: '/css/bootstrap.min.css', value: 8 },
    { label: '/downloads/manual.pdf', value: 7 },
    { label: '/images/product-1.jpg', value: 7 },
    { label: '/js/app.js', value: 7 },
    { label: '/downloads/app-v1.2.3.zip', value: 3 },
    { label: '/images/banner.jpg', value: 6 }
  ],
  alerts: [
    {
      id: '1',
      type: 'error',
      title: '404 Not Found 다수 발생',
      message: '/temp/file.pdf, /nonexistent.html, /api/v1/invalid 등에서 404 오류가 총 8회 발생했습니다.',
      timestamp: new Date(Date.now() - 15 * 60 * 1000),
      isRead: false
    },
    {
      id: '2',
      type: 'warning',
      title: '403 Forbidden 접근 시도',
      message: '/admin/secret 경로에 대한 무단 접근 시도가 3회 감지되었습니다.',
      timestamp: new Date(Date.now() - 30 * 60 * 1000),
      isRead: false
    },
    {
      id: '3',
      type: 'info',
      title: '캐시 미스율 증가',
      message: '새로운 콘텐츠 배포로 인해 캐시 미스율이 일시적으로 23.6%로 증가했습니다.',
      timestamp: new Date(Date.now() - 1 * 60 * 60 * 1000),
      isRead: false
    },
    {
      id: '4',
      type: 'success',
      title: '대용량 파일 전송 완료',
      message: 'app-v1.2.3.zip (45MB) 파일이 3회 성공적으로 전송되었습니다.',
      timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000),
      isRead: true
    }
  ]
};

export const CloudFrontDashboard: React.FC = () => {
  const [data, setData] = useState<CloudFrontData>(CLOUDFRONT_DATA);
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
      case 'cache': dataToExport = data.cacheChart; break;
      case 'edge': dataToExport = data.edgeLocations; break;
      case 'content': dataToExport = data.contentTypes; break;
      case 'resources': dataToExport = data.topResources; break;
    }
    
    const csv = [
      ['Label', 'Value'],
      ...dataToExport.map(item => [item.label, item.value])
    ].map(row => row.join(',')).join('\n');
    
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `cloudfront_${type}_data.csv`;
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
  const totalCacheRequests = data.cacheChart.reduce((sum, item) => sum + item.value, 0);

  return (
    <div className="cloudfront-dashboard">
      <div className="dashboard-header">
        <div className="header-title">
          <img src="/image/Cloudfront.png" alt="CloudFront" className="header-service-icon" />
          <h2>CloudFront 분석 대시보드</h2>
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
                      height: `${(item.value / Math.max(...data.trafficChart.map(d => d.value))) * 100}%`,
                      backgroundColor: '#4ecdc4'
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

        {/* 캐시 성능 */}
        <div className="chart-card">
          <div className="chart-header">
            <h3><Zap size={20} /> 캐시 성능</h3>
            <button className="export-button" onClick={() => exportData('cache')}>
              <Download size={14} /> 내보내기
            </button>
          </div>
          <div className="chart-container">
            <div className="cache-chart">
              <div className="cache-visual">
                <div className="cache-ring">
                  <svg viewBox="0 0 100 100">
                    {data.cacheChart.reduce((acc, item, index) => {
                      const percentage = (item.value / totalCacheRequests) * 100;
                      const prevPercentage = data.cacheChart.slice(0, index).reduce((sum, i) => sum + (i.value / totalCacheRequests) * 100, 0);
                      const strokeDasharray = `${percentage * 2.51} ${251 - percentage * 2.51}`;
                      const strokeDashoffset = -prevPercentage * 2.51;
                      acc.push(
                        <circle
                          key={index}
                          cx="50" cy="50" r="40"
                          fill="none"
                          stroke={item.color}
                          strokeWidth="12"
                          strokeDasharray={strokeDasharray}
                          strokeDashoffset={strokeDashoffset}
                          transform="rotate(-90 50 50)"
                        />
                      );
                      return acc;
                    }, [] as JSX.Element[])}
                  </svg>
                  <div className="cache-center">
                    <div className="cache-hit-rate">61.4%</div>
                    <div className="cache-label">Hit Rate</div>
                  </div>
                </div>
              </div>
              <div className="cache-legend">
                {data.cacheChart.map((item, index) => (
                  <div key={index} className="legend-item">
                    <div className="legend-color" style={{ backgroundColor: item.color }}></div>
                    <span className="legend-label">{item.label}</span>
                    <span className="legend-value">{item.value}</span>
                    <span className="legend-percent">({((item.value / totalCacheRequests) * 100).toFixed(1)}%)</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Edge Location 분포 */}
        <div className="chart-card">
          <div className="chart-header">
            <h3><MapPin size={20} /> Edge Location 분포</h3>
            <button className="export-button" onClick={() => exportData('edge')}>
              <Download size={14} /> 내보내기
            </button>
          </div>
          <div className="chart-container">
            <div className="edge-chart">
              {data.edgeLocations.slice(0, 8).map((item, index) => (
                <div key={index} className="edge-item">
                  <div className="edge-info">
                    <span className="edge-rank">#{index + 1}</span>
                    <span className="edge-label">{item.label}</span>
                    <span className="edge-value">{item.value}건</span>
                  </div>
                  <div className="edge-bar-track">
                    <div
                      className="edge-bar-fill"
                      style={{
                        width: `${(item.value / Math.max(...data.edgeLocations.map(d => d.value))) * 100}%`,
                        backgroundColor: item.color
                      }}
                    ></div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* 콘텐츠 타입 */}
        <div className="chart-card">
          <div className="chart-header">
            <h3><Server size={20} /> 콘텐츠 타입별 요청</h3>
            <button className="export-button" onClick={() => exportData('content')}>
              <Download size={14} /> 내보내기
            </button>
          </div>
          <div className="chart-container">
            <div className="content-type-chart">
              {data.contentTypes.slice(0, 8).map((item, index) => (
                <div key={index} className="content-item">
                  <div className="content-info">
                    <div className="content-color" style={{ backgroundColor: item.color }}></div>
                    <span className="content-label">{item.label}</span>
                  </div>
                  <div className="content-bar-wrapper">
                    <div className="content-bar-track">
                      <div
                        className="content-bar-fill"
                        style={{
                          width: `${(item.value / Math.max(...data.contentTypes.map(d => d.value))) * 100}%`,
                          backgroundColor: item.color
                        }}
                      ></div>
                    </div>
                    <span className="content-value">{item.value}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* 인기 리소스 */}
        <div className="chart-card full-width">
          <div className="chart-header">
            <h3><Globe size={20} /> 인기 리소스 TOP 10</h3>
            <button className="export-button" onClick={() => exportData('resources')}>
              <Download size={14} /> 내보내기
            </button>
          </div>
          <div className="chart-container">
            <div className="resources-grid">
              {data.topResources.map((item, index) => (
                <div key={index} className="resource-item">
                  <div className="resource-rank">#{index + 1}</div>
                  <div className="resource-info">
                    <div className="resource-path">{item.label}</div>
                    <div className="resource-bar-track">
                      <div
                        className="resource-bar-fill"
                        style={{
                          width: `${(item.value / Math.max(...data.topResources.map(d => d.value))) * 100}%`
                        }}
                      ></div>
                    </div>
                  </div>
                  <div className="resource-value">{item.value}건</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
