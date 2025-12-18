import React, { useState, useRef, useEffect } from 'react';
import { 
  Sparkles, 
  Database,
  Clock, 
  Download,
  BarChart3
} from 'lucide-react';
import { InsightsDashboard } from './InsightsDashboard';
import { CloudFrontDashboard } from './CloudFrontDashboard';
import { S3Dashboard } from './S3Dashboard';
import { VPCFlowDashboard } from './VPCFlowDashboard';
import { ALBDashboard } from './ALBDashboard';
import NaturalLanguageQuery from './NaturalLanguageQuery';
import './QueryInterface.css';

interface QueryResult {
  id: string;
  query: string;
  sqlQuery: string;
  timestamp: Date;
  status: 'running' | 'completed' | 'error';
  results?: any[];
  error?: string;
  executionTime?: number;
}

interface QueryInterfaceProps {
  databaseName?: string;
  tableName?: string;
  logType?: string;
}

export const QueryInterface: React.FC<QueryInterfaceProps> = ({ 
  databaseName: initialDatabaseName,
  tableName: initialTableName,
  logType: initialLogType
}) => {

  const [activeTab, setActiveTab] = useState<'query' | 'dashboard'>('query');
  
  // 테이블 선택 상태
  const [availableTables, setAvailableTables] = useState<Array<{
    database_name: string;
    table_name: string;
    log_type: string;
  }>>([]);
  const [selectedDatabase, setSelectedDatabase] = useState<string>(initialDatabaseName || '');
  const [selectedTable, setSelectedTable] = useState<string>(initialTableName || '');
  const [selectedLogType, setSelectedLogType] = useState<string>(initialLogType || 's3_access');
  
  // 쿼리 히스토리 상태
  const [queryHistory, setQueryHistory] = useState<QueryResult[]>([]);
  
  const queryHistoryRef = useRef<HTMLDivElement>(null);
  
  // 테이블 목록 로드
  useEffect(() => {
    const loadTables = async () => {
      try {
        const response = await fetch('/api/v1/tables/list');
        const data = await response.json();
        const tables = data.tables || [];
        setAvailableTables(tables);
        
        // 테이블 목록 로드 후, props가 없고 테이블이 있으면 첫 번째 테이블 선택
        if (!initialDatabaseName && !initialTableName && tables.length > 0) {
          console.log('Setting first table:', tables[0]);
          setSelectedDatabase(tables[0].database_name);
          setSelectedTable(tables[0].table_name);
          setSelectedLogType(tables[0].log_type);
        }
      } catch (err) {
        console.error('Failed to load tables:', err);
      }
    };
    loadTables();
  }, []);
  
  // props가 변경되면 선택 상태 업데이트
  useEffect(() => {
    if (initialDatabaseName && initialTableName) {
      console.log('Props changed - updating selection:', initialDatabaseName, initialTableName, initialLogType);
      setSelectedDatabase(initialDatabaseName);
      setSelectedTable(initialTableName);
      setSelectedLogType(initialLogType || 's3_access');
    }
  }, [initialDatabaseName, initialTableName, initialLogType]);

  return (
    <div className="query-interface">
      <div className="query-interface-header">
        <div className="header-title">
          <Database className="header-icon" size={24} />
          <h2>로그 분석 워크스페이스</h2>
          <span className="beta-badge">Beta</span>
        </div>
        {availableTables.length > 0 && (
          <div className="table-selector">
            <label>분석 테이블:</label>
            <select 
              value={`${selectedDatabase}.${selectedTable}`}
              onChange={(e) => {
                const [db, table] = e.target.value.split('.');
                const selected = availableTables.find(t => t.database_name === db && t.table_name === table);
                if (selected) {
                  setSelectedDatabase(selected.database_name);
                  setSelectedTable(selected.table_name);
                  setSelectedLogType(selected.log_type);
                }
              }}
            >
              {availableTables.map(table => (
                <option 
                  key={`${table.database_name}.${table.table_name}`}
                  value={`${table.database_name}.${table.table_name}`}
                >
                  {table.table_name} ({table.log_type})
                </option>
              ))}
            </select>
          </div>
        )}
        <div className="header-tabs">
          <button
            className={`tab-button ${activeTab === 'query' ? 'active' : ''}`}
            onClick={() => setActiveTab('query')}
          >
            <Sparkles size={16} />
            자연어 분석
          </button>
          <button
            className={`tab-button ${activeTab === 'dashboard' ? 'active' : ''}`}
            onClick={() => setActiveTab('dashboard')}
          >
            <BarChart3 size={16} />
            대시보드
          </button>
        </div>

      </div>

      <div className="query-interface-content">
        {activeTab === 'dashboard' ? (
          // 로그 타입에 따라 적절한 대시보드 표시
          selectedLogType === 'cloudfront' ? (
            <CloudFrontDashboard />
          ) : selectedLogType === 's3_access' ? (
            <S3Dashboard />
          ) : selectedLogType === 'vpc_flow' ? (
            <VPCFlowDashboard />
          ) : selectedLogType === 'alb' ? (
            <ALBDashboard />
          ) : (
            <InsightsDashboard />
          )
        ) : (
          <>
        {/* 자연어 쿼리 컴포넌트 (추천 질문 포함) */}
        <div className="natural-language-section">
          <NaturalLanguageQuery
            databaseName={selectedDatabase}
            tableName={selectedTable}
            logType={selectedLogType}
            onQueryExecuted={(query, sql, results) => {
              // 쿼리 히스토리에 추가
              const queryResult = {
                id: Date.now().toString(),
                query: query,
                sqlQuery: sql,
                timestamp: new Date(),
                status: 'completed' as const,
                results: results,
                executionTime: 0
              };
              setQueryHistory(prev => [queryResult, ...prev]);
            }}
          />
        </div>

        {/* 히스토리는 NaturalLanguageQuery 컴포넌트 내부에서 관리 */}
          </>
        )}
      </div>
    </div>
  );
};