#!/bin/bash
# =============================================================================
# Import all existing GCP resources into Terraform state
# Run this once before terraform apply if resources were partially created
# Usage: ./import-existing.sh
# =============================================================================

set -e

PROJECT="project-5449519e-8afb-48ac-b77"
REGION="us-central1"
DB_PASS="changeme-strong-password"   # ← must match DB_PASSWORD in deploy-gcp.sh

VARS="-var=project_id=${PROJECT} -var=region=${REGION} -var=db_password=${DB_PASS}"

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
ok()   { echo -e "${GREEN}  ✓ $1${NC}"; }
skip() { echo -e "${YELLOW}  ↷ $1 — already in state or not found, skipping${NC}"; }

import_resource() {
  local label="$1"
  local resource="$2"
  local id="$3"
  echo -e "\nImporting: $label"
  terraform import $VARS "$resource" "$id" && ok "$label" || skip "$label"
}

# ── VPC & Networking ──────────────────────────────────────────────────────────
import_resource "VPC network" \
  google_compute_network.vpc \
  "projects/${PROJECT}/global/networks/cropsense-vpc"

import_resource "Subnet" \
  google_compute_subnetwork.subnet \
  "${PROJECT}/${REGION}/cropsense-subnet"

import_resource "Private IP allocation" \
  google_compute_global_address.private_ip_alloc \
  "projects/${PROJECT}/global/addresses/cropsense-private-ip-alloc"

import_resource "Private VPC connection" \
  google_service_networking_connection.private_vpc_connection \
  "projects/${PROJECT}/global/networks/cropsense-vpc:servicenetworking.googleapis.com"

# ── Cloud SQL ─────────────────────────────────────────────────────────────────
import_resource "Cloud SQL instance" \
  google_sql_database_instance.postgres_instance \
  "${PROJECT}/cropsense-postgres-db"

import_resource "Cloud SQL database" \
  google_sql_database.database \
  "${PROJECT}/cropsense-postgres-db/cropsense"

import_resource "Cloud SQL user" \
  google_sql_user.db_user \
  "${PROJECT}/cropsense-postgres-db/cropsense"

# ── IAM & Service Account ─────────────────────────────────────────────────────
import_resource "Cloud Run service account" \
  google_service_account.run_sa \
  "projects/${PROJECT}/serviceAccounts/cropsense-run-sa@${PROJECT}.iam.gserviceaccount.com"

import_resource "IAM: Vertex AI user" \
  google_project_iam_member.vertex_ai_user \
  "${PROJECT} roles/aiplatform.user serviceAccount:cropsense-run-sa@${PROJECT}.iam.gserviceaccount.com"

import_resource "IAM: Firestore user" \
  google_project_iam_member.firestore_user \
  "${PROJECT} roles/datastore.user serviceAccount:cropsense-run-sa@${PROJECT}.iam.gserviceaccount.com"

import_resource "IAM: BigQuery editor" \
  google_project_iam_member.bigquery_editor \
  "${PROJECT} roles/bigquery.dataEditor serviceAccount:cropsense-run-sa@${PROJECT}.iam.gserviceaccount.com"

import_resource "IAM: Cloud SQL client" \
  google_project_iam_member.sql_client \
  "${PROJECT} roles/cloudsql.client serviceAccount:cropsense-run-sa@${PROJECT}.iam.gserviceaccount.com"

# ── Firestore ─────────────────────────────────────────────────────────────────
import_resource "Firestore database" \
  google_firestore_database.database \
  "projects/${PROJECT}/databases/(default)"

# ── BigQuery ──────────────────────────────────────────────────────────────────
import_resource "BigQuery dataset" \
  google_bigquery_dataset.analytics_dataset \
  "${PROJECT}/cropsense_analytics"

import_resource "BigQuery table: ai_queries" \
  google_bigquery_table.ai_queries \
  "${PROJECT}/cropsense_analytics/ai_queries"

import_resource "BigQuery table: farm_events" \
  google_bigquery_table.farm_events \
  "${PROJECT}/cropsense_analytics/farm_events"

import_resource "BigQuery table: market_transactions" \
  google_bigquery_table.market_transactions \
  "${PROJECT}/cropsense_analytics/market_transactions"

import_resource "BigQuery table: weather_warnings" \
  google_bigquery_table.weather_warnings \
  "${PROJECT}/cropsense_analytics/weather_warnings"

# ── Cloud Run ─────────────────────────────────────────────────────────────────
import_resource "Cloud Run service" \
  google_cloud_run_service.backend \
  "locations/${REGION}/namespaces/${PROJECT}/services/cropsense-backend"

import_resource "Cloud Run public IAM" \
  google_cloud_run_service_iam_member.public_access \
  "${PROJECT}/${REGION}/cropsense-backend roles/run.invoker allUsers"

echo -e "\n${GREEN}═══════════════════════════════════════════${NC}"
echo -e "${GREEN}  Import complete! Now run terraform apply.${NC}"
echo -e "${GREEN}═══════════════════════════════════════════${NC}"
echo ""
echo "  cd /Users/puneetsharma/cropsense-ai/cropsense-ai"
echo "  ./deploy-gcp.sh"
