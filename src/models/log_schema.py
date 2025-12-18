"""
로그 스키마 정의 및 템플릿 관리
S3 Access Log, VPC Flow Log, ELB Log, CloudFront Log 등의 스키마 템플릿
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from enum import Enum
import re


class LogType(Enum):
    """지원하는 로그 타입"""
    S3_ACCESS = "s3_access"
    CLOUDFRONT = "cloudfront"
    ALB = "alb"
    VPC_FLOW = "vpc_flow"
    CLOUDTRAIL = "cloudtrail"


class FieldType(Enum):
    """Athena 데이터 타입"""
    STRING = "string"
    INT = "int"
    BIGINT = "bigint"
    DOUBLE = "double"
    BOOLEAN = "boolean"
    TIMESTAMP = "timestamp"
    DATE = "date"


@dataclass
class SchemaField:
    """스키마 필드 정의"""
    name: str
    type: FieldType
    description: str
    regex_pattern: Optional[str] = None
    is_nullable: bool = True
    default_value: Optional[str] = None
    
    def to_athena_ddl(self) -> str:
        """Athena DDL 형식으로 변환"""
        return f"`{self.name}` {self.type.value}"


@dataclass
class LogSchema:
    """로그 스키마 정의"""
    log_type: LogType
    name: str
    description: str
    fields: List[SchemaField]
    sample_log_pattern: str
    regex_pattern: str
    partition_fields: List[str]
    
    def get_create_table_ddl(self, 
                           database_name: str, 
                           table_name: str, 
                           s3_location: str,
                           partition_projection: bool = True) -> str:
        """Athena CREATE TABLE DDL 생성 - AWS 공식 문서 기준"""
        
        # CloudTrail은 JSON 형식이므로 별도 처리
        if self.log_type == LogType.CLOUDTRAIL:
            return self._get_cloudtrail_ddl(database_name, table_name, s3_location, partition_projection)
        
        # S3 Access Logs는 RegexSerDe 사용 (AWS 공식 문서 기준)
        if self.log_type == LogType.S3_ACCESS:
            return self._get_s3_access_ddl(database_name, table_name, s3_location, partition_projection)
        
        # ALB Logs는 RegexSerDe 사용 (AWS 공식 문서 기준)
        if self.log_type == LogType.ALB:
            return self._get_alb_ddl(database_name, table_name, s3_location, partition_projection)
        
        # CloudFront Logs는 LazySimpleSerDe 사용 (AWS 공식 문서 기준)
        if self.log_type == LogType.CLOUDFRONT:
            return self._get_cloudfront_ddl(database_name, table_name, s3_location, partition_projection)
        
        # VPC Flow Logs는 LazySimpleSerDe 사용 (AWS 공식 문서 기준)
        if self.log_type == LogType.VPC_FLOW:
            return self._get_vpc_flow_ddl(database_name, table_name, s3_location, partition_projection)
        
        # 필드 정의
        field_definitions = [field.to_athena_ddl() for field in self.fields]
        fields_ddl = ",\n  ".join(field_definitions)
        
        # 파티션 필드 정의
        partition_ddl = ""
        if self.partition_fields:
            partition_definitions = [f"`{field}` string" for field in self.partition_fields]
            partition_ddl = f"\nPARTITIONED BY (\n  {', '.join(partition_definitions)}\n)"
        
        # 파티션 프로젝션 설정
        projection_properties = ""
        if partition_projection and self.partition_fields:
            projection_properties = self._get_partition_projection_properties()
        
        # SerDe 설정
        serde_properties = self._get_serde_properties()
        
        # 헤더 라인 스킵 설정
        skip_header = '2' if self.log_type == LogType.CLOUDFRONT else '0'
        
        # 구분자 설정
        delimiter = '\\t' if self.log_type == LogType.CLOUDFRONT else ' '
        
        ddl = f"""CREATE EXTERNAL TABLE `{database_name}`.`{table_name}` (
  {fields_ddl}
){partition_ddl}
STORED AS INPUTFORMAT 
  'org.apache.hadoop.mapred.TextInputFormat' 
OUTPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat'
LOCATION
  '{s3_location}'
