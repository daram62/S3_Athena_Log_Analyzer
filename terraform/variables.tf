variable "aws_region" {
  description = "AWS 리전"
  default     = "ap-northeast-2"
}

variable "app_name" {
  description = "애플리케이션 이름"
  default     = "genai-log-analyzer"
}

variable "environment" {
  description = "환경"
  default     = "prod"
}

variable "domain_name" {
  description = "메인 도메인"
  default     = "ludiakim.people.aws.dev"
}

variable "subdomain" {
  description = "서브도메인"
  default     = "loglift"
}

locals {
  name_prefix = "log-analyzer"  # 짧은 이름으로 32자 제한 준수
  full_domain = "${var.subdomain}.${var.domain_name}"
}
