resource "google_redis_instance" "cheap_redis" {
  name               = var.instance_name
  tier               = "BASIC"
    memory_size_gb = 1
    region = var.project_region
    authorized_network = "projects/${var.project_id}/global/networks/${var.vpc_name}"
}

output "redis_url" {
    value = google_redis_instance.cheap_redis.host 
}

output "redis_port" {
    value = google_redis_instance.cheap_redis.port
  
}