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
  type    = bool
  default = false
}

variable "GCS_BUCKET_NAME" {
  description = "Name of GCS Bucket"
  type        = string
}
variable "GCS_PROCESSED_PATH" {
  description = "Path to processed data in GCS Bucket"
  type        = string
}
variable "GCS_MODELS_PATH" {
  description = "Path to trained models in GCS Bucket"
  type        = string
}
variable "MODEL_RUN_ID" {
  description = "ID of the model run to use for predictions"
  type        = string
}
variable "ALPHA_VANTAGE_API_KEY" {
  description = "API Key for Alpha Vantage"
  type        = string
}