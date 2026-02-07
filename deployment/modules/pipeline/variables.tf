variable "region" {
    description = "The region to deploy resources in"
    type        = string 
}

variable "project_id" {
    description = "The GCP project ID"
    type        = string 
}

variable "bucket_name" {
  description = "The name of the GCS bucket to store function source"
  type        = string
}

variable "env_vars" {
  description = "Environment variables for the Cloud Function"
  type        = map(string)
  default     = {}
}

variable "service_account_id" {
  description = "Service Account ID for the Cloud Function"
  type        = string
}