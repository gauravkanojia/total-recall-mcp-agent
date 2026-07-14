variable "name_prefix" {
  type = string
}

variable "tags" {
  type = map(string)
}

variable "database_url" {
  type      = string
  sensitive = true
}

resource "aws_secretsmanager_secret" "database_url" {
  name = "${var.name_prefix}-database-url"
  tags = var.tags
}

resource "aws_secretsmanager_secret_version" "database_url" {
  secret_id     = aws_secretsmanager_secret.database_url.id
  secret_string = var.database_url
}

output "database_secret_arn" {
  value = aws_secretsmanager_secret.database_url.arn
}
