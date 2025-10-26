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