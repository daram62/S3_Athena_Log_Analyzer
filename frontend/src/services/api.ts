/**
 * Gen-AI Log Analyzer API 클라이언트
 */

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

export interface BucketInfo {
  name: string;
  creation_date: string;
  region: string | null;
}

export interface LogAnalysisRequest {
  bucket_name: string;
  prefix?: string;
  max_samples?: number;
}

export interface LogAnalysisResult {
  bucket_name: string;
  log_type: string;
  confidence: number;
  sample_count: number;
  inferred_schema: any;
  partition_strategy: string;
}

export interface TableCreationRequest {
  bucket_name: string;
  log_type: string;
  database_name?: string;
  table_name?: string;
}

export interface TableCreationResult {
  database_name: string;
  table_name: string;
  ddl_statement: string;
  status: string;
  message: string;
}

/**
 * S3 버킷 목록 조회
 */
export async function listBuckets(): Promise<BucketInfo[]> {
  const response = await fetch(`${API_BASE_URL}/buckets`);
  if (!response.ok) {
    throw new Error(`Failed to fetch buckets: ${response.statusText}`);
  }
  return response.json();
}

/**
 * 로그 파일 분석
 */
export async function analyzeLogs(request: LogAnalysisRequest): Promise<LogAnalysisResult> {
  const response = await fetch(`${API_BASE_URL}/analyze-logs`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });
  
  if (!response.ok) {
    throw new Error(`Failed to analyze logs: ${response.statusText}`);
  }
  
  return response.json();
}

/**
 * Athena 테이블 생성
 */
export async function createTable(request: TableCreationRequest): Promise<TableCreationResult> {
  const response = await fetch(`${API_BASE_URL}/tables/create`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });
  
  if (!response.ok) {
    throw new Error(`Failed to create table: ${response.statusText}`);
  }
  
  return response.json();
}

/**
 * 헬스 체크
 */
export async function healthCheck(): Promise<any> {
  const response = await fetch(`${API_BASE_URL}/health`);
  if (!response.ok) {
    throw new Error(`Health check failed: ${response.statusText}`);
  }
  return response.json();
}

/**
 * S3 버킷의 폴더 목록 조회
 */
export interface FolderInfo {
  path: string;
  name: string;
}

export interface FoldersResponse {
  bucket: string;
  folders: FolderInfo[];
}

export async function listFolders(bucketName: string, prefix: string = ''): Promise<FoldersResponse> {
  const url = `${API_BASE_URL}/buckets/${encodeURIComponent(bucketName)}/folders${prefix ? `?prefix=${encodeURIComponent(prefix)}` : ''}`;
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to fetch folders: ${response.statusText}`);
  }
  return response.json();
}


/**
 * 쿼리 템플릿 관련
 */
export interface QueryTemplate {
  id: string;
  category: string;
  name: string;
  description: string;
  sql_template: string;
  parameters: string[];
  use_cases: string[];
}

export async function listQueryTemplates(logType: string = 's3_access'): Promise<QueryTemplate[]> {
  const response = await fetch(`${API_BASE_URL}/query-templates/?log_type=${logType}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch query templates: ${response.statusText}`);
  }
  return response.json();
}

export async function getQueryTemplate(templateId: string, logType: string = 's3_access'): Promise<QueryTemplate> {
  const response = await fetch(`${API_BASE_URL}/query-templates/${templateId}?log_type=${logType}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch query template: ${response.statusText}`);
  }
  return response.json();
}

/**
 * 테이블 존재 여부 확인
 */
export interface TableCheckResult {
  exists: boolean;
  database: string;
  table: string;
  location?: string;
  created_at?: string;
}

export async function checkTableExists(databaseName: string, tableName: string): Promise<TableCheckResult> {
  const response = await fetch(`${API_BASE_URL}/tables/check/${encodeURIComponent(databaseName)}/${encodeURIComponent(tableName)}`);
  if (!response.ok) {
    throw new Error(`Failed to check table: ${response.statusText}`);
  }
  return response.json();
}
