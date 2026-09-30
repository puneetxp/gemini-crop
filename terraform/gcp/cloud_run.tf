# Cloud Run is deployed via deploy-gcp.sh (after Docker image is built and pushed).
# Terraform manages infrastructure (SQL, VPC, IAM, BigQuery, Firestore).
# The deploy script runs: gcloud run deploy ... after pushing the image.
#
# If you want Terraform to manage Cloud Run, run deploy-gcp.sh first to push
# the image, then uncomment the resources below and run terraform apply.

/*
resource "google_cloud_run_service" "backend" {
  name     = "cropsense-backend"
  location = var.region

  template {
    spec {
      service_account_name = google_service_account.run_sa.email
      containers {
        image = "us-central1-docker.pkg.dev/${var.project_id}/cropsense-repo/cropsense-backend:latest"

        resources {
          limits = {
            memory = "2Gi"
            cpu    = "2000m"
          }
        }

        env {
          name  = "GOOGLE_CLOUD_PROJECT"
          value = var.project_id
        }
        env {
          name  = "GOOGLE_CLOUD_REGION"
          value = var.region
        }
        env {
          name  = "GOOGLE_CLOUD_SQL_INSTANCE"
          value = google_sql_database_instance.postgres_instance.connection_name
        }
        env {
          name  = "POSTGRES_USER"
          value = google_sql_user.db_user.name
        }
        env {
          name  = "POSTGRES_PASSWORD"
          value = google_sql_user.db_user.password
        }
        env {
          name  = "POSTGRES_DB"
          value = google_sql_database.database.name
        }
        env {
          name  = "ENVIRONMENT"
          value = var.environment
        }
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }

  depends_on = [
    google_project_service.apis,
    google_sql_database_instance.postgres_instance
  ]
}

resource "google_cloud_run_service_iam_member" "public_access" {
  service  = google_cloud_run_service.backend.name
  location = google_cloud_run_service.backend.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}
*/
