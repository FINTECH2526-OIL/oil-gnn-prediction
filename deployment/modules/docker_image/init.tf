terraform {
    required_providers {
docker = {
              source = "kreuzwerker/docker"
              version = "~> 3.0" # Use an appropriate version constraint
            }
    }
}
provider "docker" {
    host = "unix:///var/run/docker.sock" # For Linux/macOS
    # host = "npipe:////.//pipe//docker_engine" # For Windows with WSL2
    # host = "tcp://localhost:2375" # For TCP connections
}