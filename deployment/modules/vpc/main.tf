resource "google_compute_network" "vpc" {
  name = var.vpc_name
}

# For Simplicity, I will stick to
resource "google_compute_subnetwork" "subnet" {
  name          = "subnet-1"
  ip_cidr_range = "10.0.0.0/24"
  region        = var.project_region
  network       = google_compute_network.vpc.id
}

output "vpc_name" {
    value = google_compute_network.vpc.name
}

output "subnet_name" {
    value = google_compute_subnetwork.subnet.name 
}