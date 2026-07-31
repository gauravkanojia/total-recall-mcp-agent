variable "name_prefix" {
  type = string
}

variable "tags" {
  type = map(string)
}

data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

output "vpc_id" {
  value = data.aws_vpc.default.id
}

output "public_subnet_ids" {
  value = data.aws_subnets.default.ids
}
