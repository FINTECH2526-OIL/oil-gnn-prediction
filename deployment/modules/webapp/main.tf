module "google_project" {
  source = "../google_project"
}

data "google_service_account" "service_account" {
  account_id = var.service_account_id
}


resource "google_artifact_registry_repository" "docker_repo" {
  project      = var.project_id
  location     = var.project_region
  repository_id = var.docker_repo_name
  description  = "Docker repository for Cloud Run images"
  format       = "DOCKER"
  # Optional: Keep image tags immutable to prevent overwrites
  # immutable_tags = true 
  
  # Wait for the API to be enabled before creating the repository
}

# module "docker_image" {
#   source = "../docker_image"
#   build_path = var.app_path
#   docker_url = "${var.project_region}-docker.pkg.dev/${var.project_id}/${var.docker_repo_name}/${var.service_name}:latest"
#   project_region = var.project_region

# }


module "cloud_run" {
  depends_on = [google_artifact_registry_repository.docker_repo]
  source  = "GoogleCloudPlatform/cloud-run/google"
  version = "~> 0.16"

  service_name          = var.service_name
  project_id            = module.google_project.gcp_project_id
  location              = module.google_project.gcp_project_region
  image                 = "${var.project_region}-docker.pkg.dev/${var.project_id}/${var.docker_repo_name}/${var.service_name}:latest"
  service_account_email = data.google_service_account.service_account.email
}


data "google_iam_policy" "noauth" {
  binding {
    role = "roles/run.invoker"
    members = [
      "allUsers",
    ]
  }
}

resource "google_cloud_run_service_iam_policy" "noauth" {
  location    = module.cloud_run.location
  project     = module.cloud_run.project_id
  service     = module.cloud_run.service_name
  policy_data = data.google_iam_policy.noauth.policy_data
}