terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

locals {
  name_prefix = "${var.project_name}-${var.environment}"
  tags = {
    Project     = var.project_name
    Environment = var.environment
  }
}

module "secrets" {
  source = "../../modules/secrets"

  name_prefix  = local.name_prefix
  tags         = local.tags
  database_url = var.database_url
}

module "iam" {
  source = "../../modules/iam"

  name_prefix = local.name_prefix
  tags        = local.tags
  secret_arns = [
    module.secrets.database_secret_arn,
  ]
}

module "network" {
  source = "../../modules/network"

  name_prefix = local.name_prefix
  tags        = local.tags
}

module "ecs" {
  source = "../../modules/ecs"

  name_prefix          = local.name_prefix
  tags                 = local.tags
  aws_region           = var.aws_region
  vpc_id               = module.network.vpc_id
  public_subnet_ids    = module.network.public_subnet_ids
  execution_role_arn   = module.iam.execution_role_arn
  task_role_arn        = module.iam.task_role_arn
  container_image      = var.container_image
  container_port       = var.container_port
  desired_count        = var.desired_count
  database_secret_arn  = module.secrets.database_secret_arn
  embedding_provider   = var.embedding_provider
  embedding_model_id   = var.embedding_model_id
  embedding_dimensions = var.embedding_dimensions
}

output "alb_dns_name" {
  description = "Public DNS name of the MCP agent load balancer."
  value       = module.ecs.alb_dns_name
}

output "health_check_url" {
  description = "ALB health check endpoint."
  value       = "http://${module.ecs.alb_dns_name}/health"
}

output "mcp_endpoint_url" {
  description = "Streamable HTTP MCP endpoint."
  value       = "http://${module.ecs.alb_dns_name}/mcp"
}
