#!/bin/bash
set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}🚀 Gen-AI Log Analyzer 배포 스크립트${NC}"
echo ""

# 변수 설정
AWS_REGION=${AWS_REGION:-ap-northeast-2}
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
APP_NAME="genai-log-analyzer"
ENV="prod"

ECR_BACKEND="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${APP_NAME}-${ENV}-backend"
ECR_FRONTEND="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${APP_NAME}-${ENV}-frontend"

echo -e "${YELLOW}📋 설정 정보${NC}"
echo "  AWS Region: ${AWS_REGION}"
echo "  AWS Account: ${AWS_ACCOUNT_ID}"
echo ""

# 0. terraform.tfvars 확인
if [ ! -f "terraform/terraform.tfvars" ]; then
  echo -e "${RED}❌ terraform/terraform.tfvars 파일이 없습니다.${NC}"
  echo -e "${YELLOW}terraform/terraform.tfvars.example을 복사하고 서비스 계정 credential을 입력하세요.${NC}"
  exit 1
fi

# 1. Terraform 인프라 배포
echo -e "${YELLOW}1️⃣ Terraform 인프라 배포${NC}"
cd terraform
terraform init
terraform apply -auto-approve
cd ..

# 2. ECR 로그인
echo -e "${YELLOW}2️⃣ ECR 로그인${NC}"
aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com

# 3. 백엔드 Docker 이미지 빌드 및 푸시
echo -e "${YELLOW}3️⃣ 백엔드 이미지 빌드 및 푸시${NC}"
docker build -t ${APP_NAME}-backend .
docker tag ${APP_NAME}-backend:latest ${ECR_BACKEND}:latest
docker push ${ECR_BACKEND}:latest

# 4. 프론트엔드 Docker 이미지 빌드 및 푸시
echo -e "${YELLOW}4️⃣ 프론트엔드 이미지 빌드 및 푸시${NC}"
cd frontend
docker build -t ${APP_NAME}-frontend .
docker tag ${APP_NAME}-frontend:latest ${ECR_FRONTEND}:latest
docker push ${ECR_FRONTEND}:latest
cd ..

# 5. ECS 서비스 업데이트
echo -e "${YELLOW}5️⃣ ECS 서비스 업데이트${NC}"
aws ecs update-service --cluster ${APP_NAME}-${ENV}-cluster --service ${APP_NAME}-${ENV}-backend --force-new-deployment --region ${AWS_REGION}
aws ecs update-service --cluster ${APP_NAME}-${ENV}-cluster --service ${APP_NAME}-${ENV}-frontend --force-new-deployment --region ${AWS_REGION}

# 6. 완료
echo ""
echo -e "${GREEN}✅ 배포 완료!${NC}"
echo ""
cd terraform
APP_URL=$(terraform output -raw app_url)
echo -e "🌐 접속 URL: ${GREEN}${APP_URL}${NC}"
echo ""
echo -e "${YELLOW}⏳ 서비스가 시작되는데 2-3분 정도 걸릴 수 있습니다.${NC}"
echo -e "${YELLOW}⏳ SSL 인증서 검증에 추가로 몇 분이 걸릴 수 있습니다.${NC}"
