import React, { useState, useEffect } from 'react';
import {
  TrendingUp,
  AlertTriangle,
  Activity,
  Download,
  Bell,
  X,
  CheckCircle,
  XCircle,
  Info,
  Zap,
  Shield,
  ShieldOff,
  Network,
  Server,
  Globe,
  Lock
} from 'lucide-react';
import './VPCFlowDashboard.css';

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

interface VPCData {
  metrics: MetricCard[];
  actionChart: ChartData[];
  protocolChart: ChartData[];
  topPorts: ChartData[];
  topSources: ChartData[];
  topDestinations: ChartData[];
  rejectedIPs: ChartData[];
  alerts: Alert[];
}

// VPC Flow Logs 분석 결과 (147건)
// ACCEPT: 109건 (74.1%), REJECT: 38건 (25.9%)
// Protocol: TCP 115건, UDP 28건, ICMP 4건
const VPC_DATA: VPCData = {
  metrics: [
    {
      id: '1',
      title: '총 플로우',
      value: '147',
      change: 5.2,
      changeType: 'increase',
      icon: <Activity size={24} />,
      color: '#4ecdc4'
    },
    {
      id: '2',
      title: 'ACCEPT',
      value: '109',
      change: 3.8,
      changeType: 'increase',
      icon: <Shield size={24} />,
      color: '#2ecc71'
    },
    {
      id: '3',
      title: 'REJECT',
      value: '38',
      change: 12.4,
      changeType: 'increase',
      icon: <ShieldOff size={24} />,
      color: '#e74c3c'
    },
    {
      id: '4',
      title: '거부율',
      value: '25.9%',
      change: 4.1,
      changeType: 'increase',
      icon: <AlertTriangle size={24} />,
      color: '#f39c12'
    },
    {
      id: '5',
      title: '총 전송량',
      value: '42.8MB',
      change: 8.7,
      changeType: 'increase',
      icon: <Network size={24} />,
      color: '#3498db'
    },
    {
      id: '6',
      title: '고유 ENI',
      value: '8',
      change: 0,
      changeType: 'neutral',
      icon: <Server size={24} />,
      color: '#9b59b6'
    }
  ],
  actionChart: [
    { label: 'ACCEPT', value: 109, color: '#2ecc71' },
    { label: 'REJECT', value: 38, color: '#e74c3c' }
  ],
  protocolChart: [
    { label: 'TCP (6)', value: 115, color: '#3498db' },
    { label: 'UDP (17)', value: 28, color: '#9b59b6' },
    { label: 'ICMP (1)', value: 4, color: '#f39c12' }
  ],
  topPorts: [
    { label: '53 (DNS)', value: 14, color: '#3498db' },
    { label: '161 (SNMP)', value: 12, color: '#2ecc71' },
    { label: '25 (SMTP)', value: 10, color: '#f39c12' },
    { label: '123 (NTP)', value: 9, color: '#9b59b6' },
    { label: '3306 (MySQL)', value: 8, color: '#e74c3c' },
    { label: '80 (HTTP)', value: 8, color: '#1abc9c' },
    { label: '443 (HTTPS)', value: 7, color: '#34495e' },
    { label: '22 (SSH)', value: 6, color: '#e67e22' },
    { label: '8080 (HTTP-Alt)', value: 6, color: '#7f8c8d' },
    { label: '27017 (MongoDB)', value: 6, color: '#16a085' }
  ],
  topSources: [
    { label: '10.0.2.20', value: 16 },
    { label: '10.0.1.13', value: 14 },
    { label: '10.0.4.40', value: 13 },
    { label: '10.0.3.30', value: 12 },
    { label: '10.0.1.11', value: 11 },
    { label: '10.0.2.21', value: 10 },
    { label: '203.0.113.30', value: 10 },
    { label: '185.220.101.x', value: 18 }
  ],
  topDestinations: [
    { label: '10.0.1.13', value: 18 },
    { label: '10.0.3.30', value: 15 },
    { label: '10.0.2.20', value: 14 },
    { label: '10.0.1.11', value: 13 },
    { label: '10.0.3.31', value: 13 },
    { label: '10.0.1.12', value: 12 },
    { label: '10.0.4.40', value: 11 },
    { label: '10.0.2.22', value: 10 }
  ],
  rejectedIPs: [
    { label: '185.220.101.1', value: 9, color: '#e74c3c' },
    { label: '185.220.101.2', value: 9, color: '#c0392b' },
    { label: '45.142.120.1', value: 6, color: '#d35400' },
    { label: '8.8.4.4 / 8.8.8.8', value: 3, color: '#e67e22' },
    { label: '198.51.100.x', value: 4, color: '#f39c12' },
    { label: '192.168.100.x', value: 4, color: '#f1c40f' },
    { label: '54.180.0.x', value: 3, color: '#95a5a6' }
  ],
  alerts: [
    {
      id: '1',
      type: 'error',
      title: '악성 IP 스캔 탐지',
      message: '185.220.101.x (Tor Exit Node)에서 포트 135, 139, 445, 1433, 3389 스캔 시도가 18회 감지되었습니다.',
      timestamp: new Date(Date.now() - 10 * 60 * 1000),
      isRead: false
    },
    {
      id: '2',
      type: 'error',
      title: '무차별 대입 공격 의심',
      message: '45.142.120.1에서 SSH(22), RDP(3389), SQL(1433) 포트로 반복 접근 시도가 감지되었습니다.',
      timestamp: new Date(Date.now() - 25 * 60 * 1000),
      isRead: false
    },
    {
      id: '3',
      type: 'warning',
      title: 'SMB/NetBIOS 접근 차단',
      message: '외부에서 포트 139, 445로의 접근이 차단되었습니다. 보안 그룹 규칙이 정상 작동 중입니다.',
      timestamp: new Date(Date.now() - 1 * 60 * 60 * 1000),
      isRead: false
    },
    {
      id: '4',
      type: 'info',
      title: '내부 트래픽 정상',
      message: '10.0.x.x 대역 간 내부 통신이 정상적으로 이루어지고 있습니다. (109건 ACCEPT)',
      timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000),
      isRead: true
    }
  ]
};

