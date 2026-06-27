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

resource "google_service_account" "web" {
  account_id   = "sa-web"
  display_name = "Web Frontend Service Account"
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
    max_instance_request_concurrency = 80
    scaling {
      max_instance_count = 5
    }
    
    # Placeholder image. CI/CD will replace this with the real image.
    containers {
      image = "us-docker.pkg.dev/cloudrun/container/hello"
      
      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
      }
      
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

  lifecycle {
    ignore_changes = [
      template[0].containers[0].image
    ]
  }
}

# The API is called directly from the user's browser (Next.js client-side), 
# so it needs to be public.
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
    service_account = google_service_account.web.email
    scaling {
      max_instance_count = 5
    }
    
    containers {
      image = "us-docker.pkg.dev/cloudrun/container/hello"
      
      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
      }
      
      # Passed as API_URL to be dynamically read or proxied at runtime by Next.js server,
      # avoiding build-time NEXT_PUBLIC_ embedding.
      env {
        name  = "API_URL"
        value = google_cloud_run_v2_service.api.uri
      }
    }
  }

  lifecycle {
    ignore_changes = [
      template[0].containers[0].image
    ]
  }
}

resource "google_cloud_run_service_iam_member" "web_invoker" {
  location = google_cloud_run_v2_service.web.location
  project  = google_cloud_run_v2_service.web.project
  service  = google_cloud_run_v2_service.web.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
