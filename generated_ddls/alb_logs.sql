-- ALB DDL
-- Generated for bucket: 2.alb-access-logs-777786711649
-- Database: genai_log_analyzer
-- Table: alb_logs

CREATE EXTERNAL TABLE `genai_log_analyzer`.`alb_logs` (
  `type` string,
  `time` string,
  `elb` string,
  `client_ip` string,
  `client_port` int,
  `target_ip` string,
  `target_port` int,
  `request_processing_time` double,
  `target_processing_time` double,
  `response_processing_time` double,
  `elb_status_code` int,
  `target_status_code` int,
  `received_bytes` bigint,
  `sent_bytes` bigint,
  `request_verb` string,
  `request_url` string,
  `request_proto` string,
  `user_agent` string,
  `ssl_cipher` string,
  `ssl_protocol` string,
  `target_group_arn` string,
  `trace_id` string,
  `domain_name` string,
  `chosen_cert_arn` string,
  `matched_rule_priority` string,
  `request_creation_time` string,
  `actions_executed` string,
  `redirect_url` string,
  `error_reason` string
)
PARTITIONED BY (
  `year` string, `month` string, `day` string
)
STORED AS INPUTFORMAT 
  'org.apache.hadoop.mapred.TextInputFormat' 
OUTPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat'
LOCATION
  's3://2.alb-access-logs-777786711649/'
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
  'storage.location.template'='s3://2.alb-access-logs-777786711649/year=${year}/month=${month:02d}/day=${day:02d}/',
  'serde.param.field.delim'=' ',
  'serde.param.serialization.format'=' '
)