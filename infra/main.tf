provider "google" {
  project = var.project_id
  region  = var.region
}

# Service Accounts
resource "google_service_account" "api" {
  account_id   = "sa-api"
  display_name = "API Service Account"
}

resource "google_service_account" "deploy" {
  account_id   = "sa-deploy"
  display_name = "Deploy Service Account"
}

resource "google_service_account" "sandbox" {
  account_id   = "sa-sandbox"
  display_name = "Sandbox Service Account"
}

resource "google_service_account" "preview_runtime" {
  account_id   = "sa-preview-runtime"
  display_name = "Preview Runtime Service Account"
}

# Storage Bucket
resource "google_storage_bucket" "uploads" {
  name          = "${var.project_id}-uploads"
  location      = var.region
  force_destroy = true
  lifecycle_rule {
    condition {
      age = 90
    }
    action {
      type = "Delete"
    }
  }
}

# Firestore
resource "google_firestore_database" "default" {
  project     = var.project_id
  name        = "(default)"
  location_id = var.region
  type        = "FIRESTORE_NATIVE"
}

# Artifact Registry
resource "google_artifact_registry_repository" "repo" {
  location      = var.region
  repository_id = "poc-foundry"
  description   = "Docker repository for PoC Foundry"
  format        = "DOCKER"
}

# Secret Manager
resource "google_secret_manager_secret" "github_private_key" {
  secret_id = "GITHUB_APP_PRIVATE_KEY"
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret" "github_webhook_secret" {
  secret_id = "GITHUB_WEBHOOK_SECRET"
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret" "anthropic_api_key" {
  secret_id = "ANTHROPIC_API_KEY"
  replication {
    auto {}
  }
}

# IAM bindings for SA
resource "google_project_iam_member" "api_firestore" {
  project = var.project_id
  role    = "roles/datastore.user"
  member  = "serviceAccount:${google_service_account.api.email}"
}

resource "google_project_iam_member" "api_storage" {
  project = var.project_id
  role    = "roles/storage.admin"
  member  = "serviceAccount:${google_service_account.api.email}"
}

resource "google_project_iam_member" "api_secret" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.api.email}"
}

resource "google_project_iam_member" "api_vertex" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.api.email}"
}

# Cloud Run Service for API
resource "google_cloud_run_v2_service" "api" {
  name     = "poc-foundry-api"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    service_account = google_service_account.api.email
    
    # Placeholder image. CI/CD will replace this with the real image.
    containers {
      image = "us-docker.pkg.dev/cloudrun/container/hello"
      
      env {
        name  = "GOOGLE_CLOUD_PROJECT"
        value = var.project_id
      }
      env {
        name  = "GOOGLE_GENAI_USE_VERTEXAI"
        value = "1"
      }
      env {
        name  = "GCS_UPLOAD_BUCKET"
        value = google_storage_bucket.uploads.name
      }
    }
  }
}

resource "google_cloud_run_service_iam_member" "api_invoker" {
  location = google_cloud_run_v2_service.api.location
  project  = google_cloud_run_v2_service.api.project
  service  = google_cloud_run_v2_service.api.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Cloud Run Service for Web (Frontend)
resource "google_cloud_run_v2_service" "web" {
  name     = "poc-foundry-web"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    service_account = google_service_account.deploy.email
    
    containers {
      image = "us-docker.pkg.dev/cloudrun/container/hello"
      
      env {
        name  = "NEXT_PUBLIC_API_URL"
        value = google_cloud_run_v2_service.api.uri
      }
    }
  }
}

resource "google_cloud_run_service_iam_member" "web_invoker" {
  location = google_cloud_run_v2_service.web.location
  project  = google_cloud_run_v2_service.web.project
  service  = google_cloud_run_v2_service.web.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
