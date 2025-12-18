-- S3_ACCESS DDL
-- Generated for bucket: 1.s3-access-logs-777786711649
-- Database: genai_log_analyzer
-- Table: s3_access_logs

CREATE EXTERNAL TABLE `genai_log_analyzer`.`s3_access_logs` (
  `bucket_owner` string,
  `bucket` string,
  `time` string,
  `remote_ip` string,
  `requester` string,
  `request_id` string,
  `operation` string,
  `key` string,
  `request_uri` string,
  `http_status` int,
  `error_code` string,
  `bytes_sent` bigint,
  `object_size` bigint,
  `total_time` int,
  `turn_around_time` int,
  `referer` string,
  `user_agent` string,
  `version_id` string,
  `host_id` string,
  `signature_version` string,
  `cipher_suite` string,
  `authentication_type` string,
  `host_header` string,
  `tls_version` string,
  `access_point_arn` string,
  `acl_required` string
)
PARTITIONED BY (
  `year` string, `month` string, `day` string
)
STORED AS INPUTFORMAT 
  'org.apache.hadoop.mapred.TextInputFormat' 
OUTPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat'
LOCATION
  's3://1.s3-access-logs-777786711649/'
TBLPROPERTIES (
  'classification'='csv',
  'delimiter'=' ',
  'skip.header.line.count'='0',
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
  'storage.location.template'='s3://1.s3-access-logs-777786711649/year=${year}/month=${month:02d}/day=${day:02d}/',
  'serde.param.field.delim'=' ',
  'serde.param.serialization.format'=' '
)