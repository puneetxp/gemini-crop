resource "google_sql_database_instance" "postgres_instance" {
  name             = "cropsense-postgres-db"
  database_version = "POSTGRES_14"
  region           = var.region

  depends_on = [google_project_service.apis]

  settings {
    tier = "db-f1-micro" # Lightweight instance for dev/testing cost optimization

    ip_configuration {
      ipv4_enabled = true # Public IP — Cloud Run connects via Cloud SQL Auth Proxy
    }
  }

  deletion_protection = false # Set to true for production systems
}

resource "google_sql_database" "database" {
  name     = "cropsense"
  instance = google_sql_database_instance.postgres_instance.name
}

resource "google_sql_user" "db_user" {
  name     = "cropsense"
  instance = google_sql_database_instance.postgres_instance.name
  password = var.db_password
}
