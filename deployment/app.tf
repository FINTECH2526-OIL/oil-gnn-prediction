module "docker_repo" {
  source           = "./modules/docker_repo"
  project_id       = var.project_id
  project_region   = var.project_region
  docker_repo_name = var.docker_repo_name
}

# module "redis" {
#   depends_on = [ module.vpc ]
#   source = "./modules/redis_instance" 
#   instance_name = "redis"
#   project_id = var.project_id
#   project_region = var.project_region
#   vpc_name = module.vpc.vpc_name
# }

module "model_service" {
  depends_on         = [module.docker_repo] //module.redis]
  source             = "./modules/cloud_run"
  service_account_id = var.service_account_id
  project_id         = var.project_id
  project_region     = var.project_region
  service_name       = var.model_service_name
  docker_repo_name   = var.docker_repo_name
  limits = {
    cpu    = 2
    memory = "8Gi"
  }
  timeout = 300
  service_env_vars = [{
    name  = "GCS_BUCKET_NAME"
    value = var.GCS_BUCKET_NAME
    },
    {
      name  = "GCS_PROCESSED_PATH"
      value = var.GCS_PROCESSED_PATH
    },
    {
      name  = "GCS_MODELS_PATH"
      value = var.GCS_MODELS_PATH
    },
    {
      name  = "MODEL_RUN_ID"
      value = var.MODEL_RUN_ID
    },
    {
      name  = "ALPHA_VANTAGE_API_KEY"
      value = var.ALPHA_VANTAGE_API_KEY
    }
  ]
  template_annotations = {
    "autoscaling.knative.dev/minScale"     = "1"
    "run.googleapis.com/cpu-throttling"      = false 
  }
  # service_env_vars = [{
  #   name = "REDIS_URL" 
  #   value = module.redis.redis_url
  # }, 
  # {
  #   name = "REDIS_PORT"
  #   value = module.redis.redis_port
  # }
  # ]
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
  use_image          = var.use_image
  # NOTE: ADD MODEL URL INTO DOCKER BUILD INSTEAD
  # service_env_vars = [{
  #   name  = "MODEL_URL"
  #   value = module.model_service.service_url
  # }]
  # app_path           = "${path.cwd}/template_site/"
  #   app_path           = "${path.cwd}/../gnn-frontend/"
  limits = {
    memory = "512Mi"
    cpu    = 1
  }
}

module "function_pipeline" {
  source      = "./modules/pipeline"
  bucket_name = var.GCS_BUCKET_NAME
  project_id  = var.project_id
  region      = var.project_region
  env_vars = {
    ALPHA_VANTAGE_API_KEY = var.ALPHA_VANTAGE_API_KEY
    GCS_BUCKET_NAME       = var.GCS_BUCKET_NAME
    GCS_PROCESSED_PATH    = var.GCS_PROCESSED_PATH
    GCS_MODELS_PATH       = var.GCS_MODELS_PATH
    MODEL_RUN_ID = var.MODEL_RUN_ID
  }
  service_account_id = var.service_account_id
}

output "web_service_url" {
  value = module.webapp.service_url
}
output "model_service_url" {
  value = module.model_service.service_url
}