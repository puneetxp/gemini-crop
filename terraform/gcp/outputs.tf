output "postgres_connection_name" {
  description = "The connection name of the Cloud SQL PostgreSQL instance"
  value       = google_sql_database_instance.postgres_instance.connection_name
}

output "bigquery_dataset_id" {
  description = "The ID of the BigQuery Dataset for Looker integration"
  value       = google_bigquery_dataset.analytics_dataset.dataset_id
}

output "run_service_account" {
  description = "Service account email for Cloud Run"
  value       = google_service_account.run_sa.email
}
