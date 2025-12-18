#!/usr/bin/env python3
"""
가상 AWS 로그 파일 생성기
CloudFront, ALB, VPC Flow, CloudTrail 로그 샘플 생성
"""

import json
import random
from datetime import datetime, timedelta
from pathlib import Path

# 샘플 데이터
SAMPLE_IPS = ["192.168.1.1", "10.0.0.1", "172.31.16.139", "203.0.113.42", "198.51.100.23"]
SAMPLE_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "curl/7.68.0",
    "aws-cli/2.0.0",
    "Python-urllib/3.8"
]
SAMPLE_PATHS = ["/index.html", "/api/users", "/images/logo.png", "/css/style.css", "/api/data"]
SAMPLE_METHODS = ["GET", "POST", "PUT", "DELETE"]
SAMPLE_STATUS_CODES = [200, 200, 200, 304, 400, 403, 404, 500]


def generate_cloudfront_logs(num_lines=100):
    """CloudFront 로그 생성 (탭 구분)"""
    lines = []
    
    # 헤더
    lines.append("#Version: 1.0")
    lines.append("#Fields: date time x-edge-location sc-bytes c-ip cs-method cs(Host) cs-uri-stem sc-status cs(Referer) cs(User-Agent) cs-uri-query cs(Cookie) x-edge-result-type x-edge-request-id x-host-header cs-protocol cs-bytes time-taken x-forwarded-for ssl-protocol ssl-cipher x-edge-response-result-type cs-protocol-version")
    
    # 데이터 라인
    base_date = datetime.now() - timedelta(days=7)
    
    for i in range(num_lines):
        date = (base_date + timedelta(hours=i)).strftime("%Y-%m-%d")
        time = (base_date + timedelta(hours=i)).strftime("%H:%M:%S")
        edge_location = random.choice(["LAX3", "ICN50", "NRT57", "SFO5", "SEA19"])
        sc_bytes = random.randint(1000, 50000)
        c_ip = random.choice(SAMPLE_IPS)
        method = random.choice(SAMPLE_METHODS)
        host = "example.cloudfront.net"
        uri_stem = random.choice(SAMPLE_PATHS)
        status = random.choice(SAMPLE_STATUS_CODES)
        referer = "-"
        user_agent = random.choice(SAMPLE_USER_AGENTS)
        uri_query = "-"
        cookie = "-"
        result_type = random.choice(["Hit", "Miss", "RefreshHit", "Error"])
        request_id = f"req-{random.randint(100000, 999999)}"
        host_header = "example.com"
        protocol = "https"
        cs_bytes = random.randint(100, 1000)
        time_taken = round(random.uniform(0.001, 0.5), 3)
        forwarded_for = "-"
        ssl_protocol = "TLSv1.3"
        ssl_cipher = "ECDHE-RSA-AES128-GCM-SHA256"
        response_result_type = result_type
        protocol_version = "HTTP/2.0"
        
        line = f"{date}\t{time}\t{edge_location}\t{sc_bytes}\t{c_ip}\t{method}\t{host}\t{uri_stem}\t{status}\t{referer}\t{user_agent}\t{uri_query}\t{cookie}\t{result_type}\t{request_id}\t{host_header}\t{protocol}\t{cs_bytes}\t{time_taken}\t{forwarded_for}\t{ssl_protocol}\t{ssl_cipher}\t{response_result_type}\t{protocol_version}"
        lines.append(line)
    
    return "\n".join(lines)


