resource "null_resource" "auth_docker_gcp" {
    triggers = {
      always_run = timestamp()
    }
  provisioner "local-exec" {
    command = <<-EOT
      gcloud auth configure-docker ${var.project_region}-docker.pkg.dev;
      docker push ${docker_image.my_app_image.name}
    EOT
    
  }
  depends_on = [ docker_image.my_app_image ]
}

resource "docker_image" "my_app_image" {
  name = var.docker_url
  build {
    context    = var.build_path
    dockerfile = "Dockerfile"
  }
}