TBLPROPERTIES (
  'classification'='csv',
  'delimiter'='{delimiter}',
  'skip.header.line.count'='{skip_header}'{projection_properties}{serde_properties}
)"""
        
        return ddl
    
    def _get_cloudtrail_ddl(self, database_name: str, table_name: str, 
                           s3_location: str, partition_projection: bool) -> str:
        """CloudTrail JSON 형식 DDL 생성 - AWS 공식 문서 기준 (파티션 없음)"""
        
        ddl = f"""CREATE EXTERNAL TABLE `{database_name}`.`{table_name}` (
  `eventversion` STRING,
  `useridentity` STRUCT<
    type:STRING,
    principalid:STRING,
    arn:STRING,
    accountid:STRING,
    invokedby:STRING,
    accesskeyid:STRING,
    username:STRING,
    onbehalfof:STRUCT<
      userid:STRING,
      identitystorearn:STRING>,
    sessioncontext:STRUCT<
      attributes:STRUCT<
        mfaauthenticated:STRING,
        creationdate:STRING>,
      sessionissuer:STRUCT<
        type:STRING,
        principalid:STRING,
        arn:STRING,
        accountid:STRING,
        username:STRING>,
      ec2roledelivery:STRING,
      webidfederationdata:STRUCT<
        federatedprovider:STRING,
        attributes:map<string,string>>>>,
  `eventtime` STRING,
  `eventsource` STRING,
  `eventname` STRING,
  `awsregion` STRING,
  `sourceipaddress` STRING,
  `useragent` STRING,
  `errorcode` STRING,
  `errormessage` STRING,
  `requestparameters` STRING,
  `responseelements` STRING,
  `additionaleventdata` STRING,
  `requestid` STRING,
  `eventid` STRING,
  `readonly` STRING,
  `resources` ARRAY<STRUCT<
    arn:STRING,
    accountid:STRING,
    type:STRING>>,
  `eventtype` STRING,
  `apiversion` STRING,
  `recipientaccountid` STRING,
  `serviceeventdetails` STRING,
  `sharedeventid` STRING,
  `vpcendpointid` STRING,
  `vpcendpointaccountid` STRING,
  `eventcategory` STRING,
  `addendum` STRUCT<
    reason:STRING,
    updatedfields:STRING,
    originalrequestid:STRING,
    originaleventid:STRING>,
  `sessioncredentialfromconsole` STRING,
  `edgedevicedetails` STRING,
  `tlsdetails` STRUCT<
    tlsversion:STRING,
    ciphersuite:STRING,
    clientprovidedhostheader:STRING>
)
ROW FORMAT SERDE 'org.apache.hive.hcatalog.data.JsonSerDe'
STORED AS INPUTFORMAT 'com.amazon.emr.cloudtrail.CloudTrailInputFormat'
OUTPUTFORMAT 'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat'
LOCATION '{s3_location}'"""
        
        return ddl
    
    def _get_s3_access_ddl(self, database_name: str, table_name: str, 
                          s3_location: str, partition_projection: bool) -> str:
        """S3 Access Logs DDL 생성 - AWS 공식 문서 기준 (파티션 없음)"""
        
        # AWS 공식 문서의 정확한 regex 패턴
        s3_regex = r"([^ ]*) ([^ ]*) \\[(.*?)\\] ([^ ]*) ([^ ]*) ([^ ]*) ([^ ]*) ([^ ]*) (\"[^\"]*\"|-) (-|[0-9]*) ([^ ]*) ([^ ]*) ([^ ]*) ([^ ]*) ([^ ]*) ([^ ]*) (\"[^\"]*\"|-) ([^ ]*)(?: ([^ ]*) ([^ ]*) ([^ ]*) ([^ ]*) ([^ ]*) ([^ ]*) ([^ ]*) ([^ ]*))?.*$"
        
        ddl = f"""CREATE EXTERNAL TABLE `{database_name}`.`{table_name}` (
  `bucketowner` STRING,
  `bucket_name` STRING,
  `requestdatetime` STRING,
  `remoteip` STRING,
  `requester` STRING,
  `requestid` STRING,
  `operation` STRING,
  `key` STRING,
  `request_uri` STRING,
  `httpstatus` STRING,
  `errorcode` STRING,
  `bytessent` BIGINT,
  `objectsize` BIGINT,
  `totaltime` STRING,
  `turnaroundtime` STRING,
  `referrer` STRING,
  `useragent` STRING,
  `versionid` STRING,
  `hostid` STRING,
  `sigv` STRING,
  `ciphersuite` STRING,
  `authtype` STRING,
  `endpoint` STRING,
  `tlsversion` STRING,
  `accesspointarn` STRING,
  `aclrequired` STRING
)
ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.RegexSerDe'
WITH SERDEPROPERTIES (
  'input.regex'='{s3_regex}'
)
STORED AS INPUTFORMAT 'org.apache.hadoop.mapred.TextInputFormat'
OUTPUTFORMAT 'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat'
LOCATION '{s3_location}'"""
        
        return ddl
    
    def _get_alb_ddl(self, database_name: str, table_name: str, 
                    s3_location: str, partition_projection: bool) -> str:
        """ALB Access Logs DDL 생성 - AWS 공식 문서 기준"""
        
        # AWS 공식 문서의 정확한 regex 패턴
        alb_regex = r"([^ ]*) ([^ ]*) ([^ ]*) ([^ ]*):([0-9]*) ([^ ]*)[:-]([0-9]*) ([-.0-9]*) ([-.0-9]*) ([-.0-9]*) (|[-0-9]*) (-|[-0-9]*) ([-0-9]*) ([-0-9]*) \"([^ ]*) (.*) (- |[^ ]*)\" \"([^\"]*)\" ([A-Z0-9-_]+) ([A-Za-z0-9.-]*) ([^ ]*) \"([^\"]*)\" \"([^\"]*)\" \"([^\"]*)\" ([-.0-9]*) ([^ ]*) \"([^\"]*)\" \"([^\"]*)\" \"([^ ]*)\" \"([^\\s]+?)\" \"([^\\s]+)\" \"([^ ]*)\" \"([^ ]*)\" ?([^ ]*)? ?( .*)?"
        
        ddl = f"""CREATE EXTERNAL TABLE IF NOT EXISTS `{database_name}`.`{table_name}` (
  `type` STRING,
  `time` STRING,
  `elb` STRING,
  `client_ip` STRING,
  `client_port` INT,
  `target_ip` STRING,
  `target_port` INT,
  `request_processing_time` DOUBLE,
  `target_processing_time` DOUBLE,
  `response_processing_time` DOUBLE,
  `elb_status_code` INT,
  `target_status_code` STRING,
  `received_bytes` BIGINT,
  `sent_bytes` BIGINT,
  `request_verb` STRING,
  `request_url` STRING,
  `request_proto` STRING,
  `user_agent` STRING,
  `ssl_cipher` STRING,
  `ssl_protocol` STRING,
  `target_group_arn` STRING,
  `trace_id` STRING,
  `domain_name` STRING,
  `chosen_cert_arn` STRING,
  `matched_rule_priority` STRING,
  `request_creation_time` STRING,
  `actions_executed` STRING,
  `redirect_url` STRING,
  `lambda_error_reason` STRING,
  `target_port_list` STRING,
  `target_status_code_list` STRING,
  `classification` STRING,
  `classification_reason` STRING,
  `conn_trace_id` STRING
)
ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.RegexSerDe'
WITH SERDEPROPERTIES (
  'serialization.format'='1',
  'input.regex'='{alb_regex}'
)
STORED AS INPUTFORMAT 'org.apache.hadoop.mapred.TextInputFormat'
OUTPUTFORMAT 'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat'
LOCATION '{s3_location}'"""
        
        return ddl
    
    def _get_cloudfront_ddl(self, database_name: str, table_name: str, 
                           s3_location: str, partition_projection: bool) -> str:
        """CloudFront Standard Logs DDL 생성 - AWS 공식 문서 기준"""
        
        ddl = f"""CREATE EXTERNAL TABLE IF NOT EXISTS `{database_name}`.`{table_name}` (
  `date` DATE,
  `time` STRING,
  `x_edge_location` STRING,
  `sc_bytes` BIGINT,
  `c_ip` STRING,
  `cs_method` STRING,
  `cs_host` STRING,
  `cs_uri_stem` STRING,
  `sc_status` INT,
  `cs_referer` STRING,
  `cs_user_agent` STRING,
  `cs_uri_query` STRING,
  `cs_cookie` STRING,
  `x_edge_result_type` STRING,
  `x_edge_request_id` STRING,
  `x_host_header` STRING,
  `cs_protocol` STRING,
  `cs_bytes` BIGINT,
  `time_taken` FLOAT,
  `x_forwarded_for` STRING,
  `ssl_protocol` STRING,
  `ssl_cipher` STRING,
  `x_edge_response_result_type` STRING,
  `cs_protocol_version` STRING,
  `fle_status` STRING,
  `fle_encrypted_fields` INT,
  `c_port` INT,
  `time_to_first_byte` FLOAT,
  `x_edge_detailed_result_type` STRING,
  `sc_content_type` STRING,
  `sc_content_len` BIGINT,
  `sc_range_start` BIGINT,
  `sc_range_end` BIGINT
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY '\\t'
LOCATION '{s3_location}'
TBLPROPERTIES ('skip.header.line.count'='2')"""
        
        return ddl
    
    def _get_vpc_flow_ddl(self, database_name: str, table_name: str, 
                         s3_location: str, partition_projection: bool) -> str:
        """VPC Flow Logs DDL 생성 - AWS 공식 문서 기준 (파티션 없음)"""
        
        ddl = f"""CREATE EXTERNAL TABLE IF NOT EXISTS `{database_name}`.`{table_name}` (
  `version` INT,
  `account_id` STRING,
  `interface_id` STRING,
  `srcaddr` STRING,
  `dstaddr` STRING,
  `srcport` INT,
  `dstport` INT,
  `protocol` BIGINT,
  `packets` BIGINT,
  `bytes` BIGINT,
  `start` BIGINT,
  `end` BIGINT,
  `action` STRING,
  `log_status` STRING,
  `vpc_id` STRING,
  `subnet_id` STRING,
  `instance_id` STRING,
  `tcp_flags` INT,
  `type` STRING,
  `pkt_srcaddr` STRING,
  `pkt_dstaddr` STRING,
  `region` STRING,
  `az_id` STRING,
  `sublocation_type` STRING,
  `sublocation_id` STRING,
  `pkt_src_aws_service` STRING,
  `pkt_dst_aws_service` STRING,
  `flow_direction` STRING,
  `traffic_path` INT
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ' '
LOCATION '{s3_location}'
TBLPROPERTIES ('skip.header.line.count'='1')"""
        
        return ddl
    
    def _get_partition_projection_properties(self) -> str:
        """파티션 프로젝션 속성 생성"""
        # S3 Access Logs는 timestamp 파티션 사용
        if self.log_type == LogType.S3_ACCESS:
            return """,
  'projection.enabled'='true',
  'projection.timestamp.format'='yyyy/MM/dd',
  'projection.timestamp.interval'='1',
  'projection.timestamp.interval.unit'='DAYS',
  'projection.timestamp.range'='2024/01/01,NOW',
  'projection.timestamp.type'='date',
  'storage.location.template'='s3://your-bucket/logs/${timestamp}'"""
        
        # 다른 로그 타입은 year/month/day 파티션 사용
        if self.partition_fields:
            return """,
  'projection.enabled'='true',
  'projection.year.type'='integer',
  'projection.year.range'='2020,2030',
  'projection.year.interval'='1',
  'projection.month.type'='integer',
  'projection.month.range'='1,12',
  'projection.month.interval'='1',
  'projection.day.type'='integer',
  'projection.day.range'='1,31',
  'projection.day.interval'='1',
  'storage.location.template'='s3://your-bucket/logs/${year}/${month}/${day}/'"""
        return ""
    
    def _get_serde_properties(self) -> str:
        """SerDe 속성 생성"""
        if self.log_type == LogType.S3_ACCESS:
            return """,
  'serde.param.field.delim'=' ',
  'serde.param.serialization.format'=' '"""
        elif self.log_type == LogType.CLOUDFRONT:
            return """,
  'serde.param.field.delim'='\t',
  'serde.param.serialization.format'='\t'"""
        elif self.log_type == LogType.ALB:
            return """,
  'serde.param.field.delim'=' ',
  'serde.param.serialization.format'=' '"""
        elif self.log_type == LogType.VPC_FLOW:
            return """,
  'serde.param.field.delim'=' ',
  'serde.param.serialization.format'=' '"""
        return ""


class LogSchemaRegistry:
    """로그 스키마 레지스트리"""
    
    def __init__(self):
        self._schemas: Dict[LogType, LogSchema] = {}
        self._initialize_schemas()
    
    def _initialize_schemas(self):
        """기본 스키마들 초기화"""
        self._schemas[LogType.S3_ACCESS] = self._create_s3_access_schema()
        self._schemas[LogType.CLOUDFRONT] = self._create_cloudfront_schema()
        self._schemas[LogType.ALB] = self._create_alb_schema()
        self._schemas[LogType.VPC_FLOW] = self._create_vpc_flow_schema()
        self._schemas[LogType.CLOUDTRAIL] = self._create_cloudtrail_schema()
    
    def get_schema(self, log_type: LogType) -> Optional[LogSchema]:
        """로그 타입에 해당하는 스키마 반환"""
        return self._schemas.get(log_type)
    
    def get_all_schemas(self) -> Dict[LogType, LogSchema]:
        """모든 스키마 반환"""
        return self._schemas.copy()
    
    def register_schema(self, schema: LogSchema):
        """새로운 스키마 등록"""
        self._schemas[schema.log_type] = schema
    
    def _create_s3_access_schema(self) -> LogSchema:
        """S3 Access Log 스키마 생성 (26개 필드) - AWS 공식 문서 기준"""
        
        fields = [
            SchemaField(name="bucketowner", type=FieldType.STRING, description="The canonical user ID of the owner of the source bucket"),
            SchemaField(name="bucket_name", type=FieldType.STRING, description="The name of the bucket that the request was processed against"),
            SchemaField(name="requestdatetime", type=FieldType.STRING, description="The time at which the request was received"),
            SchemaField(name="remoteip", type=FieldType.STRING, description="The apparent internet address of the requester"),
            SchemaField(name="requester", type=FieldType.STRING, description="The canonical user ID of the requester, or a - for unauthenticated requests"),
            SchemaField(name="requestid", type=FieldType.STRING, description="A string generated by Amazon S3 to uniquely identify each request"),
            SchemaField(name="operation", type=FieldType.STRING, description="The operation that was requested"),
            SchemaField(name="key", type=FieldType.STRING, description="The key part of the request, URL encoded, or - if the operation does not take a key parameter"),
            SchemaField(name="request_uri", type=FieldType.STRING, description="The Request-URI part of the HTTP request message"),
            SchemaField(name="httpstatus", type=FieldType.STRING, description="The numeric HTTP status code of the response"),
            SchemaField(name="errorcode", type=FieldType.STRING, description="The Amazon S3 Error Code, or - if no error occurred"),
            SchemaField(name="bytessent", type=FieldType.BIGINT, description="The number of response bytes sent, excluding HTTP protocol overhead, or - if zero"),
            SchemaField(name="objectsize", type=FieldType.BIGINT, description="The total size of the object in question"),
            SchemaField(name="totaltime", type=FieldType.STRING, description="The number of milliseconds the request was in flight from the server's perspective"),
            SchemaField(name="turnaroundtime", type=FieldType.STRING, description="The number of milliseconds that Amazon S3 spent processing your request"),
            SchemaField(name="referrer", type=FieldType.STRING, description="The value of the HTTP Referer header, if present"),
            SchemaField(name="useragent", type=FieldType.STRING, description="The value of the HTTP User-Agent header"),
            SchemaField(name="versionid", type=FieldType.STRING, description="The version ID in the request, or - if the operation does not take a versionId parameter"),
            SchemaField(name="hostid", type=FieldType.STRING, description="The x-amz-id-2 or Amazon S3 extended request ID"),
            SchemaField(name="sigv", type=FieldType.STRING, description="The signature version, SigV2 or SigV4, that was used to authenticate the request"),
            SchemaField(name="ciphersuite", type=FieldType.STRING, description="The Secure Sockets Layer (SSL) cipher that was negotiated for HTTPS request"),
            SchemaField(name="authtype", type=FieldType.STRING, description="The type of request authentication used"),
            SchemaField(name="endpoint", type=FieldType.STRING, description="The endpoint used to connect to Amazon S3"),
            SchemaField(name="tlsversion", type=FieldType.STRING, description="The Transport Layer Security (TLS) version negotiated by the client"),
            SchemaField(name="accesspointarn", type=FieldType.STRING, description="The Amazon Resource Name (ARN) of the access point"),
            SchemaField(name="aclrequired", type=FieldType.STRING, description="Whether the request required ACL authorization")
        ]
        
        regex_pattern = r'([^ ]*) ([^ ]*) \[(.*?)\] ([^ ]*) ([^ ]*) ([^ ]*) ([^ ]*) ([^ ]*) (\"[^\"]*\"|-) (-|[0-9]*) ([^ ]*) ([^ ]*) ([^ ]*) ([^ ]*) ([^ ]*) ([^ ]*) (\"[^\"]*\"|-) ([^ ]*)(?: ([^ ]*) ([^ ]*) ([^ ]*) ([^ ]*) ([^ ]*) ([^ ]*) ([^ ]*) ([^ ]*))?.*$'
        
        
        # 샘플 로그 라인
        sample_log = '79a59df900b949e55d96a1e698fbacedfd6e09d98eacf8f8d5218e7cd47ef2be mybucket [06/Feb/2019:00:00:38 +0000] 192.0.2.3 79a59df900b949e55d96a1e698fbacedfd6e09d98eacf8f8d5218e7cd47ef2be 3E57427F3EXAMPLE REST.GET.VERSIONING - "GET /mybucket?versioning HTTP/1.1" 200 - 113 - 7 - "-" "S3Console/0.4" - s9lzHYrFp76ZVxRcpX9+5cjAnEH2ROuNkd2BHfIa6UkFVdtjf5mKR3/eTPFvsiP/XV/VLi31234= SigV2 ECDHE-RSA-AES128-GCM-SHA256 AuthHeader mybucket.s3.amazonaws.com TLSV1.1 - -'
        
        return LogSchema(
            log_type=LogType.S3_ACCESS,
            name="S3 Access Log",
            description="Amazon S3 server access log format with 26 fields (AWS Official)",
            fields=fields,
            sample_log_pattern=sample_log,
            regex_pattern=regex_pattern,
            partition_fields=["timestamp"]
        )
    
    def _create_cloudfront_schema(self) -> LogSchema:
        """CloudFront 로그 스키마 생성"""
        
        fields = [
            SchemaField(name="date", type=FieldType.DATE, description="The date on which the event occurred"),
            SchemaField(name="time", type=FieldType.STRING, description="The time when the CloudFront server finished responding to the request"),
            SchemaField(name="x_edge_location", type=FieldType.STRING, description="The edge location that served the request"),
            SchemaField(name="sc_bytes", type=FieldType.BIGINT, description="The total number of bytes that CloudFront served to the viewer"),
            SchemaField(name="c_ip", type=FieldType.STRING, description="The IP address of the viewer that made the request"),
            SchemaField(name="cs_method", type=FieldType.STRING, description="The HTTP access method: DELETE, GET, HEAD, OPTIONS, PATCH, POST, or PUT"),
            SchemaField(name="cs_host", type=FieldType.STRING, description="The domain name of the CloudFront distribution"),
            SchemaField(name="cs_uri_stem", type=FieldType.STRING, description="The portion of the URI that identifies the path and object"),
            SchemaField(name="sc_status", type=FieldType.INT, description="The HTTP status code"),
            SchemaField(name="cs_referer", type=FieldType.STRING, description="The name of the domain that originated the request"),
            SchemaField(name="cs_user_agent", type=FieldType.STRING, description="The value of the User-Agent header in the request"),
            SchemaField(name="cs_uri_query", type=FieldType.STRING, description="The query string portion of the URI, if any"),
            SchemaField(name="cs_cookie", type=FieldType.STRING, description="The cookie header in the request, including name-value pairs"),
            SchemaField(name="x_edge_result_type", type=FieldType.STRING, description="How CloudFront classified the response"),
            SchemaField(name="x_edge_request_id", type=FieldType.STRING, description="An encrypted string that uniquely identifies a request"),
            SchemaField(name="x_host_header", type=FieldType.STRING, description="The value that the viewer included in the Host header"),
            SchemaField(name="cs_protocol", type=FieldType.STRING, description="The protocol that the viewer specified in the request"),
            SchemaField(name="cs_bytes", type=FieldType.BIGINT, description="The number of bytes of data that the viewer included in the request"),
            SchemaField(name="time_taken", type=FieldType.DOUBLE, description="The number of seconds between receiving the request and writing the last byte of the response"),
            SchemaField(name="x_forwarded_for", type=FieldType.STRING, description="If the viewer used an HTTP proxy or a load balancer, the IP address of the proxy or load balancer"),
            SchemaField(name="ssl_protocol", type=FieldType.STRING, description="When cs-protocol is https, the SSL/TLS protocol that the client and CloudFront negotiated"),
            SchemaField(name="ssl_cipher", type=FieldType.STRING, description="When cs-protocol is https, the SSL/TLS cipher that the client and CloudFront negotiated"),
            SchemaField(name="x_edge_response_result_type", type=FieldType.STRING, description="How CloudFront classified the response after the last byte left the edge location"),
            SchemaField(name="cs_protocol_version", type=FieldType.STRING, description="The HTTP version that the viewer specified in the request"),
        ]
        
        regex_pattern = r'^\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\s+\w{3}\d+'
        sample_log = '2023-01-01\t12:00:00\tLAX3\t1234\t192.168.1.1\tGET\texample.cloudfront.net\t/index.html\t200\t-\tMozilla/5.0\t-\t-\tHit\trequest-id\texample.com\thttps\t500\t0.001\t-\tTLSv1.3\tECDHE-RSA-AES128-GCM-SHA256\tHit\tHTTP/2.0'
        
        return LogSchema(
            log_type=LogType.CLOUDFRONT,
            name="CloudFront Access Log",
            description="Amazon CloudFront standard access log format",
            fields=fields,
            sample_log_pattern=sample_log,
            regex_pattern=regex_pattern,
            partition_fields=["year", "month", "day"]
        )
    
    def _create_alb_schema(self) -> LogSchema:
        """ALB 로그 스키마 생성 - AWS 공식 문서 기준"""
        
        fields = [
            SchemaField(name="type", type=FieldType.STRING, description="The type of request or connection"),
            SchemaField(name="time", type=FieldType.STRING, description="The time when the load balancer generated a response to the client"),
            SchemaField(name="elb", type=FieldType.STRING, description="The resource ID of the load balancer"),
            SchemaField(name="client_ip", type=FieldType.STRING, description="The IP address of the requesting client"),
            SchemaField(name="client_port", type=FieldType.INT, description="The port of the requesting client"),
            SchemaField(name="target_ip", type=FieldType.STRING, description="The IP address of the target that processed this request"),
            SchemaField(name="target_port", type=FieldType.INT, description="The port of the target that processed this request"),
            SchemaField(name="request_processing_time", type=FieldType.DOUBLE, description="The total time elapsed in seconds from the time the load balancer received the request until the time it sent it to a target"),
            SchemaField(name="target_processing_time", type=FieldType.DOUBLE, description="The total time elapsed in seconds from the time the load balancer sent the request to a target until the target started to send the response headers"),
            SchemaField(name="response_processing_time", type=FieldType.DOUBLE, description="The total time elapsed in seconds from the time the load balancer received the response header from the target until it started to send the response to the client"),
            SchemaField(name="elb_status_code", type=FieldType.INT, description="The status code of the response from the load balancer"),
            SchemaField(name="target_status_code", type=FieldType.STRING, description="The status code of the response from the target"),
            SchemaField(name="received_bytes", type=FieldType.BIGINT, description="The size of the request in bytes received from the client"),
            SchemaField(name="sent_bytes", type=FieldType.BIGINT, description="The size of the response in bytes sent to the client"),
            SchemaField(name="request_verb", type=FieldType.STRING, description="The HTTP request method"),
            SchemaField(name="request_url", type=FieldType.STRING, description="The request URL"),
            SchemaField(name="request_proto", type=FieldType.STRING, description="The request protocol"),
            SchemaField(name="user_agent", type=FieldType.STRING, description="A User-Agent string that identifies the client that originated the request"),
            SchemaField(name="ssl_cipher", type=FieldType.STRING, description="The SSL cipher"),
            SchemaField(name="ssl_protocol", type=FieldType.STRING, description="The SSL protocol"),
            SchemaField(name="target_group_arn", type=FieldType.STRING, description="The Amazon Resource Name (ARN) of the target group"),
            SchemaField(name="trace_id", type=FieldType.STRING, description="The contents of the X-Amzn-Trace-Id header"),
            SchemaField(name="domain_name", type=FieldType.STRING, description="The SNI domain provided by the client during the TLS handshake"),
            SchemaField(name="chosen_cert_arn", type=FieldType.STRING, description="The ARN of the certificate presented to the client"),
            SchemaField(name="matched_rule_priority", type=FieldType.STRING, description="The priority value of the rule that matched the request"),
            SchemaField(name="request_creation_time", type=FieldType.STRING, description="The time when the load balancer received the request from the client"),
            SchemaField(name="actions_executed", type=FieldType.STRING, description="The actions taken when processing the request"),
            SchemaField(name="redirect_url", type=FieldType.STRING, description="The URL of the redirect target for the location header of the HTTP response"),
            SchemaField(name="lambda_error_reason", type=FieldType.STRING, description="The error reason from Lambda"),
            SchemaField(name="target_port_list", type=FieldType.STRING, description="A space-delimited list of IP addresses and ports for the targets that processed this request"),
            SchemaField(name="target_status_code_list", type=FieldType.STRING, description="A space-delimited list of status codes from the responses of the targets"),
            SchemaField(name="classification", type=FieldType.STRING, description="The classification for desync mitigation"),
            SchemaField(name="classification_reason", type=FieldType.STRING, description="The classification reason code"),
            SchemaField(name="conn_trace_id", type=FieldType.STRING, description="The connection trace ID"),
        ]
        
        # AWS 공식 문서의 정규식 패턴
        regex_pattern = r'([^ ]*) ([^ ]*) ([^ ]*) ([^ ]*):([0-9]*) ([^ ]*)[:-]([0-9]*) ([-.0-9]*) ([-.0-9]*) ([-.0-9]*) (|[-0-9]*) (-|[-0-9]*) ([-0-9]*) ([-0-9]*) \"([^ ]*) (.*) (- |[^ ]*)\" \"([^\"]*)\" ([A-Z0-9-_]+) ([A-Za-z0-9.-]*) ([^ ]*) \"([^\"]*)\" \"([^\"]*)\" \"([^\"]*)\" ([-.0-9]*) ([^ ]*) \"([^\"]*)\" \"([^\"]*)\" \"([^ ]*)\" \"([^\\s]+?)\" \"([^\\s]+)\" \"([^ ]*)\" \"([^ ]*)\" ?([^ ]*)? ?( .*)?'
        
        sample_log = 'http 2023-01-01T12:00:00.123456Z app/my-loadbalancer/50dc6c495c0c9188 192.168.1.1:12345 10.0.0.1:80 0.000 0.001 0.000 200 200 0 29 "GET http://example.com:80/ HTTP/1.1" "Mozilla/5.0" ECDHE-RSA-AES128-GCM-SHA256 TLSv1.2 arn:aws:elasticloadbalancing:us-east-1:123456789012:targetgroup/my-targets/73e2d6bc24d8a067 "Root=1-58337262-36d228ad5d99923122bbe354" "-" "-" 0 2023-01-01T12:00:00.123000Z "forward" "-" "-" "10.0.0.1:80" "200" "-" "-"'
        
        return LogSchema(
            log_type=LogType.ALB,
            name="ALB Access Log",
            description="Application Load Balancer access log format (AWS Official)",
            fields=fields,
            sample_log_pattern=sample_log,
            regex_pattern=regex_pattern,
            partition_fields=["year", "month", "day"]
        )
    
    def _create_vpc_flow_schema(self) -> LogSchema:
        """VPC Flow 로그 스키마 생성"""
        
        fields = [
            SchemaField(name="version", type=FieldType.INT, description="The VPC Flow Logs version"),
            SchemaField(name="account_id", type=FieldType.STRING, description="The AWS account ID for the flow log"),
            SchemaField(name="interface_id", type=FieldType.STRING, description="The ID of the network interface for which the traffic is recorded"),
            SchemaField(name="srcaddr", type=FieldType.STRING, description="The source IPv4 or IPv6 address"),
            SchemaField(name="dstaddr", type=FieldType.STRING, description="The destination IPv4 or IPv6 address"),
            SchemaField(name="srcport", type=FieldType.INT, description="The source port of the traffic"),
            SchemaField(name="dstport", type=FieldType.INT, description="The destination port of the traffic"),
            SchemaField(name="protocol", type=FieldType.INT, description="The IANA protocol number of the traffic"),
            SchemaField(name="packets", type=FieldType.BIGINT, description="The number of packets transferred during the capture window"),
            SchemaField(name="bytes", type=FieldType.BIGINT, description="The number of bytes transferred during the capture window"),
            SchemaField(name="start", type=FieldType.BIGINT, description="The time, in Unix seconds, of the start of the capture window"),
            SchemaField(name="end", type=FieldType.BIGINT, description="The time, in Unix seconds, of the end of the capture window"),
            SchemaField(name="action", type=FieldType.STRING, description="The action associated with the traffic: ACCEPT or REJECT"),
            SchemaField(name="log_status", type=FieldType.STRING, description="The logging status of the flow log: OK, NODATA, or SKIPDATA"),
        ]
        
        regex_pattern = r'^2\s+\d+\s+eni-[a-f0-9]+\s+'
        sample_log = '2 123456789012 eni-1235b8ca123456789 172.31.16.139 172.31.16.21 20641 22 6 20 4249 1418530010 1418530070 ACCEPT OK'
        
        return LogSchema(
            log_type=LogType.VPC_FLOW,
            name="VPC Flow Log",
            description="Amazon VPC Flow Logs format (version 2)",
            fields=fields,
            sample_log_pattern=sample_log,
            regex_pattern=regex_pattern,
            partition_fields=["year", "month", "day"]
        )
    
    def _create_cloudtrail_schema(self) -> LogSchema:
        """CloudTrail 로그 스키마 생성 (JSON 형식)"""
        
        fields = [
            SchemaField(name="eventversion", type=FieldType.STRING, description="The version of the log event format"),
            SchemaField(name="useridentity", type=FieldType.STRING, description="Information about the IAM identity that made the request"),
            SchemaField(name="eventtime", type=FieldType.STRING, description="The date and time the request was made"),
            SchemaField(name="eventsource", type=FieldType.STRING, description="The service that the request was made to"),
            SchemaField(name="eventname", type=FieldType.STRING, description="The requested action"),
            SchemaField(name="awsregion", type=FieldType.STRING, description="The AWS region that the request was made to"),
            SchemaField(name="sourceipaddress", type=FieldType.STRING, description="The IP address that the request was made from"),
            SchemaField(name="useragent", type=FieldType.STRING, description="The agent through which the request was made"),
            SchemaField(name="errorcode", type=FieldType.STRING, description="The AWS service error if the request returns an error"),
            SchemaField(name="errormessage", type=FieldType.STRING, description="If the request returns an error, the description of the error"),
            SchemaField(name="requestparameters", type=FieldType.STRING, description="The parameters, if any, that were sent with the request"),
            SchemaField(name="responseelements", type=FieldType.STRING, description="The response element for actions that make changes"),
            SchemaField(name="requestid", type=FieldType.STRING, description="The value that identifies the request"),
            SchemaField(name="eventid", type=FieldType.STRING, description="GUID generated by CloudTrail to uniquely identify each event"),
            SchemaField(name="eventtype", type=FieldType.STRING, description="Identifies the type of event that generated the event record"),
            SchemaField(name="recipientaccountid", type=FieldType.STRING, description="Represents the account ID that received this event"),
        ]
        
        regex_pattern = r'^\{.*"Records".*\}'
        sample_log = '{"Records": [{"eventVersion": "1.05", "userIdentity": {"type": "IAMUser", "principalId": "AIDAI...", "arn": "arn:aws:iam::123456789012:user/Alice"}, "eventTime": "2023-01-01T12:00:00Z", "eventSource": "s3.amazonaws.com", "eventName": "GetObject", "awsRegion": "us-east-1", "sourceIPAddress": "192.0.2.1", "userAgent": "aws-cli/2.0.0", "requestParameters": {"bucketName": "my-bucket", "key": "my-file.txt"}, "responseElements": null, "requestID": "EXAMPLE123", "eventID": "EXAMPLE456", "eventType": "AwsApiCall", "recipientAccountId": "123456789012"}]}'
        
        return LogSchema(
            log_type=LogType.CLOUDTRAIL,
            name="CloudTrail Log",
            description="AWS CloudTrail log format (JSON)",
            fields=fields,
            sample_log_pattern=sample_log,
            regex_pattern=regex_pattern,
            partition_fields=["year", "month", "day"]
        )


# 전역 스키마 레지스트리 인스턴스
schema_registry = LogSchemaRegistry()


def get_schema_for_log_type(log_type: LogType) -> Optional[LogSchema]:
    """로그 타입에 해당하는 스키마 반환"""
    return schema_registry.get_schema(log_type)


def get_available_log_types() -> List[LogType]:
    """사용 가능한 로그 타입 목록 반환"""
    return list(schema_registry.get_all_schemas().keys())
