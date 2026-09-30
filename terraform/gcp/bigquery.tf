resource "google_bigquery_dataset" "analytics_dataset" {
  dataset_id                  = "cropsense_analytics"
  friendly_name               = "CropSense AI Analytics Log Dataset"
  description                 = "Looker Studio database containing audits of AI queries, marketplace metrics, and severe weather warnings"
  location                    = var.region
  default_table_expiration_ms = 31536000000 # 365 days

  depends_on = [google_project_service.apis]
}

resource "google_bigquery_table" "ai_queries" {
  dataset_id = google_bigquery_dataset.analytics_dataset.dataset_id
  table_id   = "ai_queries"
  schema = <<EOF
[
  {"name": "timestamp", "type": "TIMESTAMP", "mode": "REQUIRED"},
  {"name": "user_id", "type": "STRING", "mode": "NULLABLE"},
  {"name": "session_id", "type": "STRING", "mode": "NULLABLE"},
  {"name": "query", "type": "STRING", "mode": "REQUIRED"},
  {"name": "response", "type": "STRING", "mode": "NULLABLE"},
  {"name": "subagent_called", "type": "STRING", "mode": "NULLABLE"}
]
EOF
}

resource "google_bigquery_table" "farm_events" {
  dataset_id = google_bigquery_dataset.analytics_dataset.dataset_id
  table_id   = "farm_events"
  schema = <<EOF
[
  {"name": "timestamp", "type": "TIMESTAMP", "mode": "REQUIRED"},
  {"name": "user_id", "type": "STRING", "mode": "REQUIRED"},
  {"name": "farm_id", "type": "STRING", "mode": "REQUIRED"},
  {"name": "action", "type": "STRING", "mode": "REQUIRED"},
  {"name": "soil_type", "type": "STRING", "mode": "NULLABLE"},
  {"name": "irrigation_type", "type": "STRING", "mode": "NULLABLE"}
]
EOF
}

resource "google_bigquery_table" "market_transactions" {
  dataset_id = google_bigquery_dataset.analytics_dataset.dataset_id
  table_id   = "market_transactions"
  schema = <<EOF
[
  {"name": "timestamp", "type": "TIMESTAMP", "mode": "REQUIRED"},
  {"name": "buyer_id", "type": "STRING", "mode": "REQUIRED"},
  {"name": "seller_id", "type": "STRING", "mode": "REQUIRED"},
  {"name": "listing_id", "type": "STRING", "mode": "REQUIRED"},
  {"name": "quantity", "type": "FLOAT", "mode": "REQUIRED"},
  {"name": "price", "type": "FLOAT", "mode": "REQUIRED"},
  {"name": "status", "type": "STRING", "mode": "REQUIRED"}
]
EOF
}

resource "google_bigquery_table" "weather_warnings" {
  dataset_id = google_bigquery_dataset.analytics_dataset.dataset_id
  table_id   = "weather_warnings"
  schema = <<EOF
[
  {"name": "timestamp", "type": "TIMESTAMP", "mode": "REQUIRED"},
  {"name": "region", "type": "STRING", "mode": "REQUIRED"},
  {"name": "severity", "type": "STRING", "mode": "REQUIRED"},
  {"name": "message", "type": "STRING", "mode": "REQUIRED"}
]
EOF
}
