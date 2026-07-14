variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "project_name" {
  type    = string
  default = "total-recall-mcp-agent"
}

variable "environment" {
  type    = string
  default = "dev"
}

variable "container_image" {
  description = "ECR image URI for the MCP agent container."
  type        = string
}

variable "container_port" {
  type    = number
  default = 8080
}

variable "desired_count" {
  type    = number
  default = 1
}

variable "database_url" {
  description = "CockroachDB connection string (prefer CockroachDB Cloud in production)."
  type        = string
  sensitive   = true
}

variable "embedding_provider" {
  type    = string
  default = "bedrock"
}

variable "embedding_model_id" {
  type    = string
  default = "amazon.titan-embed-text-v2:0"
}

variable "embedding_dimensions" {
  type    = number
  default = 1024
}
