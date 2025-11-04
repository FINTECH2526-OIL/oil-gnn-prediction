resource "google_compute_instance" "prometheus_vm" {
  name         = "prometheus"
  machine_type = "e2-micro"
  zone         = "${var.project_region}-b"

  boot_disk {
    initialize_params {
      image = "ubuntu-os-cloud/ubuntu-2204-lts"
    }
  }

  network_interface {
    network    = var.vpc_name
    subnetwork = var.subnet_name
    access_config {}
  }

  metadata_startup_script = <<-EOF
    #!/bin/bash
    sudo apt update
    sudo apt install -y prometheus
    echo "scrape_configs:
      - job_name: 'cloud-run'
        metrics_path: /metrics
        static_configs:
          - targets: ['${var.cloud_run_url}']" | sudo tee /etc/prometheus/prometheus.yml
    sudo systemctl restart prometheus
  EOF
}

output "prometheus_url" {
  value = google_compute_instance.prometheus_vm.self_link
  
}