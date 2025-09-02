variable "project_id" {
  description = "Project ID"
  type        = string
}

variable "project_region" {
  description = "Project Region"
  type        = string
}

variable "credentials" {
  description = "Google Service Account Credentials in JSON"
  type        = string
  sensitive   = true
}

variable "service_account_id" {
  description = "Account ID of Service Account"
  type        = string
}