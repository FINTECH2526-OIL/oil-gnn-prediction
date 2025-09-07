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
  depends_on = [google_project_service.artifact_registry]
}


module "cloud_run" {
  depends_on = [  ]
  source  = "GoogleCloudPlatform/cloud-run/google"
  version = "~> 0.16"

  service_name          = var.service_name
  project_id            = module.google_project.gcp_project_id
  location              = module.google_project.gcp_project_region
  image                 = "${var.project_region}-docker.pkg.dev/${var.project_id}/${var.docker_repo_name}/${var.service_name}:latest"
  service_account_email = data.google_service_account.service_account.email
}


// TODO: Modify this to include
// - Cloud Build (Should also require GCS)
// - Cloud Run (Invoker, Creator, Modifier)
// - GCS Storage

data "google_iam_policy" "noauth" {
  binding {
    role = "roles/run.invoker"
    members = [
      "allUsers",
    ]
  }
}