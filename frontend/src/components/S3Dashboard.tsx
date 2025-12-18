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
  HardDrive,
  Users,
  FileText,
  Upload,
  Trash2,
  Eye
} from 'lucide-react';
import './S3Dashboard.css';

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

interface S3Data {
  metrics: MetricCard[];
  trafficChart: ChartData[];
  operationsChart: ChartData[];
  statusChart: ChartData[];
  topObjects: ChartData[];
  requesterChart: ChartData[];
  alerts: Alert[];
}

// S3 Access Logs 분석 결과 (123건)
// Operations: GET 35, PUT 30, DELETE 53, 기타 5
// Status: 200 47, 204 53, 304 1, 206 2, 403 5, 404 5, 500 5, 503 8
const S3_DATA: S3Data = {
  metrics: [
    {
      id: '1',
      title: '총 요청 수',
      value: '123',
      change: 8.5,
      changeType: 'increase',
      icon: <Activity size={24} />,
      color: '#4ecdc4'
    },
    {
      id: '2',
      title: '총 전송량',
      value: '2.1GB',
      change: 15.3,
      changeType: 'increase',
      icon: <HardDrive size={24} />,
      color: '#3498db'
    },
    {
      id: '3',
      title: '에러율',
      value: '18.7%',
      change: 2.4,
      changeType: 'increase',
      icon: <AlertTriangle size={24} />,
      color: '#e74c3c'
    },
    {
      id: '4',
      title: '평균 응답시간',
      value: '892ms',
      change: -12.1,
      changeType: 'decrease',
      icon: <Clock size={24} />,
      color: '#9b59b6'
    },
    {
      id: '5',
      title: '고유 요청자',
      value: '14',
      change: 4.2,
      changeType: 'increase',
      icon: <Users size={24} />,
      color: '#f39c12'
    },
    {
      id: '6',
      title: '고유 객체',
      value: '42',
      change: 6.8,
      changeType: 'increase',
      icon: <FileText size={24} />,
      color: '#2ecc71'
    }
  ],
  trafficChart: [
    { label: '11/18', value: 21 },
    { label: '11/19', value: 12 },
    { label: '11/20', value: 16 },
    { label: '11/21', value: 18 },
    { label: '11/22', value: 11 },
    { label: '11/23', value: 14 },
    { label: '11/24', value: 16 },
    { label: '11/25', value: 15 }
  ],
  operationsChart: [
    { label: 'DELETE', value: 53, color: '#e74c3c' },
    { label: 'GET', value: 35, color: '#3498db' },
    { label: 'PUT', value: 30, color: '#2ecc71' },
    { label: 'HEAD', value: 3, color: '#f39c12' },
    { label: 'LIST', value: 2, color: '#9b59b6' }
  ],
  statusChart: [
    { label: '204 No Content', value: 53, color: '#95a5a6' },
    { label: '200 OK', value: 47, color: '#2ecc71' },
    { label: '503 SlowDown', value: 8, color: '#e74c3c' },
    { label: '500 Internal', value: 5, color: '#c0392b' },
    { label: '404 NoSuchKey', value: 5, color: '#f39c12' },
    { label: '403 AccessDenied', value: 5, color: '#9b59b6' }
  ],
  topObjects: [
    { label: 'cache/session_index.cache', value: 18 },
    { label: 'temp/old_file.tmp', value: 10 },
    { label: 'results/output.json', value: 10 },
    { label: 'data/etl/processed/daily_stats.csv', value: 8 },
    { label: 'data/upload.csv', value: 7 },
    { label: 'temp/session_*.dat', value: 12 },
    { label: 'metrics/daily/*.json', value: 6 },
    { label: 'notifications/email_queue.json', value: 5 }
  ],
  requesterChart: [
    { label: 'GlueRole', value: 18, color: '#3498db' },
    { label: 'ECSRole', value: 16, color: '#2ecc71' },
    { label: 'LambdaRole', value: 15, color: '#f39c12' },
    { label: 'datascientist', value: 14, color: '#9b59b6' },
    { label: 'admin', value: 13, color: '#e74c3c' },
    { label: 'developer', value: 13, color: '#1abc9c' },
    { label: 'analyst', value: 12, color: '#34495e' },
    { label: 'StepFunctionsRole', value: 10, color: '#e67e22' },
    { label: 'EC2Role', value: 7, color: '#7f8c8d' },
    { label: 'Anonymous', value: 5, color: '#bdc3c7' }
  ],
  alerts: [
    {
      id: '1',
      type: 'error',
      title: '503 SlowDown 다수 발생',
      message: 'database/backup.sql, uploads/document.pdf 업로드 시 요청 제한(SlowDown) 오류가 8회 발생했습니다.',
      timestamp: new Date(Date.now() - 20 * 60 * 1000),
      isRead: false
    },
    {
      id: '2',
      type: 'error',
      title: '500 Internal Error',
      message: 'backups/*.tar.gz, archive/historical_data.zip 다운로드 시 내부 오류가 5회 발생했습니다.',
      timestamp: new Date(Date.now() - 45 * 60 * 1000),
      isRead: false
    },
    {
      id: '3',
      type: 'warning',
      title: '403 AccessDenied 접근 시도',
      message: 'private/secret.txt, private/credentials.json, admin/logs/access.log에 대한 무단 접근이 5회 감지되었습니다.',
      timestamp: new Date(Date.now() - 1 * 60 * 60 * 1000),
      isRead: false
    },
    {
      id: '4',
      type: 'info',
      title: '대용량 파일 전송 완료',
      message: 'ml/model_v2.pkl (512MB), media/video/product_demo.mp4 (1GB) 파일이 성공적으로 전송되었습니다.',
      timestamp: new Date(Date.now() - 3 * 60 * 60 * 1000),
      isRead: true
    }
  ]
};

