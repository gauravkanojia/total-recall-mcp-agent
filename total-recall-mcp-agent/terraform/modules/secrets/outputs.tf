output "database_secret_arn" {
  value = aws_secretsmanager_secret.database_url.arn
}
