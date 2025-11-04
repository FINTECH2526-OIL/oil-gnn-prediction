variable "service_account_id" {
  description = "Account ID of Service Account"
  type        = string
}

variable "use_service_account_for_auth" {
  description = "Use Service Account for Authentication"
  type = bool
  default = false
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

variable "service_env_vars" {
  default = []
  description = "Cloud Run Service's Env Variables"
  type = list(
    object(
      {
        name = string
        value = string
      }
    )
  )
}

variable "exposed_port" {
  default = 8080
  description = "Exposed Service Port on Container"
  type = number
}
  

# variable "app_path" {
#   description = "Folder path of application"
#   type = string
# }

variable "use_image" {
  type = bool
  default = false
}