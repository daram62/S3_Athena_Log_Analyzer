-- CLOUDFRONT DDL
-- Generated for bucket: 5.cloudfront-logs-777786711649
-- Database: genai_log_analyzer
-- Table: cloudfront_logs

CREATE EXTERNAL TABLE `genai_log_analyzer`.`cloudfront_logs` (
  `date` date,
  `time` string,
  `x_edge_location` string,
  `sc_bytes` bigint,
  `c_ip` string,
  `cs_method` string,
  `cs_host` string,
  `cs_uri_stem` string,
  `sc_status` int,
  `cs_referer` string,
  `cs_user_agent` string,
  `cs_uri_query` string,
  `cs_cookie` string,
  `x_edge_result_type` string,
  `x_edge_request_id` string,
  `x_host_header` string,
  `cs_protocol` string,
  `cs_bytes` bigint,
  `time_taken` double,
  `x_forwarded_for` string,
  `ssl_protocol` string,
  `ssl_cipher` string,
  `x_edge_response_result_type` string,
  `cs_protocol_version` string
)
PARTITIONED BY (
  `year` string, `month` string, `day` string
)
STORED AS INPUTFORMAT 
  'org.apache.hadoop.mapred.TextInputFormat' 
OUTPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat'
LOCATION
  's3://5.cloudfront-logs-777786711649/'
TBLPROPERTIES (
  'classification'='csv',
  'delimiter'='\t',
  'skip.header.line.count'='2',
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
  'storage.location.template'='s3://5.cloudfront-logs-777786711649/year=${year}/month=${month:02d}/day=${day:02d}/',
  'serde.param.field.delim'='	',
  'serde.param.serialization.format'='	'
)