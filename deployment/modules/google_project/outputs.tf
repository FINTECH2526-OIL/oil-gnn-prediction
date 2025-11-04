data "google_client_config" "this" {}

output "gcp_project_id" {
  value = data.google_client_config.this.project
}
output "gcp_project_region" {
  value = data.google_client_config.this.region
}