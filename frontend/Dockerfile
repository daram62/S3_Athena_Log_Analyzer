# Frontend Dockerfile
FROM node:18-alpine AS build

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .

# 배포 환경에서는 상대 경로 사용 (ALB가 라우팅)
ENV REACT_APP_API_URL=/api/v1

RUN npm run build

# Nginx로 정적 파일 서빙
FROM nginx:alpine

COPY --from=build /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
