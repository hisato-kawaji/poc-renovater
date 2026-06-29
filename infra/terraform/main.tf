terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# ---------------------------------------------------------
# Variables
# ---------------------------------------------------------
variable "project_id" {
  type = string
}

variable "region" {
  type    = string
  default = "asia-northeast1"
}

# ---------------------------------------------------------
# Cloud SQL (PostgreSQL)
# ---------------------------------------------------------
resource "google_sql_database_instance" "poc_foundry_db" {
  name             = "poc-foundry-db"
  database_version = "POSTGRES_15"
  region           = var.region

  settings {
    tier = "db-f1-micro"
    backup_configuration {
      enabled = true
    }
  }
}

resource "google_sql_database" "default_db" {
  name     = "poc_foundry"
  instance = google_sql_database_instance.poc_foundry_db.name
}

resource "google_sql_user" "default_user" {
  name     = "foundry_api"
  instance = google_sql_database_instance.poc_foundry_db.name
  password = var.db_password
}

variable "db_password" {
  type      = string
  sensitive = true
}

# ---------------------------------------------------------
# Cloud Run (API)
# ---------------------------------------------------------
resource "google_cloud_run_v2_service" "api_service" {
  name     = "poc-foundry-api"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    containers {
      image = "gcr.io/${var.project_id}/poc-foundry-api:latest"
      env {
        name  = "DATABASE_URL"
        value = "postgresql+asyncpg://${google_sql_user.default_user.name}:${var.db_password}@/${google_sql_database.default_db.name}?host=/cloudsql/${google_sql_database_instance.poc_foundry_db.connection_name}"
      }
    }
  }
}

# ---------------------------------------------------------
# Load Balancing (External HTTP(S) LB)
# ---------------------------------------------------------
resource "google_compute_region_network_endpoint_group" "cloudrun_neg" {
  name                  = "api-neg"
  network_endpoint_type = "SERVERLESS"
  region                = var.region
  cloud_run {
    service = google_cloud_run_v2_service.api_service.name
  }
}

resource "google_compute_backend_service" "backend" {
  name                  = "api-backend"
  protocol              = "HTTPS"
  load_balancing_scheme = "EXTERNAL_MANAGED"
  
  backend {
    group = google_compute_region_network_endpoint_group.cloudrun_neg.id
  }
}

resource "google_compute_url_map" "url_map" {
  name            = "poc-foundry-urlmap"
  default_service = google_compute_backend_service.backend.id
}

resource "google_compute_target_http_proxy" "http_proxy" {
  name    = "poc-foundry-http-proxy"
  url_map = google_compute_url_map.url_map.id
}

resource "google_compute_global_forwarding_rule" "default" {
  name                  = "poc-foundry-forwarding-rule"
  target                = google_compute_target_http_proxy.http_proxy.id
  port_range            = "80"
  load_balancing_scheme = "EXTERNAL_MANAGED"
}