def generate_alb_logs(num_lines=100):
    """ALB 로그 생성 (공백 구분)"""
    lines = []
    base_date = datetime.now() - timedelta(days=7)
    
    for i in range(num_lines):
        request_type = random.choice(["http", "https", "h2", "ws", "wss"])
        timestamp = (base_date + timedelta(hours=i)).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        elb = f"app/my-loadbalancer/{random.randint(10000000, 99999999)}"
        client_ip = random.choice(SAMPLE_IPS)
        client_port = random.randint(40000, 65000)
        target_ip = random.choice(SAMPLE_IPS)
        target_port = random.choice([80, 443, 8080])
        request_processing_time = round(random.uniform(0.0, 0.01), 3)
        target_processing_time = round(random.uniform(0.001, 0.1), 3)
        response_processing_time = round(random.uniform(0.0, 0.01), 3)
        elb_status_code = random.choice(SAMPLE_STATUS_CODES)
        target_status_code = random.choice(SAMPLE_STATUS_CODES)
        received_bytes = random.randint(0, 1000)
        sent_bytes = random.randint(100, 50000)
        method = random.choice(SAMPLE_METHODS)
        url = f"http://example.com:80{random.choice(SAMPLE_PATHS)}"
        http_version = "HTTP/1.1"
        user_agent = random.choice(SAMPLE_USER_AGENTS)
        ssl_cipher = "ECDHE-RSA-AES128-GCM-SHA256" if request_type in ["https", "h2"] else "-"
        ssl_protocol = "TLSv1.2" if request_type in ["https", "h2"] else "-"
        target_group_arn = f"arn:aws:elasticloadbalancing:us-east-1:123456789012:targetgroup/my-targets/{random.randint(10000000, 99999999)}"
        trace_id = f"Root=1-{random.randint(10000000, 99999999)}-{random.randint(10000000, 99999999)}"
        domain_name = "-"
        chosen_cert_arn = "-"
        matched_rule_priority = "0"
        request_creation_time = timestamp
        actions_executed = "forward"
        redirect_url = "-"
        error_reason = "-"
        
        line = f'{request_type} {timestamp} {elb} {client_ip}:{client_port} {target_ip}:{target_port} {request_processing_time} {target_processing_time} {response_processing_time} {elb_status_code} {target_status_code} {received_bytes} {sent_bytes} "{method} {url} {http_version}" "{user_agent}" {ssl_cipher} {ssl_protocol} {target_group_arn} "{trace_id}" "{domain_name}" "{chosen_cert_arn}" {matched_rule_priority} {request_creation_time} "{actions_executed}" "{redirect_url}" "{error_reason}"'
        lines.append(line)
    
    return "\n".join(lines)


def generate_vpc_flow_logs(num_lines=100):
    """VPC Flow 로그 생성 (공백 구분)"""
    lines = []
    
    # 헤더 (선택사항)
    lines.append("version account-id interface-id srcaddr dstaddr srcport dstport protocol packets bytes start end action log-status")
    
    base_time = int((datetime.now() - timedelta(days=7)).timestamp())
    
    for i in range(num_lines):
        version = 2
        account_id = "123456789012"
        interface_id = f"eni-{random.randint(10000000, 99999999):08x}"
        srcaddr = random.choice(SAMPLE_IPS)
        dstaddr = random.choice(SAMPLE_IPS)
        srcport = random.randint(1024, 65535)
        dstport = random.choice([22, 80, 443, 3306, 5432, 6379])
        protocol = random.choice([6, 17])  # 6=TCP, 17=UDP
        packets = random.randint(1, 100)
        bytes_transferred = random.randint(100, 100000)
        start = base_time + (i * 60)
        end = start + 60
        action = random.choice(["ACCEPT", "ACCEPT", "ACCEPT", "REJECT"])
        log_status = "OK"
        
        line = f"{version} {account_id} {interface_id} {srcaddr} {dstaddr} {srcport} {dstport} {protocol} {packets} {bytes_transferred} {start} {end} {action} {log_status}"
        lines.append(line)
    
    return "\n".join(lines)


