provider "google" {
 project = var.project_id
 region  = var.region
}
resource "google_artifact_registry_repository" "docker_repo" {
 location      = var.region
 repository_id = "my-repo"
 description   = "Docker repository"
 format        = "DOCKER"
}
resource "google_service_account" "gh_actions" {
 account_id   = "github-actions-deployer"
 display_name = "GitHub Actions CI/CD"
}
resource "google_project_iam_member" "run_admin" {
 project = var.project_id
 role    = "roles/run.admin"
 member  = "serviceAccount:${google_service_account.gh_actions.email}"
}
resource "google_project_iam_member" "artifact_writer" {
 project = var.project_id
 role    = "roles/artifactregistry.writer"
 member  = "serviceAccount:${google_service_account.gh_actions.email}"
}
resource "google_project_iam_member" "build_editor" {
 project = var.project_id
 role    = "roles/cloudbuild.builds.editor"
 member  = "serviceAccount:${google_service_account.gh_actions.email}"
}
resource "google_service_account_iam_member" "act_as_compute_sa" {
 service_account_id = "projects/${var.project_id}/serviceAccounts/${var.project_number}-compute@developer.gserviceaccount.com"
 role               = "roles/iam.serviceAccountUser"
 member             = "serviceAccount:${google_service_account.gh_actions.email}"
}
resource "google_cloud_run_service" "app" {
 name     = "my-app"
 location = var.region
 template {
   spec {
     containers {
       image = "us-central1-docker.pkg.dev/${var.project_id}/my-repo/my-app:latest"
     }
   }
 }
 traffic {
   percent         = 100
   latest_revision = true
 }
 autogenerate_revision_name = true
}