terraform {
  cloud {

    organization = "fintech-stuff"

    workspaces {
      name = "github-fintech-oil"
    }
  }
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "6.8.0"
    }
    google-beta = {
      version = "6.49.2"
    }
  }
}

provider "google" {
  project     = var.project_id
  region      = var.project_region
  credentials = var.credentials
}


provider "google-beta" {
  project     = var.project_id
  region      = var.project_region
  credentials = var.credentials
}

