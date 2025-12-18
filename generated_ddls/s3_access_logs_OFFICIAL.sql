================================================================================
S3 Access Logs DDL (AWS 공식 문서 기준)
================================================================================
CREATE EXTERNAL TABLE `s3_access_logs_db`.`mybucket_logs` (
  `bucketowner` string,
  `bucket_name` string,
  `requestdatetime` string,
  `remoteip` string,
  `requester` string,
  `requestid` string,
  `operation` string,
  `key` string,
  `request_uri` string,
  `httpstatus` string,
  `errorcode` string,
  `bytessent` bigint,
  `objectsize` bigint,
  `totaltime` string,
  `turnaroundtime` string,
  `referrer` string,
  `useragent` string,
  `versionid` string,
  `hostid` string,
  `sigv` string,
  `ciphersuite` string,
  `authtype` string,
  `endpoint` string,
  `tlsversion` string,
  `accesspointarn` string,
  `aclrequired` string
)
PARTITIONED BY (
  `timestamp` string
)
ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.RegexSerDe'
WITH SERDEPROPERTIES (
  'input.regex'='([^ ]*) ([^ ]*) \[(.*?)\] ([^ ]*) ([^ ]*) ([^ ]*) ([^ ]*) ([^ ]*) (\"[^\"]*\"|-) (-|[0-9]*) ([^ ]*) ([^ ]*) ([^ ]*) ([^ ]*) ([^ ]*) ([^ ]*) (\"[^\"]*\"|-) ([^ ]*)(?: ([^ ]*) ([^ ]*) ([^ ]*) ([^ ]*) ([^ ]*) ([^ ]*) ([^ ]*) ([^ ]*))?.*$'
)
STORED AS INPUTFORMAT 
  'org.apache.hadoop.mapred.TextInputFormat' 
OUTPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat'
LOCATION
  's3://bucket-name/prefix-name/account-id/region/source-bucket-name/'
TBLPROPERTIES (
  'projection.enabled'='true',
  'projection.timestamp.format'='yyyy/MM/dd',
  'projection.timestamp.interval'='1',
  'projection.timestamp.interval.unit'='DAYS',
  'projection.timestamp.range'='2024/01/01,NOW',
  'projection.timestamp.type'='date',
  'storage.location.template'='s3://bucket-name/prefix-name/account-id/region/source-bucket-name/${timestamp}'
)

================================================================================
필드 개수: 26
파티션 필드: ['timestamp']
================================================================================
