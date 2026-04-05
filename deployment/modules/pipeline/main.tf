########################
# Pub/Sub Topic
########################
resource "google_pubsub_topic" "daily_topic" {
  name = "daily-trigger-topic"
}


########################
# Cloud Storage Bucket
# (for function source)
########################
data "google_storage_bucket" "function_bucket" {
  name     = var.bucket_name
}

data "google_service_account" "service_account" {
  account_id = var.service_account_id
  project = var.project_id
}

########################
# Zip source from ../
########################
data "archive_file" "function_source" {
  type        = "zip"
  source_dir  = "${path.module}/../../../gnn-backend"
  output_path = "${path.module}/oil-pipeline-function.zip"
}

resource "google_storage_bucket_object" "source_zip" {
  name   = "oil-pipeline-function-${data.archive_file.function_source.output_md5}.zip"
  bucket = data.google_storage_bucket.function_bucket.name
  source = data.archive_file.function_source.output_path
}

########################
# Cloud Function (2nd gen)
########################
resource "google_cloudfunctions2_function" "function" {
  name     = "oil-data-pipeline"
  location = var.region

  build_config {
    service_account = "projects/${var.project_id}/serviceAccounts/${data.google_service_account.service_account.email}"
    runtime     = "python311"
    entry_point = "scheduled_daily_update" # must exist in ../main.py

    source {
      storage_source {
        bucket = var.bucket_name
        object = google_storage_bucket_object.source_zip.name
      }
    }
  }

  service_config {
    available_cpu = 4
    service_account_email = data.google_service_account.service_account.email
    max_instance_count = 1
    available_memory  = "8G"
    timeout_seconds   = 3600
    
    environment_variables = var.env_vars
  }

  event_trigger {
    trigger_region = var.region
    event_type     = "google.cloud.pubsub.topic.v1.messagePublished"
    pubsub_topic   = google_pubsub_topic.daily_topic.id
    retry_policy = "RETRY_POLICY_DO_NOT_RETRY"
    service_account_email = data.google_service_account.service_account.email
  }
}

########################
# Cloud Scheduler Job
########################
resource "google_cloud_scheduler_job" "daily_job" {
  name      = "daily-pubsub-job"
  schedule  = "15 7 * * TUE-SAT" # daily at midnight UTC
  time_zone = "Asia/Singapore"
  

  pubsub_target {
    topic_name = google_pubsub_topic.daily_topic.id
    data       = base64encode("{\"trigger\":\"daily\"}")
  }
  # http_target {
  #   http_method = "POST"
  #   uri         = "https://pubsub.googleapis.com/v1/projects/${var.project_id}/topics/${google_pubsub_topic.daily_topic.id}:publish"
  #   body        = base64encode("{\"messages\": [{\"data\": \"\", \"attributes\": {}}]}")
  #   headers = {
  #     "Content-Type" = "application/json"
  #   }
  #   oidc_token {
  #     service_account_email = data.google_service_account.service_account.email
  #     audience = google_cloudfunctions2_function.function.service_config[0].uri
  #   }
  # }

}
