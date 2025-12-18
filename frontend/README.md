# S3 LogLift Frontend

S3 LogLift 지능형 로그 분석 플랫폼의 프론트엔드 애플리케이션입니다.

## 🚀 주요 기능

- **다크/라이트 테마 지원**: 시스템 설정 자동 감지 및 수동 전환
- **반응형 디자인**: 모바일, 태블릿, 데스크톱 최적화
- **실시간 AWS 연결 상태**: SSO 로그인 상태 자동 확인
- **직관적인 3단계 워크플로우**: S3 선택 → 검증 → 테이블 생성
- **접근성 준수**: WCAG 2.1 AA 기준 준수

## 🛠️ 기술 스택

- **React 18** with TypeScript
- **CSS Variables** 기반 테마 시스템
- **Lucide React** 아이콘
- **Axios** HTTP 클라이언트

## 📦 설치 및 실행

### 1. 의존성 설치
```bash
cd frontend
npm install
```

### 2. 개발 서버 실행
```bash
npm start
```

브라우저에서 [http://localhost:3000](http://localhost:3000)으로 접속

### 3. 빌드
```bash
npm run build
```

## 🎨 테마 시스템

### CSS 변수 기반 테마
```css
:root[data-theme="dark"] {
  --primary-bg: #1a1a1a;
  --text-primary: #ffffff;
  --accent-primary: #ff6b6b;
  /* ... */
}
```

### 테마 전환
- **자동 감지**: 시스템 설정 (prefers-color-scheme) 자동 적용
- **수동 전환**: 헤더의 테마 토글 버튼
- **로컬 저장**: 사용자 선택 기억

## 🔧 컴포넌트 구조

```
src/
├── components/
│   ├── MainHeader.tsx          # 메인 헤더 (로고, 상태, 테마 토글)
│   ├── ThemeToggle.tsx         # 테마 전환 버튼
│   └── *.css                   # 컴포넌트별 스타일
├── contexts/
│   └── ThemeContext.tsx        # 테마 상태 관리
├── styles/
│   └── globals.css             # 글로벌 스타일 및 CSS 변수
└── App.tsx                     # 메인 애플리케이션
```

## 🎯 주요 기능 설명

### 1. 테마 시스템
- **3가지 모드**: Light, Dark, System
- **부드러운 전환**: 0.3초 애니메이션
- **시스템 연동**: OS 다크모드 자동 감지

### 2. AWS 연결 상태
- **실시간 확인**: 백엔드 API 연동
- **시각적 피드백**: 연결/미연결/확인중 상태 표시
- **가이드 제공**: 연결 실패 시 설정 도움말

### 3. 반응형 디자인
- **모바일 우선**: Mobile-first 접근법
- **브레이크포인트**: 480px, 768px, 1024px
- **유연한 레이아웃**: Grid 및 Flexbox 활용

## 🔗 백엔드 연동

프론트엔드는 다음 API 엔드포인트를 사용합니다:

```typescript
// AWS 상태 확인
GET /api/aws/status

// 버킷 목록 조회
GET /api/aws/buckets

// 로그 검증
POST /api/logs/verify

// 테이블 생성
POST /api/athena/create-database-table
```

## 🧪 테스트

```bash
npm test
```

## 📱 브라우저 지원

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## 🎨 디자인 시스템

### 색상 팔레트
- **Primary**: #ff6b6b (빨간색 계열)
- **Secondary**: #4ecdc4 (청록색 계열)
- **Success**: #00d4aa / #28a745
- **Warning**: #ffd93d / #ffc107
- **Error**: #ff6b6b / #dc3545

### 타이포그래피
- **제목**: 28px-32px, 700 weight
- **부제목**: 14px-16px, 400 weight
- **본문**: 14px-16px, 400 weight
- **버튼**: 14px-16px, 600 weight

### 간격 시스템
- **xs**: 4px
- **sm**: 8px
- **md**: 16px
- **lg**: 24px
- **xl**: 32px
- **2xl**: 48px

## 🚀 배포

### Vercel 배포
```bash
npm run build
# Vercel CLI 또는 GitHub 연동 사용
```

### Docker 배포
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "start"]
```

## 📄 라이선스

MIT License