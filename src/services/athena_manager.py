"""Athena 데이터베이스 및 테이블 관리 서비스"""

import boto3
import time
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from ..models.log_configuration import LogType
from ..services.aws_clients import aws_client_manager

logger = logging.getLogger(__name__)


class AthenaManager:
    """Athena 데이터베이스 및 테이블 관리"""
    
    def __init__(self, region: str = 'us-east-1'):
        self.region = region
        from .aws_clients import AWSServiceType
        self.athena_client = aws_client_manager.get_client(AWSServiceType.ATHENA)
        self.s3_client = aws_client_manager.get_client(AWSServiceType.S3)
        
        # Athena 쿼리 결과 저장용 S3 버킷 (설정에서 가져오기)
        from ..config import settings
        self.query_results_bucket = settings.aws.athena_results_bucket
        
    def database_exists(self, database_name: str) -> bool:
        """데이터베이스 존재 여부 확인"""
        try:
            response = self.athena_client.get_database(
                CatalogName='AwsDataCatalog',
                DatabaseName=database_name
            )
            return True
        except self.athena_client.exceptions.MetadataException:
            return False
        except Exception as e:
            logger.error(f"Database existence check failed: {e}")
            return False
    
    def create_database(self, database_name: str, description: str = None) -> bool:
        """데이터베이스 생성"""
        try:
            query = f"CREATE DATABASE IF NOT EXISTS {database_name}"
            if description:
                query += f" COMMENT '{description}'"
            
            result = self.execute_query(query)
            return result.get('success', False)
            
        except Exception as e:
            logger.error(f"Database creation failed: {e}")
            return False
    
    def table_exists(self, database_name: str, table_name: str) -> bool:
        """테이블 존재 여부 확인"""
        try:
            response = self.athena_client.get_table_metadata(
                CatalogName='AwsDataCatalog',
                DatabaseName=database_name,
                TableName=table_name
            )
            return True
        except self.athena_client.exceptions.MetadataException:
            return False
        except Exception as e:
            logger.error(f"Table existence check failed: {e}")
            return False
    
    def create_table_from_schema(self, database_name: str, table_name: str, 
                                schema_info: Any, s3_location: str) -> bool:
        """스키마 정보를 기반으로 테이블 생성"""
        try:
            # 컬럼 정의 생성
            columns = []
            for col in schema_info.columns:
                col_type = self._map_column_type(col.data_type)
                columns.append(f"`{col.name}` {col_type}")
            
            columns_ddl = ",\n  ".join(columns)
            
            # 파티션 컬럼 (날짜 기반)
            partition_ddl = ""
            if schema_info.supports_partitioning:
                partition_ddl = """
PARTITIONED BY (
  `year` string,
  `month` string,
  `day` string
)"""
            
            # 저장 형식 결정
            stored_as = self._get_storage_format(schema_info.log_type)
            
            # CREATE TABLE 쿼리 생성
            create_query = f"""
CREATE EXTERNAL TABLE IF NOT EXISTS {database_name}.{table_name} (
  {columns_ddl}
){partition_ddl}
{stored_as}
LOCATION '{s3_location}'
TBLPROPERTIES (
  'projection.enabled'='true',
  'projection.year.type'='integer',
  'projection.year.range'='2020,2030',
  'projection.month.type'='integer',
  'projection.month.range'='1,12',
  'projection.month.digits'='2',
  'projection.day.type'='integer',
  'projection.day.range'='1,31',
  'projection.day.digits'='2',
  'storage.location.template'='{s3_location}/${{year}}/${{month}}/${{day}}'
)
"""
            
            result = self.execute_query(create_query)
            return result.get('success', False)
            
        except Exception as e:
            logger.error(f"Table creation failed: {e}")
            return False
    
    def setup_partitions(self, database_name: str, table_name: str, 
                        s3_location: str, days_back: int = 30) -> int:
        """파티션 설정 (최근 N일)"""
        try:
            partitions_added = 0
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)
            
            current_date = start_date
            while current_date <= end_date:
                year = current_date.strftime('%Y')
                month = current_date.strftime('%m')
                day = current_date.strftime('%d')
                
                partition_location = f"{s3_location}/year={year}/month={month}/day={day}"
                
                # 파티션 추가 쿼리
                alter_query = f"""
ALTER TABLE {database_name}.{table_name} 
ADD IF NOT EXISTS PARTITION (
  year='{year}',
  month='{month}',
  day='{day}'
) LOCATION '{partition_location}'
"""
                
                result = self.execute_query(alter_query)
                if result.get('success'):
                    partitions_added += 1
                
                current_date += timedelta(days=1)
            
            return partitions_added
            
        except Exception as e:
            logger.error(f"Partition setup failed: {e}")
            return 0
    
    def execute_query(self, query: str, timeout: int = 30) -> Dict[str, Any]:
        """Athena 쿼리 실행"""
        try:
            # 쿼리 실행
            response = self.athena_client.start_query_execution(
                QueryString=query,
                ResultConfiguration={
                    'OutputLocation': f's3://{self.query_results_bucket}/'
                },
                WorkGroup='primary'
            )
            
            query_execution_id = response['QueryExecutionId']
            
            # 쿼리 완료 대기
            start_time = time.time()
            while time.time() - start_time < timeout:
                response = self.athena_client.get_query_execution(
                    QueryExecutionId=query_execution_id
                )
                
                status = response['QueryExecution']['Status']['State']
                
                if status == 'SUCCEEDED':
                    return {
                        'success': True,
                        'query_execution_id': query_execution_id,
                        'status': status
                    }
                elif status in ['FAILED', 'CANCELLED']:
                    error_message = response['QueryExecution']['Status'].get('StateChangeReason', 'Unknown error')
                    return {
                        'success': False,
                        'error': error_message,
                        'status': status
                    }
                
                time.sleep(1)
            
            # 타임아웃
            return {
                'success': False,
                'error': 'Query execution timeout',
                'status': 'TIMEOUT'
            }
            
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'status': 'ERROR'
            }
    
    def get_query_results(self, query_execution_id: str) -> Dict[str, Any]:
        """쿼리 결과 조회"""
        try:
            response = self.athena_client.get_query_results(
                QueryExecutionId=query_execution_id
            )
            
            # 결과 파싱
            result_set = response.get('ResultSet', {})
            rows = result_set.get('Rows', [])
            
            if not rows:
                return {'success': True, 'data': [], 'row_count': 0}
            
            # 헤더 추출
            headers = [col['VarCharValue'] for col in rows[0]['Data']]
            
            # 데이터 행 추출
            data_rows = []
            for row in rows[1:]:  # 첫 번째 행은 헤더이므로 제외
                row_data = {}
                for i, col in enumerate(row['Data']):
                    row_data[headers[i]] = col.get('VarCharValue', '')
                data_rows.append(row_data)
            
            return {
                'success': True,
                'data': data_rows,
                'headers': headers,
                'row_count': len(data_rows)
            }
            
        except Exception as e:
            logger.error(f"Query results retrieval failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _map_column_type(self, data_type: str) -> str:
        """데이터 타입을 Athena 타입으로 매핑"""
        type_mapping = {
            'string': 'string',
            'int': 'bigint',
            'integer': 'bigint',
            'float': 'double',
            'double': 'double',
            'boolean': 'boolean',
            'timestamp': 'timestamp',
            'date': 'date'
        }
        return type_mapping.get(data_type.lower(), 'string')
    
    def _get_storage_format(self, log_type: str) -> str:
        """로그 타입에 따른 저장 형식 반환"""
        if log_type in ['s3_access', 'cloudfront', 'alb']:
            return """
STORED AS INPUTFORMAT 'org.apache.hadoop.mapred.TextInputFormat'
OUTPUTFORMAT 'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat'
"""
        elif log_type == 'vpc_flow':
            return """
STORED AS INPUTFORMAT 'org.apache.hadoop.mapred.TextInputFormat'
OUTPUTFORMAT 'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat'
"""
        else:
            # 기본값
            return """
STORED AS INPUTFORMAT 'org.apache.hadoop.mapred.TextInputFormat'
OUTPUTFORMAT 'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat'
"""
    
    def list_databases(self) -> List[Dict[str, str]]:
        """데이터베이스 목록 조회"""
        try:
            response = self.athena_client.list_databases(
                CatalogName='AwsDataCatalog'
            )
            
            databases = []
            for db in response.get('DatabaseList', []):
                databases.append({
                    'name': db['Name'],
                    'description': db.get('Description', ''),
                    'parameters': db.get('Parameters', {})
                })
            
            return databases
            
        except Exception as e:
            logger.error(f"Database listing failed: {e}")
            return []
    
    def list_tables(self, database_name: str) -> List[Dict[str, str]]:
        """테이블 목록 조회"""
        try:
            response = self.athena_client.list_table_metadata(
                CatalogName='AwsDataCatalog',
                DatabaseName=database_name
            )
            
            tables = []
            for table in response.get('TableMetadataList', []):
                tables.append({
                    'name': table['Name'],
                    'table_type': table.get('TableType', ''),
                    'parameters': table.get('Parameters', {}),
                    'columns': len(table.get('Columns', []))
                })
            
            return tables
            
        except Exception as e:
            logger.error(f"Table listing failed: {e}")
            return []
    
    def drop_table(self, database_name: str, table_name: str) -> bool:
        """테이블 삭제"""
        try:
            query = f"DROP TABLE IF EXISTS {database_name}.{table_name}"
            result = self.execute_query(query)
            return result.get('success', False)
            
        except Exception as e:
            logger.error(f"Table drop failed: {e}")
            return False
    
    def drop_database(self, database_name: str, cascade: bool = False) -> bool:
        """데이터베이스 삭제"""
        try:
            query = f"DROP DATABASE IF EXISTS {database_name}"
            if cascade:
                query += " CASCADE"
            
            result = self.execute_query(query)
            return result.get('success', False)
            
        except Exception as e:
            logger.error(f"Database drop failed: {e}")
            return False