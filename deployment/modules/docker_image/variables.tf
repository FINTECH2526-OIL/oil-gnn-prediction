variable "docker_url" {
    description = "URL of docker repository + image tag"
    type = string
}

variable "build_path" {
    description = "Folder path of app build context"
    type = string
}

variable "project_region" {
  description = "Project Region"
  type = string
}