export const VPCFlowDashboard: React.FC = () => {
  const [data, setData] = useState<VPCData>(VPC_DATA);
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
      case 'action': dataToExport = data.actionChart; break;
      case 'protocol': dataToExport = data.protocolChart; break;
      case 'ports': dataToExport = data.topPorts; break;
      case 'sources': dataToExport = data.topSources; break;
      case 'rejected': dataToExport = data.rejectedIPs; break;
    }
    
    const csv = [
      ['Label', 'Value'],
      ...dataToExport.map(item => [item.label, item.value])
    ].map(row => row.join(',')).join('\n');
    
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `vpc_${type}_data.csv`;
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
  const totalFlows = data.actionChart.reduce((sum, item) => sum + item.value, 0);

  return (
    <div className="vpc-dashboard">
      <div className="dashboard-header">
        <div className="header-title">
          <img src="/image/VPC.png" alt="VPC" className="header-service-icon" />
          <h2>VPC Flow Logs 대시보드</h2>
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
            <h3><Zap size={20} /> 보안 알림</h3>
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
        {/* ACCEPT/REJECT 분포 */}
        <div className="chart-card">
          <div className="chart-header">
            <h3><Shield size={20} /> 트래픽 허용/거부</h3>
            <button className="export-button" onClick={() => exportData('action')}>
              <Download size={14} /> 내보내기
            </button>
          </div>
          <div className="chart-container">
            <div className="action-chart">
              <div className="action-visual">
                <div className="action-donut">
                  <svg viewBox="0 0 100 100">
                    <circle cx="50" cy="50" r="40" fill="none" stroke="#2ecc71" strokeWidth="15"
                      strokeDasharray={`${(109/147)*251} ${251-(109/147)*251}`}
                      strokeDashoffset="0" transform="rotate(-90 50 50)" />
                    <circle cx="50" cy="50" r="40" fill="none" stroke="#e74c3c" strokeWidth="15"
                      strokeDasharray={`${(38/147)*251} ${251-(38/147)*251}`}
                      strokeDashoffset={`${-(109/147)*251}`} transform="rotate(-90 50 50)" />
                  </svg>
                  <div className="action-center">
                    <div className="action-total">{totalFlows}</div>
                    <div className="action-label">총 플로우</div>
                  </div>
                </div>
              </div>
              <div className="action-legend">
                {data.actionChart.map((item, index) => (
                  <div key={index} className="legend-row">
                    <div className="legend-info">
                      <div className="legend-color" style={{ backgroundColor: item.color }}></div>
                      <span className="legend-label">{item.label}</span>
                    </div>
                    <div className="legend-stats">
                      <span className="legend-value">{item.value}</span>
                      <span className="legend-percent">({((item.value / totalFlows) * 100).toFixed(1)}%)</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* 프로토콜 분포 */}
        <div className="chart-card">
          <div className="chart-header">
            <h3><Network size={20} /> 프로토콜 분포</h3>
            <button className="export-button" onClick={() => exportData('protocol')}>
              <Download size={14} /> 내보내기
            </button>
          </div>
          <div className="chart-container">
            <div className="protocol-chart">
              {data.protocolChart.map((item, index) => (
                <div key={index} className="protocol-row">
                  <div className="protocol-info">
                    <div className="protocol-color" style={{ backgroundColor: item.color }}></div>
                    <span className="protocol-label">{item.label}</span>
                  </div>
                  <div className="protocol-bar-wrapper">
                    <div className="protocol-bar-track">
                      <div
                        className="protocol-bar-fill"
                        style={{
                          width: `${(item.value / Math.max(...data.protocolChart.map(d => d.value))) * 100}%`,
                          backgroundColor: item.color
                        }}
                      ></div>
                    </div>
                    <span className="protocol-value">{item.value}</span>
                    <span className="protocol-percent">({((item.value / totalFlows) * 100).toFixed(1)}%)</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* 상위 포트 */}
        <div className="chart-card">
          <div className="chart-header">
            <h3><Lock size={20} /> 상위 목적지 포트</h3>
            <button className="export-button" onClick={() => exportData('ports')}>
              <Download size={14} /> 내보내기
            </button>
          </div>
          <div className="chart-container">
            <div className="ports-chart">
              {data.topPorts.slice(0, 8).map((item, index) => (
                <div key={index} className="port-row">
                  <div className="port-info">
                    <span className="port-rank">#{index + 1}</span>
                    <span className="port-label">{item.label}</span>
                  </div>
                  <div className="port-bar-wrapper">
                    <div className="port-bar-track">
                      <div
                        className="port-bar-fill"
                        style={{
                          width: `${(item.value / Math.max(...data.topPorts.map(d => d.value))) * 100}%`,
                          backgroundColor: item.color
                        }}
                      ></div>
                    </div>
                    <span className="port-value">{item.value}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* 차단된 IP */}
        <div className="chart-card">
          <div className="chart-header">
            <h3><ShieldOff size={20} /> 차단된 소스 IP</h3>
            <button className="export-button" onClick={() => exportData('rejected')}>
              <Download size={14} /> 내보내기
            </button>
          </div>
          <div className="chart-container">
            <div className="rejected-chart">
              {data.rejectedIPs.map((item, index) => (
                <div key={index} className="rejected-row">
                  <div className="rejected-info">
                    <span className="rejected-icon">🚫</span>
                    <span className="rejected-label">{item.label}</span>
                  </div>
                  <div className="rejected-bar-wrapper">
                    <div className="rejected-bar-track">
                      <div
                        className="rejected-bar-fill"
                        style={{
                          width: `${(item.value / Math.max(...data.rejectedIPs.map(d => d.value))) * 100}%`,
                          backgroundColor: item.color
                        }}
                      ></div>
                    </div>
                    <span className="rejected-value">{item.value}건</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* 상위 소스/목적지 */}
        <div className="chart-card full-width">
          <div className="chart-header">
            <h3><Globe size={20} /> 내부 트래픽 상위 IP</h3>
            <button className="export-button" onClick={() => exportData('sources')}>
              <Download size={14} /> 내보내기
            </button>
          </div>
          <div className="chart-container">
            <div className="traffic-grid">
              <div className="traffic-section">
                <h4>소스 IP (발신)</h4>
                <div className="traffic-list">
                  {data.topSources.slice(0, 6).map((item, index) => (
                    <div key={index} className="traffic-item">
                      <span className="traffic-rank">#{index + 1}</span>
                      <span className="traffic-ip">{item.label}</span>
                      <span className="traffic-count">{item.value}건</span>
                    </div>
                  ))}
                </div>
              </div>
              <div className="traffic-section">
                <h4>목적지 IP (수신)</h4>
                <div className="traffic-list">
                  {data.topDestinations.slice(0, 6).map((item, index) => (
                    <div key={index} className="traffic-item">
                      <span className="traffic-rank">#{index + 1}</span>
                      <span className="traffic-ip">{item.label}</span>
                      <span className="traffic-count">{item.value}건</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
