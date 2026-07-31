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
