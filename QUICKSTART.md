# 빠른 시작 가이드

Gen-AI Log Analyzer를 5분 안에 시작하는 방법

---

## 📋 사전 준비

### 필수 소프트웨어
- Python 3.9 이상
- Node.js 14 이상
- pip (Python 패키지 관리자)
- npm (Node.js 패키지 관리자)

### AWS 요구사항
- AWS 계정
- AWS CLI 설치 및 설정
- 다음 AWS 서비스 권한:
  - S3 (읽기/쓰기)
  - Athena (쿼리 실행)
  - Glue Catalog (테이블 관리)
  - Bedrock (AI 서비스, 선택사항)

---

## 🚀 설치 및 실행

### 1단계: 저장소 클론

```bash
git clone <repository-url>
cd GenAI_Project
```

### 2단계: Python 환경 설정

```bash
# 가상 환경 생성 (권장)
python -m venv venv

# 가상 환경 활성화
# macOS/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
```

### 3단계: 환경 변수 설정

```bash
# .env 파일 생성
cp .env.example .env

# .env 파일 편집
nano .env  # 또는 원하는 에디터 사용
```

**.env 파일 필수 설정:**
```bash
# AWS 설정
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here

# Athena 설정
ATHENA_OUTPUT_BUCKET=s3://your-athena-results-bucket/
ATHENA_DATABASE=log_analytics

# API 설정
API_HOST=0.0.0.0
API_PORT=8000

# 로깅
LOG_LEVEL=INFO
```

### 4단계: 프론트엔드 설정

```bash
cd frontend
npm install
cd ..
```

### 5단계: 서버 실행

**터미널 1 - 백엔드:**
```bash
# 개발 모드로 실행
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

# 또는 Makefile 사용
make run
```

**터미널 2 - 프론트엔드:**
```bash
cd frontend
npm start
```

### 6단계: 접속

브라우저에서 다음 URL 접속:
- **프론트엔드**: http://localhost:3000
- **API 문서**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## 🎯 첫 번째 사용

### Part 1: S3 → Athena 테이블 생성

1. **S3 버킷 선택**
   - 웹 인터페이스에서 "S3 Bucket" 입력
   - 예: `my-application-logs`

2. **로그 분석**
   - "Analyze Logs" 버튼 클릭
   - 시스템이 자동으로 로그 타입 감지
   - 스키마 자동 추론

3. **테이블 생성**
   - "Create Table" 버튼 클릭
   - Athena에 테이블 자동 생성
   - 완료! 이제 SQL로 쿼리 가능

### Part 2: 자연어 쿼리 (개발 중)

1. **질문 입력**
   - 예: "어제 가장 많이 접근된 파일 10개는?"

2. **자동 실행**
   - AI가 SQL 자동 생성
   - Athena에서 즉시 실행
   - 결과 표시

---

## 🧪 테스트

### 설치 확인

```bash
# Python 테스트 실행
pytest

# 커버리지 포함
pytest --cov=src

# 특정 테스트만
pytest tests/test_log_detection_engine.py -v
```

### API 테스트

```bash
# 헬스 체크
curl http://localhost:8000/health

# S3 버킷 목록 조회
curl http://localhost:8000/buckets

# 로그 분석 테스트
curl -X POST http://localhost:8000/analyze-logs \
  -H "Content-Type: application/json" \
  -d '{"bucket_name": "my-logs-bucket", "prefix": "logs/"}'
```

---

## 🔧 문제 해결

### 일반적인 문제

#### 1. AWS 자격 증명 오류
```
Error: Unable to locate credentials
```

**해결 방법:**
```bash
# AWS CLI 설정
aws configure

# 또는 .env 파일에 직접 설정
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
```

#### 2. Athena 출력 버킷 오류
```
Error: Query results location not set
```

**해결 방법:**
```bash
# .env 파일에 Athena 출력 버킷 설정
ATHENA_OUTPUT_BUCKET=s3://your-athena-results-bucket/

# S3 버킷이 없다면 생성
aws s3 mb s3://your-athena-results-bucket
```

#### 3. 포트 충돌
```
Error: Address already in use
```

**해결 방법:**
```bash
# 다른 포트 사용
uvicorn src.api.main:app --reload --port 8001

# 또는 기존 프로세스 종료
lsof -ti:8000 | xargs kill -9
```

#### 4. 프론트엔드 빌드 오류
```
Error: Cannot find module
```

**해결 방법:**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

---

## 📚 다음 단계

### 추가 설정

1. **IAM 권한 최적화**
   - [IAM_SETUP_GUIDE.md](IAM_SETUP_GUIDE.md) 참조
   - 최소 권한 원칙 적용

2. **로그 타입 추가**
   - 커스텀 로그 포맷 정의
   - DDL 템플릿 커스터마이징

3. **성능 최적화**
   - 파티션 전략 조정
   - 쿼리 최적화

### 학습 자료

- [API 문서](.kiro/steering/api.md)
- [기술 스택](.kiro/steering/tech.md)
- [프로젝트 구조](.kiro/steering/structure.md)
- [구현 가이드라인](.kiro/steering/implementation.md)

---

## 💡 팁

### 개발 효율성

```bash
# Makefile 명령어 활용
make install-dev  # 개발 의존성 설치
make test         # 테스트 실행
make format       # 코드 포맷팅
make lint         # 린팅
make clean        # 임시 파일 정리
```

### 디버깅

```bash
# 상세 로그 출력
LOG_LEVEL=DEBUG uvicorn src.api.main:app --reload

# Python 디버거 사용
import pdb; pdb.set_trace()
```

### 프로덕션 배포

```bash
# 프로덕션 모드로 실행
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --workers 4

# 프론트엔드 빌드
cd frontend
npm run build
```

---

## 🆘 도움말

문제가 해결되지 않으면:

1. [GitHub Issues](https://github.com/your-repo/issues) 확인
2. 새로운 이슈 생성
3. 다음 정보 포함:
   - 오류 메시지
   - 실행 환경 (OS, Python 버전)
   - 재현 단계

---

## ✅ 체크리스트

설치가 완료되었는지 확인:

- [ ] Python 3.9+ 설치됨
- [ ] Node.js 14+ 설치됨
- [ ] AWS CLI 설정됨
- [ ] .env 파일 생성 및 설정됨
- [ ] Python 의존성 설치됨
- [ ] 프론트엔드 의존성 설치됨
- [ ] 백엔드 서버 실행됨 (http://localhost:8000)
- [ ] 프론트엔드 실행됨 (http://localhost:3000)
- [ ] API 문서 접근 가능 (http://localhost:8000/docs)
- [ ] 테스트 통과

모든 항목이 체크되었다면 준비 완료! 🎉