def generate_cloudtrail_logs(num_events=50):
    """CloudTrail 로그 생성 (JSON)"""
    records = []
    base_date = datetime.now() - timedelta(days=7)
    
    event_names = ["GetObject", "PutObject", "ListBucket", "CreateBucket", "DeleteObject"]
    event_sources = ["s3.amazonaws.com", "ec2.amazonaws.com", "iam.amazonaws.com", "lambda.amazonaws.com"]
    
    for i in range(num_events):
        event_time = (base_date + timedelta(hours=i)).strftime("%Y-%m-%dT%H:%M:%SZ")
        
        record = {
            "eventVersion": "1.08",
            "userIdentity": {
                "type": "IAMUser",
                "principalId": f"AIDAI{random.randint(100000000000, 999999999999)}",
                "arn": f"arn:aws:iam::123456789012:user/user-{random.randint(1, 10)}",
                "accountId": "123456789012",
                "accessKeyId": f"AKIAI{random.randint(100000000000, 999999999999)}",
                "userName": f"user-{random.randint(1, 10)}"
            },
            "eventTime": event_time,
            "eventSource": random.choice(event_sources),
            "eventName": random.choice(event_names),
            "awsRegion": "us-east-1",
            "sourceIPAddress": random.choice(SAMPLE_IPS),
            "userAgent": random.choice(SAMPLE_USER_AGENTS),
            "requestParameters": {
                "bucketName": f"my-bucket-{random.randint(1, 5)}",
                "key": random.choice(SAMPLE_PATHS).lstrip("/")
            },
            "responseElements": None,
            "requestID": f"REQ{random.randint(100000000000, 999999999999)}",
            "eventID": f"EVT{random.randint(100000000000, 999999999999)}",
            "readOnly": random.choice([True, False]),
            "eventType": "AwsApiCall",
            "recipientAccountId": "123456789012"
        }
        records.append(record)
    
    return json.dumps({"Records": records}, indent=2)


def main():
    """메인 함수"""
    print("=" * 60)
    print("🎨 AWS 로그 샘플 생성기")
    print("=" * 60)
    print()
    
    # 출력 디렉토리 생성
    output_dir = Path("sample_logs")
    output_dir.mkdir(exist_ok=True)
    
    # 1. CloudFront 로그
    print("📦 CloudFront 로그 생성 중...")
    cloudfront_log = generate_cloudfront_logs(100)
    cloudfront_file = output_dir / "cloudfront_access.log"
    cloudfront_file.write_text(cloudfront_log)
    print(f"   ✅ {cloudfront_file} ({len(cloudfront_log)} bytes)")
    
    # 2. ALB 로그
    print("📦 ALB 로그 생성 중...")
    alb_log = generate_alb_logs(100)
    alb_file = output_dir / "alb_access.log"
    alb_file.write_text(alb_log)
    print(f"   ✅ {alb_file} ({len(alb_log)} bytes)")
    
    # 3. VPC Flow 로그
    print("📦 VPC Flow 로그 생성 중...")
    vpc_log = generate_vpc_flow_logs(100)
    vpc_file = output_dir / "vpc_flow.log"
    vpc_file.write_text(vpc_log)
    print(f"   ✅ {vpc_file} ({len(vpc_log)} bytes)")
    
    # 4. CloudTrail 로그
    print("📦 CloudTrail 로그 생성 중...")
    cloudtrail_log = generate_cloudtrail_logs(50)
    cloudtrail_file = output_dir / "cloudtrail_events.json"
    cloudtrail_file.write_text(cloudtrail_log)
    print(f"   ✅ {cloudtrail_file} ({len(cloudtrail_log)} bytes)")
    
    print()
    print("=" * 60)
    print("✨ 로그 생성 완료!")
    print("=" * 60)
    print()
    print(f"📁 생성된 파일 위치: {output_dir.absolute()}")
    print()
    print("📤 S3 업로드 명령어:")
    print(f"   aws s3 cp {output_dir}/ s3://YOUR-BUCKET/logs/ --recursive")
    print()
    print("또는 개별 업로드:")
    print(f"   aws s3 cp {cloudfront_file} s3://YOUR-BUCKET/cloudfront-logs/")
    print(f"   aws s3 cp {alb_file} s3://YOUR-BUCKET/alb-logs/")
    print(f"   aws s3 cp {vpc_file} s3://YOUR-BUCKET/vpc-flow-logs/")
    print(f"   aws s3 cp {cloudtrail_file} s3://YOUR-BUCKET/cloudtrail-logs/")


if __name__ == "__main__":
    main()
