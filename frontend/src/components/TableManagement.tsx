import React, { useState, useEffect } from 'react';
import './TableManagement.css';

interface TableInfo {
  database_name: string;
  table_name: string;
  log_type: string;
  s3_location: string;
  created_at?: string;
  field_count: number;
  partition_count?: number;
  status: string;
}

interface TableDetail {
  table_info: TableInfo;
  columns: Array<{ name: string; type: string; comment: string }>;
  partitions: string[];
  sample_queries: Array<{ name: string; description: string; sql: string }>;
}

interface TableManagementProps {
  onNavigateToAnalysis?: (databaseName: string, tableName: string, logType: string) => void;
}

const TableManagement: React.FC<TableManagementProps> = ({ onNavigateToAnalysis }) => {
  const [tables, setTables] = useState<TableInfo[]>([]);
  const [selectedTable, setSelectedTable] = useState<string | null>(null);
  const [tableDetail, setTableDetail] = useState<TableDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'columns' | 'queries'>('overview');
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [tableToDelete, setTableToDelete] = useState<{ name: string; database: string } | null>(null);

  // 테이블 목록 로드
  useEffect(() => {
    loadTables();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const loadTables = async () => {
    setLoading(true);
    setError(null);
    
    try {
      // database_name 파라미터 없이 모든 데이터베이스의 테이블 조회
      const response = await fetch(`/api/v1/tables/list`);
      if (!response.ok) throw new Error('테이블 목록 조회 실패');
      
      const data = await response.json();
      setTables(data.tables);
      
      // 현재 선택된 테이블이 목록에 있는지 확인
      const currentTableExists = selectedTable && data.tables.some(
        (t: TableInfo) => t.table_name === selectedTable
      );
      
      // 선택된 테이블이 없거나 목록에 없으면 첫 번째 테이블 선택
      if (data.tables.length > 0 && !currentTableExists) {
        selectTable(data.tables[0].table_name, data.tables[0].database_name);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '알 수 없는 오류');
    } finally {
      setLoading(false);
    }
  };

  const selectTable = async (tableName: string, databaseName: string) => {
    setSelectedTable(tableName);
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(
        `/api/v1/tables/detail/${databaseName}/${tableName}`
      );
      if (!response.ok) throw new Error('테이블 상세 조회 실패');
      
      const data = await response.json();
      setTableDetail(data);
      setActiveTab('overview');
    } catch (err) {
      setError(err instanceof Error ? err.message : '알 수 없는 오류');
    } finally {
      setLoading(false);
    }
  };

  const confirmDeleteTable = (tableName: string, databaseName: string) => {
    setTableToDelete({ name: tableName, database: databaseName });
    setShowDeleteModal(true);
  };

  const deleteTable = async () => {
    if (!tableToDelete) return;
    
    setLoading(true);
    setShowDeleteModal(false);
    
    try {
      const response = await fetch('/api/v1/tables/delete', {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          database_name: tableToDelete.database,
          table_name: tableToDelete.name,
          delete_data: false
        })
      });
      
      if (!response.ok) throw new Error('테이블 삭제 실패');
      
      setSelectedTable(null);
      setTableDetail(null);
      setTableToDelete(null);
      loadTables();
    } catch (err) {
      setError(err instanceof Error ? err.message : '테이블 삭제 실패');
    } finally {
      setLoading(false);
    }
  };

  const refreshPartitions = async (tableName: string, databaseName: string) => {
    setLoading(true);
    try {
      const response = await fetch(
        `/api/v1/tables/refresh-partitions/${databaseName}/${tableName}`,
        { method: 'POST' }
      );
      
      if (!response.ok) throw new Error('파티션 새로고침 실패');
      
      alert('파티션이 새로고침되었습니다');
      selectTable(tableName, databaseName);
    } catch (err) {
      alert(err instanceof Error ? err.message : '파티션 새로고침 실패');
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    alert('클립보드에 복사되었습니다');
  };

  const getLogTypeIcon = (logType: string) => {
    const iconMap: Record<string, string> = {
      s3_access: '/image/S3.png',
      cloudfront: '/image/Cloudfront.png',
      alb: '/image/ALB.png',
      vpc_flow: '/image/VPC.png',
      cloudtrail: '/image/Cloudtrail.png'
    };
    const iconPath = iconMap[logType];
    if (iconPath) {
      return <img src={iconPath} alt={logType} className="log-type-icon" />;
    }
    return <span>📊</span>;
  };

  const getLogTypeName = (logType: string) => {
    const names: Record<string, string> = {
      s3_access: 'S3 Access Logs',
      cloudfront: 'CloudFront Logs',
      alb: 'ALB Logs',
      vpc_flow: 'VPC Flow Logs',
      cloudtrail: 'CloudTrail Logs'
    };
    return names[logType] || logType;
  };

  return (
    <div className="table-management">
      <div className="header">
        <h1>📊 테이블 관리</h1>
        <p>생성된 Athena 테이블을 관리하고 분석하세요</p>
      </div>

      {error && (
        <div className="error-banner">
          ⚠️ {error}
        </div>
      )}

      <div className="content">
        {/* 왼쪽: 테이블 목록 */}
        <div className="table-list">
          <div className="list-header">
            <h2>테이블 목록</h2>
            <button onClick={loadTables} className="refresh-btn" disabled={loading}>
              🔄 새로고침
            </button>
          </div>

          {loading && tables.length === 0 ? (
            <div className="loading">로딩 중...</div>
          ) : tables.length === 0 ? (
            <div className="empty-state">
              <p>생성된 테이블이 없습니다</p>
              <p className="hint">S3 버킷을 분석하여 테이블을 생성하세요</p>
            </div>
          ) : (
            <div className="table-items">
              {tables.map((table) => (
                <div
                  key={`${table.database_name}.${table.table_name}`}
                  className={`table-item ${selectedTable === table.table_name ? 'active' : ''}`}
                  onClick={() => selectTable(table.table_name, table.database_name)}
                >
                  <div className="table-icon">
                    {getLogTypeIcon(table.log_type)}
                  </div>
                  <div className="table-info">
                    <div className="table-name">{table.table_name}</div>
                    <div className="table-type">{getLogTypeName(table.log_type)}</div>
                    <div className="table-meta">
                      {table.field_count} 필드
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* 오른쪽: 테이블 상세 */}
        <div className="table-detail">
          {!selectedTable ? (
            <div className="empty-detail">
              <p>테이블을 선택하세요</p>
            </div>
          ) : loading && !tableDetail ? (
            <div className="loading">로딩 중...</div>
          ) : tableDetail ? (
            <>
              <div className="detail-header">
                <div className="detail-title">
                  <h2>
                    {getLogTypeIcon(tableDetail.table_info.log_type)}{' '}
                    {tableDetail.table_info.table_name}
                  </h2>
                  <span className="log-type-badge">
                    {getLogTypeName(tableDetail.table_info.log_type)}
                  </span>
                </div>
                <div className="detail-actions">
                  <button
                    onClick={() => {
                      // 분석 페이지로 이동 (테이블 정보 전달)
                      if (onNavigateToAnalysis) {
                        onNavigateToAnalysis(
                          tableDetail.table_info.database_name,
                          tableDetail.table_info.table_name,
                          tableDetail.table_info.log_type
                        );
                      }
                    }}
                    className="action-btn primary"
                    disabled={loading}
                  >
                    📊 분석하기
                  </button>

                  <button
                    onClick={() => confirmDeleteTable(tableDetail.table_info.table_name, tableDetail.table_info.database_name)}
                    className="action-btn danger"
                    disabled={loading}
                  >
                    🗑️ 삭제
                  </button>
                </div>
              </div>

              <div className="tabs">
                <button
                  className={`tab ${activeTab === 'overview' ? 'active' : ''}`}
                  onClick={() => setActiveTab('overview')}
                >
                  개요
                </button>
                <button
                  className={`tab ${activeTab === 'columns' ? 'active' : ''}`}
                  onClick={() => setActiveTab('columns')}
                >
                  컬럼 ({tableDetail.columns.length})
                </button>
                <button
                  className={`tab ${activeTab === 'queries' ? 'active' : ''}`}
                  onClick={() => setActiveTab('queries')}
                >
                  샘플 쿼리 ({tableDetail.sample_queries.length})
                </button>
              </div>

              <div className="tab-content">
                {activeTab === 'overview' && (
                  <div className="overview">
                    <div className="info-grid">
                      <div className="info-item">
                        <div className="info-label">데이터베이스</div>
                        <div className="info-value">{tableDetail.table_info.database_name}</div>
                      </div>
                      <div className="info-item">
                        <div className="info-label">S3 위치</div>
                        <div className="info-value code">{tableDetail.table_info.s3_location}</div>
                      </div>
                      <div className="info-item">
                        <div className="info-label">생성일</div>
                        <div className="info-value">
                          {tableDetail.table_info.created_at
                            ? new Date(tableDetail.table_info.created_at).toLocaleString('ko-KR')
                            : 'N/A'}
                        </div>
                      </div>
                      <div className="info-item">
                        <div className="info-label">필드 수</div>
                        <div className="info-value">{tableDetail.table_info.field_count}</div>
                      </div>
                    </div>
                  </div>
                )}

                {activeTab === 'columns' && (
                  <div className="columns">
                    <table className="columns-table">
                      <thead>
                        <tr>
                          <th>컬럼명</th>
                          <th>타입</th>
                          <th>설명</th>
                        </tr>
                      </thead>
                      <tbody>
                        {tableDetail.columns.map((col, idx) => (
                          <tr key={idx}>
                            <td className="col-name">{col.name}</td>
                            <td className="col-type">{col.type}</td>
                            <td className="col-comment">{col.comment || '-'}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}

                {activeTab === 'queries' && (
                  <div className="queries">
                    {tableDetail.sample_queries.map((query, idx) => (
                      <div key={idx} className="query-card">
                        <div className="query-header">
                          <div>
                            <h3>{query.name}</h3>
                            <p className="query-description">{query.description}</p>
                          </div>
                          <button
                            onClick={() => copyToClipboard(query.sql)}
                            className="copy-btn"
                          >
                            📋 복사
                          </button>
                        </div>
                        <pre className="query-sql">{query.sql}</pre>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </>
          ) : null}
        </div>
      </div>

      {/* 삭제 확인 모달 */}
      {showDeleteModal && tableToDelete && (
        <div className="modal-overlay" onClick={() => setShowDeleteModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div className="modal-icon warning">⚠️</div>
              <h2>테이블 삭제 확인</h2>
            </div>
            <div className="modal-body">
              <p className="modal-message">
                정말로 이 테이블을 삭제하시겠습니까?
              </p>
              <div className="modal-details">
                <div className="detail-row">
                  <span className="detail-label">테이블명:</span>
                  <span className="detail-value">{tableToDelete.name}</span>
                </div>
                <div className="detail-row">
                  <span className="detail-label">데이터베이스:</span>
                  <span className="detail-value">{tableToDelete.database}</span>
                </div>
              </div>
              <div className="modal-warning">
                <span className="warning-icon">💡</span>
                <span>테이블 메타데이터만 삭제되며, S3의 실제 로그 파일은 유지됩니다.</span>
              </div>
            </div>
            <div className="modal-footer">
              <button
                className="modal-btn cancel"
                onClick={() => {
                  setShowDeleteModal(false);
                  setTableToDelete(null);
                }}
                disabled={loading}
              >
                취소
              </button>
              <button
                className="modal-btn delete"
                onClick={deleteTable}
                disabled={loading}
              >
                {loading ? '삭제 중...' : '삭제'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TableManagement;
