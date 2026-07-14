#!/usr/bin/env bash
# Build, push, and deploy Total Recall MCP to AWS ECS Fargate.
#
# Prerequisites:
#   - AWS CLI configured (aws sts get-caller-identity)
#   - Docker (or podman with docker-compatible CLI)
#   - Terraform >= 1.5
#   - terraform/environments/dev/terraform.tfvars filled in (database_url)
#
# Usage:
#   ./scripts/deploy_aws.sh
#   AWS_REGION=us-west-2 IMAGE_TAG=v1 ./scripts/deploy_aws.sh
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TF_DIR="${ROOT_DIR}/terraform/environments/dev"

AWS_REGION="${AWS_REGION:-us-east-1}"
PROJECT_NAME="${PROJECT_NAME:-total-recall-mcp-agent}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
ECR_REPO="${ECR_REPO:-${PROJECT_NAME}}"

if ! command -v aws >/dev/null 2>&1; then
  echo "aws CLI not found." >&2
  exit 1
fi

if ! command -v terraform >/dev/null 2>&1; then
  echo "terraform not found." >&2
  exit 1
fi

if [[ ! -f "${TF_DIR}/terraform.tfvars" ]]; then
  echo "Missing ${TF_DIR}/terraform.tfvars" >&2
  echo "Copy terraform.tfvars.example and fill in database_url, etc." >&2
  exit 1
fi

ACCOUNT_ID="$(aws sts get-caller-identity --query Account --output text)"
IMAGE_URI="${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO}:${IMAGE_TAG}"

echo "=== Ensure ECR repository: ${ECR_REPO} ==="
if ! aws ecr describe-repositories --repository-names "${ECR_REPO}" --region "${AWS_REGION}" >/dev/null 2>&1; then
  aws ecr create-repository --repository-name "${ECR_REPO}" --region "${AWS_REGION}" >/dev/null
fi

echo "=== Docker login to ECR ==="
aws ecr get-login-password --region "${AWS_REGION}" \
  | docker login --username AWS --password-stdin "${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

echo "=== Build image ==="
docker build -t "${PROJECT_NAME}:${IMAGE_TAG}" "${ROOT_DIR}"

echo "=== Tag and push ${IMAGE_URI} ==="
docker tag "${PROJECT_NAME}:${IMAGE_TAG}" "${IMAGE_URI}"
docker push "${IMAGE_URI}"

echo "=== Terraform apply ==="
terraform -chdir="${TF_DIR}" init -input=false
terraform -chdir="${TF_DIR}" apply -auto-approve \
  -var="aws_region=${AWS_REGION}" \
  -var="container_image=${IMAGE_URI}"

echo
echo "=== Deployment outputs ==="
terraform -chdir="${TF_DIR}" output
