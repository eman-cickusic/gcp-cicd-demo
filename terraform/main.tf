provider "google" {
  project = var.project_id
  region  = var.region
}

# Artifact Registry for Docker images
resource "google_artifact_registry_repository" "docker_repo" {
  location      = var.region
  repository_id = "my-repo"
  description   = "Docker repository for secure CI/CD pipeline"
  format        = "DOCKER"
  
  docker_config {
    immutable_tags = true
  }
}

# Secret Manager secret for API key
resource "google_secret_manager_secret" "api_key" {
  secret_id = "api-key"
  
  labels = {
    environment = "production"
    component   = "api"
  }
  
  replication {
    user_managed {
      replicas {
        location = var.region
      }
    }
  }
}

# Secret version for API key
resource "google_secret_manager_secret_version" "api_key_version" {
  secret      = google_secret_manager_secret.api_key.id
  secret_data = var.api_key_value
}

# Service account for GitHub Actions
resource "google_service_account" "gh_actions" {
  account_id   = "github-actions-deployer"
  display_name = "GitHub Actions CI/CD with Security"
  description  = "Service account for secure CI/CD pipeline"
}

# IAM roles for Cloud Run
resource "google_project_iam_member" "run_admin" {
  project = var.project_id
  role    = "roles/run.admin"
  member  = "serviceAccount:${google_service_account.gh_actions.email}"
}

# IAM roles for Artifact Registry
resource "google_project_iam_member" "artifact_writer" {
  project = var.project_id
  role    = "roles/artifactregistry.writer"
  member  = "serviceAccount:${google_service_account.gh_actions.email}"
}

# IAM roles for Cloud Build (for security scanning)
resource "google_project_iam_member" "build_editor" {
  project = var.project_id
  role    = "roles/cloudbuild.builds.editor"
  member  = "serviceAccount:${google_service_account.gh_actions.email}"
}

# IAM role for Secret Manager access
resource "google_project_iam_member" "secret_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.gh_actions.email}"
}

# Service account user role for compute engine
resource "google_service_account_iam_member" "act_as_compute_sa" {
  service_account_id = "projects/${var.project_id}/serviceAccounts/${var.project_number}-compute@developer.gserviceaccount.com"
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${google_service_account.gh_actions.email}"
}

# Service account for Cloud Run service (principle of least privilege)
resource "google_service_account" "cloud_run_sa" {
  account_id   = "cloud-run-service"
  display_name = "Cloud Run Service Account"
  description  = "Service account for Cloud Run service with minimal permissions"
}

# Grant Cloud Run service account access to Secret Manager
resource "google_project_iam_member" "cloud_run_secret_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.cloud_run_sa.email}"
}

# Grant Cloud Run service account logging permissions
resource "google_project_iam_member" "cloud_run_log_writer" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.cloud_run_sa.email}"
}

# Cloud Run service with security best practices
resource "google_cloud_run_service" "app" {
  name     = "my-app"
  location = var.region

  template {
    metadata {
      labels = {
        environment = "production"
        version     = "2.0.0"
      }
      annotations = {
        "autoscaling.knative.dev/maxScale"      = "100"
        "autoscaling.knative.dev/minScale"      = "1"
        "run.googleapis.com/execution-environment" = "gen2"
        "run.googleapis.com/cpu-throttling"     = "false"
      }
    }
    
    spec {
      service_account_name  = google_service_account.cloud_run_sa.email
      container_concurrency = 80
      timeout_seconds      = 300
      
      containers {
        image = "us-central1-docker.pkg.dev/${var.project_id}/my-repo/my-app:latest"
        
        ports {
          container_port = 8080
        }
        
        env {
          name  = "ENVIRONMENT"
          value = "production"
        }
        
        env {
          name  = "GCP_PROJECT_ID"
          value = var.project_id
        }
        
        resources {
          limits = {
            cpu    = "1000m"
            memory = "512Mi"
          }
          requests = {
            cpu    = "100m"
            memory = "128Mi"
          }
        }
        
        # Security context
        security_context {
          run_as_non_root = true
        }
        
        # Liveness probe
        liveness_probe {
          http_get {
            path = "/health"
            port = 8080
          }
          initial_delay_seconds = 30
          period_seconds       = 30
        }
        
        # Readiness probe
        startup_probe {
          http_get {
            path = "/health"
            port = 8080
          }
          initial_delay_seconds = 10
          period_seconds       = 10
          failure_threshold    = 3
        }
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }

  autogenerate_revision_name = true
}

# IAM policy for public access (can be restricted as needed)
resource "google_cloud_run_service_iam_member" "public_access" {
  service  = google_cloud_run_service.app.name
  location = google_cloud_run_service.app.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Cloud Logging sink for security monitoring
resource "google_logging_project_sink" "security_sink" {
  name = "security-events-sink"
  
  # Send security-related logs to a dedicated log bucket
  destination = "logging.googleapis.com/projects/${var.project_id}/locations/global/buckets/security-logs"
  
  # Filter for security events
  filter = <<-EOT
    resource.type="cloud_run_revision"
    AND (
      httpRequest.status>=400
      OR jsonPayload.severity="ERROR"
      OR jsonPayload.message=~"security|unauthorized|forbidden|invalid.*key"
    )
  EOT
  
  unique_writer_identity = true
}

# Log bucket for security events
resource "google_logging_project_bucket_config" "security_logs" {
  project          = var.project_id
  location         = "global"
  retention_days   = 90
  bucket_id        = "security-logs"
  description      = "Security events and audit logs"
}

# Enable required APIs
resource "google_project_service" "required_apis" {
  for_each = toset([
    "run.googleapis.com",
    "cloudbuild.googleapis.com",
    "artifactregistry.googleapis.com",
    "secretmanager.googleapis.com",
    "logging.googleapis.com",
    "monitoring.googleapis.com",
    "cloudresourcemanager.googleapis.com"
  ])
  
  project = var.project_id
  service = each.key
  
  disable_dependent_services = false
}

# Monitoring policy for failed requests
resource "google_monitoring_alert_policy" "failed_requests" {
  display_name = "High Error Rate - Cloud Run"
  combiner     = "OR"
  
  conditions {
    display_name = "Error rate too high"
    
    condition_threshold {
      filter          = "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"my-app\""
      duration        = "300s"
      comparison      = "COMPARISON_GREATER_THAN"
      threshold_value = 10
      
      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_RATE"
        cross_series_reducer = "REDUCE_SUM"
      }
    }
  }
  
  notification_channels = []
  
  alert_strategy {
    auto_close = "1800s"
  }
}
