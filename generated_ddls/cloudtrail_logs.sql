-- CLOUDTRAIL DDL
-- Generated for bucket: 4.cloudtrail-logs-777786711649
-- Database: genai_log_analyzer
-- Table: cloudtrail_logs

CREATE EXTERNAL TABLE `genai_log_analyzer`.`cloudtrail_logs` (
  `eventversion` string,
  `useridentity` struct<
    type:string,
    principalid:string,
    arn:string,
    accountid:string,
    invokedby:string,
    accesskeyid:string,
    userName:string,
    sessioncontext:struct<
      attributes:struct<
        mfaauthenticated:string,
        creationdate:string>,
      sessionissuer:struct<
        type:string,
        principalId:string,
        arn:string,
        accountId:string,
        userName:string>>>,
  `eventtime` string,
  `eventsource` string,
  `eventname` string,
  `awsregion` string,
  `sourceipaddress` string,
  `useragent` string,
  `errorcode` string,
  `errormessage` string,
  `requestparameters` string,
  `responseelements` string,
  `additionaleventdata` string,
  `requestid` string,
  `eventid` string,
  `resources` array<struct<
    ARN:string,
    accountId:string,
    type:string>>,
  `eventtype` string,
  `apiversion` string,
  `readonly` string,
  `recipientaccountid` string,
  `serviceeventdetails` string,
  `sharedeventid` string,
  `vpcendpointid` string
)
PARTITIONED BY (
  `year` string,
  `month` string,
  `day` string
)
ROW FORMAT SERDE 'com.amazon.emr.hive.serde.CloudTrailSerde'
STORED AS INPUTFORMAT 'com.amazon.emr.cloudtrail.CloudTrailInputFormat'
OUTPUTFORMAT 'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat'
LOCATION 's3://4.cloudtrail-logs-777786711649/'
TBLPROPERTIES (
  'classification'='cloudtrail',
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
  'storage.location.template'='s3://4.cloudtrail-logs-777786711649/year=${year}/month=${month:02d}/day=${day:02d}/'
)