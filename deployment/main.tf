module "webapp" {
  source             = "./modules/webapp"
  service_account_id = var.service_account_id
  project_id         = var.project_id
  project_region     = var.project_region
  service_name       = var.service_name
  docker_repo_name   = var.docker_repo_name
  app_path           = "${path.cwd}/template_site/"
  #   app_path           = "${path.cwd}/../gnn-frontend/"
}