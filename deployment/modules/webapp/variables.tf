variable "service_account_id" {
  description = "Account ID of Service Account"
  type        = string
}

variable "project_id" {
  description = "Project ID"
  type = string
}

variable "project_region" {
  description = "Project Region"
  type = string
}

variable "service_name" {
  description = "Cloud Run Service Name"
  type = string
}

variable "docker_repo_name" {
  description = "Name of Artifact Repository (For storing docker images)"
  type = string
}

variable "app_path" {
  description = "Folder path of application"
  type = string
}