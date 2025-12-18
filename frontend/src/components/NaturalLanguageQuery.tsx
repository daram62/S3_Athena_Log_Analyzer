import React, { useState } from 'react';
import './NaturalLanguageQuery.css';

interface NaturalLanguageQueryProps {
  databaseName: string;
  tableName: string;
  logType?: string;
  onQueryExecuted?: (question: string, sql: string, results: any[]) => void;
}

interface QueryResult {
  query_id: string;
  sql_query: string;
  explanation: string;
  confidence: number;
  assumptions: string[];
  suggestions: string[];
  execution_status?: string;
  results?: any[];
  row_count?: number;
  execution_time_ms?: number;
  question?: string;
  timestamp?: Date;
}

// 로그 타입별 추천 질문
const SUGGESTED_QUESTIONS: Record<string, string[]> = {
  s3_access: [
    "전체 데이터 10개 보여줘",
    "가장 많이 접근된 파일 Top 10은?",
    "에러(4xx, 5xx) 발생 현황 분석해줘",
    "IP별 요청 횟수 Top 20",
    "가장 많은 데이터를 전송한 파일은?",
    "403 에러가 발생한 요청들 보여줘"
  ],
  cloudfront: [
    "전체 데이터 10개 보여줘",
    "캐시 히트율 분석해줘",
    "엣지 로케이션별 트래픽 분포",
    "4xx, 5xx 에러 분석",
    "가장 많이 요청된 콘텐츠 Top 10",
    "응답 시간이 1초 이상인 요청들"
  ],
  alb: [
    "전체 데이터 10개 보여줘",
    "타겟별 평균 응답 시간",
    "5xx 에러가 발생한 요청들",
    "가장 많이 호출된 엔드포인트 Top 10",
    "클라이언트 IP별 요청 수",
    "응답 시간이 가장 느린 요청들"
  ],
  vpc_flow: [
    "전체 데이터 10개 보여줘",
    "가장 많은 트래픽을 발생시킨 IP",
    "포트별 트래픽 분포",
    "프로토콜별 트래픽 통계",
    "외부에서 들어오는 트래픽 Top 10",
    "시간대별 트래픽 패턴 분석"
  ],

};

const NaturalLanguageQuery: React.FC<NaturalLanguageQueryProps> = ({
  databaseName,
  tableName,
  logType = 's3_access',
  onQueryExecuted
}) => {
  const [question, setQuestion] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [queryHistory, setQueryHistory] = useState<QueryResult[]>([]);
  const [expandedHistoryId, setExpandedHistoryId] = useState<string | null>(null);
  
  const suggestedQuestions = SUGGESTED_QUESTIONS[logType] || SUGGESTED_QUESTIONS.s3_access;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!question.trim()) {
      setError('질문을 입력해주세요');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/v1/natural-language/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question: question.trim(),
          database_name: databaseName,
          table_name: tableName,
          log_type: logType,
          execute_immediately: true
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || '쿼리 실행 실패');
      }

      const data = await response.json();
      
      // 히스토리에 추가 (최신이 맨 위)
      const newResult: QueryResult = {
        ...data,
        question: question.trim(),
        timestamp: new Date()
      };
      setQueryHistory(prev => [newResult, ...prev]);
      
      // 입력창 초기화
      setQuestion('');
      
      // 부모 컴포넌트에 알림
      if (onQueryExecuted && data.execution_status === 'succeeded' && data.results) {
        onQueryExecuted(question.trim(), data.sql_query, data.results);
      }
    } catch (err: any) {
      setError(err.message || '쿼리 처리 중 오류가 발생했습니다');
    } finally {
      setIsLoading(false);
    }
  };

  const toggleHistoryExpand = (queryId: string) => {
    setExpandedHistoryId(prev => prev === queryId ? null : queryId);
  };

  const renderResultTable = (results: any[]) => {
    if (!results || results.length === 0) return null;
    
    return (
      <div className="results-table-container">
        <table className="results-table">
          <thead>
            <tr>
              {Object.keys(results[0]).map((key) => (
                <th key={key}>{key}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {results.map((row, index) => (
              <tr key={index}>
                {Object.values(row).map((value: any, i) => (
                  <td key={i}>{String(value)}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  return (
    <div className="natural-language-query">
      <div className="query-header">
        <h2>🤖 자연어 쿼리</h2>
        <p className="query-subtitle">
          자연어로 질문하면 AI가 SQL을 생성하고 실행합니다
        </p>
      </div>

      {/* 추천 질문 - 항상 표시 */}
      <div className="suggested-questions">
        <h4>💡 추천 질문</h4>
        <div className="suggestions-grid">
          {suggestedQuestions.map((q, index) => (
            <button
              key={index}
              className="suggestion-chip"
              onClick={() => setQuestion(q)}
              disabled={isLoading}
            >
              {q}
            </button>
          ))}
        </div>
      </div>

      {/* 질문 입력 폼 - 항상 표시 */}
      <form onSubmit={handleSubmit} className="query-form">
        <div className="input-group">
          <textarea
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="질문을 입력하거나 위의 추천 질문을 클릭하세요"
            className="query-input"
            rows={2}
            disabled={isLoading}
          />
          <div className="form-actions">
            <button
              type="submit"
              className="btn-primary"
              disabled={isLoading || !question.trim()}
            >
              {isLoading ? (
                <>
                  <span className="spinner"></span>
                  분석 중...
                </>
              ) : (
                <>🚀 질문하기</>
              )}
            </button>
          </div>
        </div>
      </form>

      {/* 에러 메시지 */}
      {error && (
        <div className="error-message">
          <span role="img" aria-label="에러">❌</span>
          {error}
        </div>
      )}

      {/* 쿼리 히스토리 */}
      {queryHistory.length > 0 && (
        <div className="query-history">
          <h3>📋 쿼리 히스토리</h3>
          
          {queryHistory.map((result, index) => {
            const isLatest = index === 0;
            const isExpanded = isLatest || expandedHistoryId === result.query_id;
            
            return (
              <div key={result.query_id} className={`history-item ${isLatest ? 'latest' : 'collapsed'}`}>
                {/* 히스토리 헤더 - 항상 클릭 가능 */}
                <div 
                  className="history-header clickable"
                  onClick={() => toggleHistoryExpand(result.query_id)}
                >
                  <div className="history-question">
                    <span className="question-text">💬 {result.question}</span>
                    <span className="history-meta">
                      ✅ {result.row_count || 0}행 • {result.execution_time_ms || 0}ms
                      {result.timestamp && ` • ${result.timestamp.toLocaleTimeString()}`}
                    </span>
                  </div>
                  <span className="toggle-icon">
                    {isExpanded ? '▼' : '▶'}
                  </span>
                </div>

                {/* 결과 내용 - 최신 건은 기본 펼침, 나머지는 토글 */}
                {isExpanded && (
                  <div className="history-content">
                    {/* 생성된 SQL */}
                    <div className="sql-section">
                      <h4>📝 생성된 SQL</h4>
                      <pre className="sql-code">{result.sql_query}</pre>
                      <p className="sql-explanation">{result.explanation}</p>
                    </div>

                    {/* 실행 결과 */}
                    {result.execution_status === 'succeeded' && result.results && result.results.length > 0 ? (
                      <div className="results-section">
                        <h4>📊 실행 결과 ({result.row_count}행)</h4>
                        {renderResultTable(result.results)}
                      </div>
                    ) : (
                      <div className="no-results">
                        <p>📭 결과가 없습니다.</p>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default NaturalLanguageQuery;
