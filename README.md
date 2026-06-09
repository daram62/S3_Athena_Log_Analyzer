# S3 Athena Log Analyzer

[ENG](#english) | [KOR](#korean)

<a id="english"></a>

S3 Athena Log Analyzer is an AWS log analysis platform that detects log data in S3, 
generates Athena tables automatically, and turns natural-language questions into SQL for instant analysis.

### Video
https://youtu.be/z_0XiGukUCM?si=vdbE647_QZVkv40n

### What it does

- Automatically detects log formats in an S3 bucket
- Generates Athena DDL and tables for supported log types
- Converts natural-language questions into SQL with Bedrock Claude
- Executes queries in Athena and shows the results
- Provides query history, suggested questions, and log dashboards

### Supported log types

- S3 Access Logs
- CloudFront Logs
- ALB Logs
- VPC Flow Logs
- CloudTrail Logs

### Tech stack

- Backend: Python, FastAPI, Pydantic, boto3
- Frontend: React, TypeScript
- AWS: S3, Athena, Glue, Bedrock
- Testing: pytest, pytest-cov

### Quick start

```bash
pip install -r requirements.txt
cd frontend
npm install
cd ..
make run
```

Environment setup:

```bash
copy .env.example .env
```

Make sure these values are configured in `.env`:

- `AWS_REGION`
- `AWS_PROFILE`
- `AWS_ATHENA_OUTPUT_LOCATION`
- `AWS_BEDROCK_MODEL_ID`
- `API_HOST`
- `API_PORT`

In a second terminal:

```bash
cd frontend
npm start
```

Open the app at http://localhost:3000 and the API docs at http://localhost:8000/docs.


### Project structure

```text
S3_Athena_Log_Analyzer/
├── src/                # FastAPI backend
├── frontend/           # React frontend
├── tests/              # Automated tests
├── generated_ddls/     # Example/generated DDLs
└── generate_sample_logs.py
```

### API endpoints

- `GET /health`
- `GET /api/v1/buckets`
- `POST /api/v1/analyze-logs`
- `POST /api/v1/tables/create`
- `POST /api/v1/natural-language/query`

### Testing

```bash
pytest
```
---

<a id="korean"></a>

S3 Athena Log Analyzer는 S3에 저장된 AWS 로그를 자동으로 감지하고 Athena 테이블을 생성한 뒤, 자연어 질문을 SQL로 변환해 바로 분석할 수 있게 해주는 플랫폼입니다.

### 시연 영상

https://youtu.be/z_0XiGukUCM?si=vdbE647_QZVkv40n

### 주요 기능

- S3 버킷의 로그 형식을 자동 감지
- 지원 로그 타입별 Athena DDL과 테이블 자동 생성
- Bedrock Claude 기반 자연어 → SQL 변환
- Athena 쿼리 실행 및 결과 확인
- 쿼리 히스토리, 추천 질문, 로그 대시보드 제공

### 지원 로그 타입

- S3 Access Logs
- CloudFront Logs
- ALB Logs
- VPC Flow Logs
- CloudTrail Logs

### 기술 스택

- Backend: Python, FastAPI, Pydantic, boto3
- Frontend: React, TypeScript
- AWS: S3, Athena, Glue, Bedrock
- Testing: pytest, pytest-cov

### 빠른 시작

```bash
pip install -r requirements.txt
cd frontend
npm install
cd ..
make run
```

환경 설정:

```bash
copy .env.example .env
```

`.env`에서 다음 값을 설정하세요.

- `AWS_REGION`
- `AWS_PROFILE`
- `AWS_ATHENA_OUTPUT_LOCATION`
- `AWS_BEDROCK_MODEL_ID`
- `API_HOST`
- `API_PORT`

별도 터미널에서 프론트엔드를 실행합니다.

```bash
cd frontend
npm start
```

브라우저에서 http://localhost:3000 을 열고, API 문서는 http://localhost:8000/docs 에서 확인할 수 있습니다.


### 프로젝트 구조

```text
S3_Athena_Log_Analyzer/
├── src/                # FastAPI 백엔드
├── frontend/           # React 프론트엔드
├── tests/              # 자동화 테스트
├── generated_ddls/     # 예시/생성 DDL
└── generate_sample_logs.py
```

### API 주요 엔드포인트

- `GET /health`
- `GET /api/v1/buckets`
- `POST /api/v1/analyze-logs`
- `POST /api/v1/tables/create`
- `POST /api/v1/natural-language/query`

### 테스트

```bash
pytest
```
