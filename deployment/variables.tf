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

variable "model_service_name" {
  description = "Cloud Run Service Name"
  type        = string
}

variable "web_service_name" {
  description = "Cloud Run Service Name"
  type        = string
}

variable "docker_repo_name" {
  description = "Name of Artifact Repository (For storing docker images)"
  type        = string
}

variable "vpc_name" {
    type = string
}

variable "use_image" {
  type = bool 
  default = false
}