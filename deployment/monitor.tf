module "vpc" {
    source = "./modules/vpc"
    project_region = var.project_region
    vpc_name = var.vpc_name
}
module "promethus" {
    source = "./modules/prometheus_instance"
    cloud_run_url = module.webapp.service_url
    project_region = var.project_region
    vpc_name = module.vpc.vpc_name
    subnet_name = module.vpc.subnet_name
}