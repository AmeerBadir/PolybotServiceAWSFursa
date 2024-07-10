variable "ami_id" {
   description = "AMI"
   type        = string
}
variable "vpc_id" {
  description = "VPC"
  type        = string
}
variable "sqs_queue_url" {
  description = "SQS queue"
  type        = string
}

variable "bucket_name" {
  description = "S3 bucket"
  type        = string
}
variable "dynamo_DB" {
  description = "db"
  type = string

}
variable "public_subnets" {
  description = "subnet ids"
  type        = list(string)
}
variable "polybot_loadbalancer_dns" {
  description = "lb dns"
  type = string

}
variable "role_name" {
  description = "role "
  type = string
}
variable "region_name" {
  description = "region name"
  type = string
}
variable "assign_public_ip" {
  description = ""
  type        = bool
  default     = true
}
variable "key_name" {
  description = ""
  type = string
}