#!/usr/bin/env bash
# Build, push, and manage Total Recall MCP on AWS ECS Fargate with Terraform.
#
# Prerequisites:
#   - AWS CLI configured (aws sts get-caller-identity)
#   - Docker (plan/apply only, unless --skip-build)
#   - Terraform >= 1.5
#   - terraform/environments/dev/terraform.tfvars filled in (database_url)
#
# Usage:
#   ./scripts/deploy_aws.sh plan
#   ./scripts/deploy_aws.sh apply
#   ./scripts/deploy_aws.sh destroy
#   ./scripts/deploy_aws.sh apply --auto-approve
#   ./scripts/deploy_aws.sh plan --skip-build
#   AWS_REGION=us-west-2 IMAGE_TAG=v1 ./scripts/deploy_aws.sh apply
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TF_DIR="${ROOT_DIR}/terraform/environments/dev"

AWS_REGION="${AWS_REGION:-us-east-1}"
PROJECT_NAME="${PROJECT_NAME:-total-recall-mcp-agent}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
ECR_REPO="${ECR_REPO:-${PROJECT_NAME}}"

COMMAND="plan"
SKIP_BUILD=0
AUTO_APPROVE=0

usage() {
  cat <<EOF
Usage: ./scripts/deploy_aws.sh [command] [options]

Commands:
  plan      Build/push container image (unless --skip-build) and run terraform plan
  apply     Build/push container image (unless --skip-build) and run terraform apply
  destroy   Tear down AWS resources with terraform destroy

Options:
  --skip-build     Skip ECR login, Docker build, and image push (use container_image from terraform.tfvars)
  --auto-approve   Skip interactive approval for apply or destroy
  -h, --help       Show this help

Environment variables:
  AWS_REGION, PROJECT_NAME, IMAGE_TAG, ECR_REPO

Examples:
  ./scripts/deploy_aws.sh plan
  ./scripts/deploy_aws.sh apply --auto-approve
  ./scripts/deploy_aws.sh destroy
  ./scripts/deploy_aws.sh plan --skip-build
EOF
}

parse_args() {
  if [[ $# -gt 0 ]]; then
    case "$1" in
      plan|apply|destroy)
        COMMAND="$1"
        shift
        ;;
      -h|--help)
        usage
        exit 0
        ;;
    esac
  fi

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --skip-build)
        SKIP_BUILD=1
        shift
        ;;
      --auto-approve)
        AUTO_APPROVE=1
        shift
        ;;
      -h|--help)
        usage
        exit 0
        ;;
      *)
        echo "Unknown argument: $1" >&2
        usage >&2
        exit 1
        ;;
    esac
  done
}

require_aws_cli() {
  if ! command -v aws >/dev/null 2>&1; then
    echo "aws CLI not found." >&2
    exit 1
  fi
}

require_terraform() {
  if ! command -v terraform >/dev/null 2>&1; then
    echo "terraform not found." >&2
    exit 1
  fi
}

require_docker() {
  if ! command -v docker >/dev/null 2>&1; then
    echo "docker not found (required unless --skip-build)." >&2
    exit 1
  fi
}

require_tfvars() {
  if [[ ! -f "${TF_DIR}/terraform.tfvars" ]]; then
    echo "Missing ${TF_DIR}/terraform.tfvars" >&2
    echo "Copy terraform.tfvars.example and fill in database_url, etc." >&2
    exit 1
  fi
}

terraform_init() {
  echo "=== Terraform init ==="
  terraform -chdir="${TF_DIR}" init -input=false
}

build_and_push_image() {
  local account_id image_uri

  require_docker

  account_id="$(aws sts get-caller-identity --query Account --output text)"
  image_uri="${account_id}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO}:${IMAGE_TAG}"

  echo "=== Ensure ECR repository: ${ECR_REPO} ==="
  if ! aws ecr describe-repositories --repository-names "${ECR_REPO}" --region "${AWS_REGION}" >/dev/null 2>&1; then
    aws ecr create-repository --repository-name "${ECR_REPO}" --region "${AWS_REGION}" >/dev/null
  fi

  echo "=== Docker login to ECR ==="
  aws ecr get-login-password --region "${AWS_REGION}" \
    | docker login --username AWS --password-stdin "${account_id}.dkr.ecr.${AWS_REGION}.amazonaws.com"

  echo "=== Build image ==="
  docker build -t "${PROJECT_NAME}:${IMAGE_TAG}" "${ROOT_DIR}"

  echo "=== Tag and push ${image_uri} ==="
  docker tag "${PROJECT_NAME}:${IMAGE_TAG}" "${image_uri}"
  docker push "${image_uri}"

  CONTAINER_IMAGE_VAR=(-var="container_image=${image_uri}")
}

terraform_plan() {
  echo "=== Terraform plan ==="
  terraform -chdir="${TF_DIR}" plan \
    -var="aws_region=${AWS_REGION}" \
    "${CONTAINER_IMAGE_VAR[@]}"
}

terraform_apply() {
  echo "=== Terraform apply ==="
  local -a apply_args=(-var="aws_region=${AWS_REGION}")

  if [[ ${#CONTAINER_IMAGE_VAR[@]} -gt 0 ]]; then
    apply_args+=("${CONTAINER_IMAGE_VAR[@]}")
  fi

  if [[ "${AUTO_APPROVE}" -eq 1 ]]; then
    apply_args+=(-auto-approve)
  fi

  terraform -chdir="${TF_DIR}" apply "${apply_args[@]}"

  echo
  echo "=== Deployment outputs ==="
  terraform -chdir="${TF_DIR}" output
}

terraform_destroy() {
  echo "=== Terraform destroy ==="
  local -a destroy_args=()

  if [[ "${AUTO_APPROVE}" -eq 1 ]]; then
    destroy_args+=(-auto-approve)
  fi

  terraform -chdir="${TF_DIR}" destroy "${destroy_args[@]}"
}

main() {
  parse_args "$@"

  require_aws_cli
  require_terraform
  require_tfvars

  CONTAINER_IMAGE_VAR=()

  case "${COMMAND}" in
    plan|apply)
      if [[ "${SKIP_BUILD}" -eq 1 ]]; then
        echo "=== Skipping image build; using container_image from terraform.tfvars ==="
      else
        build_and_push_image
      fi
      terraform_init
      if [[ "${COMMAND}" == "plan" ]]; then
        terraform_plan
      else
        # Default apply behavior matches the original script (non-interactive).
        if [[ "${AUTO_APPROVE}" -eq 0 ]]; then
          AUTO_APPROVE=1
        fi
        terraform_apply
      fi
      ;;
    destroy)
      terraform_init
      terraform_destroy
      ;;
    *)
      echo "Unknown command: ${COMMAND}" >&2
      usage >&2
      exit 1
      ;;
  esac
}

main "$@"
