# Gen-AI Log Analyzer 🚀

생성형 AI를 활용한 AWS 로그 분석 자동화 플랫폼

AWS Support 엔지니어들의 로그 분석 시간을 단축하는 2가지 핵심 기능을 제공합니다.

## 🎯 핵심 기능

### 1️⃣ S3 → Athena 자동 셋업
S3 버킷의 로그를 Athena에서 바로 쿼리할 수 있도록 자동 설정

```
S3 버킷 선택 → 로그 타입 자동 감지 → Athena 테이블 자동 생성 (30초)
```

- ✅ 복잡한 DDL 작성 불필요
- ✅ 로그 타입 자동 감지 (S3, CloudFront, ALB, VPC Flow)
- ✅ 파티션 자동 최적화

### 2️⃣ 자연어 → SQL 자동 변환
자연어 질문을 SQL로 변환하여 Athena에서 즉시 실행

```
"지난주 에러가 가장 많았던 날은?" → SQL 쿼리 자동 생성 → 결과 표시
```

- ✅ SQL 몰라도 자연어로 질문
- ✅ AI가 SQL 쿼리 자동 생성 (Bedrock Claude)
- ✅ 로그 타입별 대시보드 제공

## 🚀 빠른 시작

### 1. 설치

```bash
# Python 의존성 설치
pip install -r requirements.txt

# 프론트엔드 의존성 설치
cd frontend && npm install && cd ..
```

### 2. 환경 설정

```bash
cp .env.example .env
# .env 파일에서 AWS 자격 증명 설정
```

### 3. 실행

```bash
# 백엔드 (터미널 1)
make run

# 프론트엔드 (터미널 2)
cd frontend && npm start
```

### 4. 접속

브라우저에서 `http://localhost:3000` 접속

## 📊 지원 로그 타입

| 로그 타입 | 상태 | 설명 |
|---------|------|------|
| S3 Access Logs | ✅ | 표준 및 확장 형식 |
| CloudFront Logs | ✅ | 웹 배포 로그 |
| ALB Logs | ✅ | Application Load Balancer |
| VPC Flow Logs | ✅ | 네트워크 트래픽 |

## 🛠️ 기술 스택

- **Backend**: Python 3.9+, FastAPI, Pydantic
- **Frontend**: React, TypeScript
- **AWS**: S3, Athena, Glue, Bedrock (Claude)
- **Testing**: pytest (76%+ coverage)

## 📁 프로젝트 구조

```
GenAI_Project/
├── src/
│   ├── api/           # FastAPI 엔드포인트
│   ├── models/        # 데이터 모델
│   ├── services/      # 비즈니스 로직
│   └── config.py      # 설정
├── frontend/          # React 프론트엔드
├── tests/             # 테스트
├── sample_logs/       # 샘플 로그 파일
└── generated_ddls/    # 생성된 DDL 파일
```

## 📖 API 문서

서버 실행 후:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 🔐 AWS 권한

필요한 IAM 권한:
- S3: ListBucket, GetObject, PutObject
- Athena: StartQueryExecution, GetQueryResults
- Glue: GetDatabase, CreateTable, DeleteTable
- Bedrock: InvokeModel

## 📝 라이선스

MIT License
