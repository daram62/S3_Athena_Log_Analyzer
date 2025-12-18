-- VPC_FLOW DDL
-- Generated for bucket: 3.vpc-flow-logs-777786711649
-- Database: genai_log_analyzer
-- Table: vpc_flow_logs

CREATE EXTERNAL TABLE `genai_log_analyzer`.`vpc_flow_logs` (
  `version` int,
  `account_id` string,
  `interface_id` string,
  `srcaddr` string,
  `dstaddr` string,
  `srcport` int,
  `dstport` int,
  `protocol` int,
  `packets` bigint,
  `bytes` bigint,
  `start` bigint,
  `end` bigint,
  `action` string,
  `log_status` string
)
PARTITIONED BY (
  `year` string, `month` string, `day` string
)
STORED AS INPUTFORMAT 
  'org.apache.hadoop.mapred.TextInputFormat' 
OUTPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat'
LOCATION
  's3://3.vpc-flow-logs-777786711649/'
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
  'storage.location.template'='s3://3.vpc-flow-logs-777786711649/year=${year}/month=${month:02d}/day=${day:02d}/',
  'serde.param.field.delim'=' ',
  'serde.param.serialization.format'=' '
)