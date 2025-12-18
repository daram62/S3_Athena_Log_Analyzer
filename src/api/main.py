"""FastAPI 메인 애플리케이션 - Gen-AI Log Analyzer"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import logging

from ..config import settings
from .s3_analysis_api import router as s3_router
from .query_templates_api import router as query_templates_router
from .query_execution_api import router as query_execution_router
from .table_management_api import router as table_router
from .natural_language_api import router as natural_language_router

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI 앱 생성
app = FastAPI(
    title="Gen-AI Log Analyzer",
    description="AWS 로그 분석 자동화 플랫폼 - S3 → Athena 자동 셋업",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.api.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 라우터 등록
app.include_router(s3_router)
app.include_router(query_templates_router)
app.include_router(query_execution_router)
app.include_router(table_router)
app.include_router(natural_language_router)


@app.get("/", response_class=HTMLResponse)
async def root():
    """메인 페이지"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Gen-AI Log Analyzer</title>
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                max-width: 800px;
                margin: 50px auto;
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }
            .container {
                background: rgba(255, 255, 255, 0.1);
                backdrop-filter: blur(10px);
                border-radius: 20px;
                padding: 40px;
                box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
            }
            h1 {
                font-size: 2.5em;
                margin-bottom: 10px;
            }
            .subtitle {
                font-size: 1.2em;
                opacity: 0.9;
                margin-bottom: 30px;
            }
            .features {
                margin: 30px 0;
            }
            .feature {
                background: rgba(255, 255, 255, 0.1);
                padding: 15px;
                margin: 10px 0;
                border-radius: 10px;
                border-left: 4px solid #4CAF50;
            }
            .links {
                margin-top: 30px;
            }
            a {
                display: inline-block;
                background: white;
                color: #667eea;
                padding: 12px 24px;
                margin: 5px;
                border-radius: 8px;
                text-decoration: none;
                font-weight: bold;
                transition: transform 0.2s;
            }
            a:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(0,0,0,0.2);
            }
            .stats {
                display: flex;
                justify-content: space-around;
                margin: 30px 0;
            }
            .stat {
                text-align: center;
            }
            .stat-number {
                font-size: 2em;
                font-weight: bold;
            }
            .stat-label {
                opacity: 0.8;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 Gen-AI Log Analyzer</h1>
            <div class="subtitle">AWS 로그 분석 자동화 플랫폼</div>
            
            <div class="stats">
                <div class="stat">
                    <div class="stat-number">5</div>
                    <div class="stat-label">지원 로그 타입</div>
                </div>
                <div class="stat">
                    <div class="stat-number">109</div>
                    <div class="stat-label">총 필드 수</div>
                </div>
                <div class="stat">
                    <div class="stat-number">70%</div>
                    <div class="stat-label">시간 단축</div>
                </div>
            </div>
            
            <div class="features">
                <div class="feature">
                    <strong>✨ S3 → Athena 자동 셋업</strong><br>
                    S3 버킷 선택 → 로그 타입 자동 감지 → Athena 테이블 자동 생성 (30초)
                </div>
                <div class="feature">
                    <strong>🤖 자연어 → SQL 자동 변환 (NEW!)</strong><br>
                    "지난주 에러가 가장 많았던 날은?" → AI가 SQL 생성 및 실행
                </div>
                <div class="feature">
                    <strong>📊 5가지 로그 타입 지원</strong><br>
                    S3 Access, CloudFront, ALB, VPC Flow, CloudTrail
                </div>
                <div class="feature">
                    <strong>⚡ 파티션 프로젝션 최적화</strong><br>
                    빠른 쿼리 성능을 위한 자동 파티션 설정
                </div>
            </div>
            
            <div class="links">
                <a href="/docs">📖 API 문서</a>
                <a href="/redoc">📚 ReDoc</a>
                <a href="http://localhost:3000" target="_blank">🎨 프론트엔드</a>
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@app.get("/health")
async def health_check():
    """헬스 체크"""
    return {
        "status": "healthy",
        "service": "Gen-AI Log Analyzer",
        "version": "1.0.0"
    }


@app.get("/info")
async def info():
    """서비스 정보"""
    return {
        "service": "Gen-AI Log Analyzer",
        "version": "1.0.0",
        "description": "AWS 로그 분석 자동화 플랫폼",
        "features": [
            "S3 → Athena 자동 셋업",
            "자연어 → SQL 자동 변환 (Bedrock Claude) 🆕",
            "5가지 로그 타입 지원 (S3, CloudFront, ALB, VPC Flow, CloudTrail)",
            "자동 로그 타입 감지",
            "DDL 자동 생성",
            "파티션 프로젝션 최적화",
            "쿼리 템플릿 제공",
            "쿼리 히스토리 및 통계 🆕",
            "로그 타입별 추천 질문 (40개+) 🆕"
        ],
        "supported_log_types": [
            {"type": "s3_access", "fields": 26, "name": "S3 Access Logs"},
            {"type": "cloudfront", "fields": 24, "name": "CloudFront Logs"},
            {"type": "alb", "fields": 29, "name": "ALB Logs"},
            {"type": "vpc_flow", "fields": 14, "name": "VPC Flow Logs"},
            {"type": "cloudtrail", "fields": 16, "name": "CloudTrail Logs"}
        ],
        "endpoints": {
            "docs": "/docs",
            "redoc": "/redoc",
            "health": "/health",
            "buckets": "/api/v1/buckets",
            "analyze": "/api/v1/analyze-logs",
            "create_table": "/api/v1/create-table",
            "query_templates": "/api/v1/query-templates",
            "natural_language": "/api/v1/natural-language/query",
            "suggestions": "/api/v1/natural-language/suggestions/{log_type}",
            "query_history": "/api/v1/natural-language/history"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