export const S3Dashboard: React.FC = () => {
  const [data, setData] = useState<S3Data>(S3_DATA);
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
      case 'operations': dataToExport = data.operationsChart; break;
      case 'status': dataToExport = data.statusChart; break;
      case 'objects': dataToExport = data.topObjects; break;
      case 'requesters': dataToExport = data.requesterChart; break;
    }
    
    const csv = [
      ['Label', 'Value'],
      ...dataToExport.map(item => [item.label, item.value])
    ].map(row => row.join(',')).join('\n');
    
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `s3_${type}_data.csv`;
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

  const getOperationIcon = (op: string) => {
    switch (op) {
      case 'GET': return <Download size={14} />;
      case 'PUT': return <Upload size={14} />;
      case 'DELETE': return <Trash2 size={14} />;
      case 'HEAD': return <Eye size={14} />;
      default: return <FileText size={14} />;
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
  const totalOperations = data.operationsChart.reduce((sum, item) => sum + item.value, 0);
  const totalStatus = data.statusChart.reduce((sum, item) => sum + item.value, 0);

  return (
    <div className="s3-dashboard">
      <div className="dashboard-header">
        <div className="header-title">
          <img src="/image/S3.png" alt="S3" className="header-service-icon" />
          <h2>S3 Access Logs 대시보드</h2>
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
                      backgroundColor: '#ff9500'
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

        {/* 작업 유형 */}
        <div className="chart-card">
          <div className="chart-header">
            <h3><FileText size={20} /> 작업 유형별 분포</h3>
            <button className="export-button" onClick={() => exportData('operations')}>
              <Download size={14} /> 내보내기
            </button>
          </div>
          <div className="chart-container">
            <div className="operations-chart">
              <div className="operations-visual">
                {data.operationsChart.map((item, index) => (
                  <div key={index} className="operation-row">
                    <div className="operation-info">
                      <span className="operation-icon" style={{ color: item.color }}>
                        {getOperationIcon(item.label)}
                      </span>
                      <span className="operation-label">{item.label}</span>
                    </div>
                    <div className="operation-bar-wrapper">
                      <div className="operation-bar-track">
                        <div
                          className="operation-bar-fill"
                          style={{
                            width: `${(item.value / totalOperations) * 100}%`,
                            backgroundColor: item.color
                          }}
                        ></div>
                      </div>
                      <span className="operation-value">{item.value}</span>
                      <span className="operation-percent">({((item.value / totalOperations) * 100).toFixed(1)}%)</span>
                    </div>
                  </div>
                ))}
              </div>
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
                          width: `${(item.value / totalStatus) * 100}%`,
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

        {/* 요청자별 분포 */}
        <div className="chart-card">
          <div className="chart-header">
            <h3><Users size={20} /> 요청자별 분포</h3>
            <button className="export-button" onClick={() => exportData('requesters')}>
              <Download size={14} /> 내보내기
            </button>
          </div>
          <div className="chart-container">
            <div className="requester-chart">
              {data.requesterChart.slice(0, 8).map((item, index) => (
                <div key={index} className="requester-row">
                  <div className="requester-info">
                    <span className="requester-rank">#{index + 1}</span>
                    <span className="requester-label">{item.label}</span>
                  </div>
                  <div className="requester-bar-wrapper">
                    <div className="requester-bar-track">
                      <div
                        className="requester-bar-fill"
                        style={{
                          width: `${(item.value / Math.max(...data.requesterChart.map(d => d.value))) * 100}%`,
                          backgroundColor: item.color
                        }}
                      ></div>
                    </div>
                    <span className="requester-value">{item.value}건</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* 인기 객체 */}
        <div className="chart-card full-width">
          <div className="chart-header">
            <h3><HardDrive size={20} /> 자주 접근되는 객체 TOP 8</h3>
            <button className="export-button" onClick={() => exportData('objects')}>
              <Download size={14} /> 내보내기
            </button>
          </div>
          <div className="chart-container">
            <div className="objects-grid">
              {data.topObjects.map((item, index) => (
                <div key={index} className="object-item">
                  <div className="object-rank">#{index + 1}</div>
                  <div className="object-info">
                    <div className="object-path">{item.label}</div>
                    <div className="object-bar-track">
                      <div
                        className="object-bar-fill"
                        style={{
                          width: `${(item.value / Math.max(...data.topObjects.map(d => d.value))) * 100}%`
                        }}
                      ></div>
                    </div>
                  </div>
                  <div className="object-value">{item.value}건</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
