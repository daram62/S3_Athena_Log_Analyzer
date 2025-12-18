# S3 LogLift Platform Makefile

.PHONY: help install install-dev test test-cov lint format type-check clean run

# 기본 타겟
help:
	@echo "사용 가능한 명령어:"
	@echo "  install      - 프로덕션 의존성 설치"
	@echo "  install-dev  - 개발 의존성 포함 설치"
	@echo "  test         - 테스트 실행"
	@echo "  test-cov     - 커버리지 포함 테스트 실행"
	@echo "  lint         - 코드 린팅 (flake8)"
	@echo "  format       - 코드 포맷팅 (black, isort)"
	@echo "  type-check   - 타입 체킹 (mypy)"
	@echo "  clean        - 임시 파일 정리"
	@echo "  run          - 개발 서버 실행"

# 의존성 설치
install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"

# 테스트
test:
	pytest

test-cov:
	pytest --cov=src --cov-report=html --cov-report=term

# 코드 품질
lint:
	flake8 src tests

format:
	black src tests
	isort src tests

type-check:
	mypy src

# 정리
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/
	rm -rf dist/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/

# 개발 서버 실행
run:
	uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

# 전체 품질 검사
check: lint type-check test

# Docker 관련 (향후 추가 예정)
docker-build:
	@echo "Docker 빌드는 향후 구현 예정"

docker-run:
	@echo "Docker 실행은 향후 구현 예정"