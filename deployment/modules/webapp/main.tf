module "google_project" {
  source = "../google_project"
}

data "google_service_account" "service_account" {
  account_id = var.service_account_id
}


module "cloud_run" {
  source  = "GoogleCloudPlatform/cloud-run/google"
  version = "~> 0.16"

  service_name          = "oil-gnn-prediction" // Hardcoded to reduce confusion in understanding deployment
  project_id            = module.google_project.gcp_project_id
  location              = module.google_project.gcp_project_region
  image                 = "${var.project_region}-docker.pkg.dev/${var.project_id}/${self.service_name}"
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