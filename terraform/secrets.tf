# 서비스 계정 Credential을 SSM Parameter Store에 저장
# 배포 전에 terraform.tfvars에 값 설정 필요

variable "service_account_access_key" {
  description = "서비스 계정 AWS Access Key ID"
  type        = string
  sensitive   = true
}

variable "service_account_secret_key" {
  description = "서비스 계정 AWS Secret Access Key"
  type        = string
  sensitive   = true
}

resource "aws_ssm_parameter" "aws_access_key" {
  name        = "/${local.name_prefix}/aws-access-key-id"
  description = "서비스 계정 AWS Access Key ID"
  type        = "SecureString"
  value       = var.service_account_access_key

  tags = {
    Name = "${local.name_prefix}-aws-access-key"
  }
}

resource "aws_ssm_parameter" "aws_secret_key" {
  name        = "/${local.name_prefix}/aws-secret-access-key"
  description = "서비스 계정 AWS Secret Access Key"
  type        = "SecureString"
  value       = var.service_account_secret_key

  tags = {
    Name = "${local.name_prefix}-aws-secret-key"
  }
}
