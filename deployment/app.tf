module "docker_repo" {
  source           = "./modules/docker_repo"
  project_id       = var.project_id
  project_region   = var.project_region
  docker_repo_name = var.docker_repo_name
}

module "redis" {
  depends_on = [ module.vpc ]
  source = "./modules/redis_instance" 
  instance_name = "redis"
  project_id = var.project_id
  project_region = var.project_region
  vpc_name = module.vpc.vpc_name
}

module "model_service" {
  depends_on         = [module.docker_repo, module.redis]
  source             = "./modules/cloud_run"
  service_account_id = var.service_account_id
  project_id         = var.project_id
  project_region     = var.project_region
  service_name       = var.model_service_name
  docker_repo_name   = var.docker_repo_name
  service_env_vars = [{
    name = "REDIS_URL" 
    value = module.redis.redis_url
  }, 
  {
    name = "REDIS_PORT"
    value = module.redis.redis_port
  }
  ]
  use_image = var.use_image
}

module "webapp" {
  depends_on         = [module.docker_repo, module.model_service]
  source             = "./modules/cloud_run"
  service_account_id = var.service_account_id
  project_id         = var.project_id
  project_region     = var.project_region
  service_name       = var.web_service_name
  docker_repo_name   = var.docker_repo_name
  use_image = var.use_image
  # NOTE: ADD MODEL URL INTO DOCKER BUILD INSTEAD
  # service_env_vars = [{
  #   name = "MODEL_URL" 
  #   value = module.model_service.service_url
  # }]
  # app_path           = "${path.cwd}/template_site/"
  #   app_path           = "${path.cwd}/../gnn-frontend/"
}