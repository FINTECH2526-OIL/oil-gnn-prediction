module "google_project" {
  source = "../google_project"
}

data "google_service_account" "service_account" {
  account_id = var.service_account_id
}



# module "docker_image" {
#   source = "../docker_image"
#   build_path = var.app_path
#   docker_url = "${var.project_region}-docker.pkg.dev/${var.project_id}/${var.docker_repo_name}/${var.service_name}:latest"
#   project_region = var.project_region

# }


module "cloud_run" {
  source  = "GoogleCloudPlatform/cloud-run/google"
  version = "~> 0.16"

  service_name          = var.service_name
  project_id            = module.google_project.gcp_project_id
  location              = module.google_project.gcp_project_region
  image                 = var.use_image ? "${var.project_region}-docker.pkg.dev/${var.project_id}/${var.docker_repo_name}/${var.service_name}:latest" : "gcr.io/cloudrun/hello"
  service_account_email = data.google_service_account.service_account.email
  env_vars = var.service_env_vars
}




data "google_iam_policy" "conditional_auth" {
  binding {
    role = "roles/run.invoker"
    members = [
      var.use_service_account_for_auth ? 
      format("serviceaccount:%s",data.google_service_account.service_account.email)
      : "allUsers"
    ]
  }
}

resource "google_cloud_run_service_iam_policy" "noauth" {
  location    = module.cloud_run.location
  project     = module.cloud_run.project_id
  service     = module.cloud_run.service_name
  policy_data = data.google_iam_policy.conditional_auth.policy_data
}