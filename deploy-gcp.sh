#!/bin/bash
# =============================================================================
# CropSense AI — GCP deployment (idempotent: safe to re-run for updates)
#
#   ./deploy-gcp.sh            # auto: rebuild only what changed since the last deploy
#   ./deploy-gcp.sh backend    # just the API (python/)
#   ./deploy-gcp.sh frontend   # just the web app (solidjs/)
#   ./deploy-gcp.sh app        # backend + frontend, skip infrastructure
#   ./deploy-gcp.sh infra      # APIs, secrets, Terraform, DB schema, Firebase settings; no image builds
#   ./deploy-gcp.sh all        # everything (first deploy, or after changing terraform/ or secrets)
#
# See "Deploying to GCP" in README.md for what each step does.
#
# Override defaults with env vars, e.g.:
#   GCP_PROJECT=my-proj BILLING_ACCOUNT=XXXXXX-XXXXXX-XXXXXX ./deploy-gcp.sh
#   OPENWEATHER_API_KEY=... ./deploy-gcp.sh      # only needed on first deploy
#   DEMO_EMAIL=... DEMO_PASSWORD=... ./deploy-gcp.sh frontend
#                                                 # one-click "demo farmer" sign-in; the account must exist
#                                                 # (sign up once in the app); the password ships in the bundle
#
# Requires: gcloud (logged in: `gcloud auth login`), terraform, node/npm.
# First deploy also needs psql + cloud-sql-proxy to load the DB schema
# (brew install libpq cloud-sql-proxy).
# =============================================================================

set -euo pipefail

export CLOUDSDK_PYTHON="${CLOUDSDK_PYTHON:-/opt/homebrew/bin/python3}"
export PATH="/opt/homebrew/bin:$HOME/.nvm/versions/node/v24.20.0/bin:$PATH"

GCP_PROJECT="${GCP_PROJECT:-cropsense-ai-a4d5cf}"
GCP_REGION="${GCP_REGION:-us-central1}"
BILLING_ACCOUNT="${BILLING_ACCOUNT:-}"
GAR_REPO="cropsense-repo"
BACKEND_SERVICE="cropsense-backend"
FRONTEND_SERVICE="cropsense-frontend"
DB_NAME="cropsense"
DB_USER="cropsense"

ROOT="$(cd "$(dirname "$0")" && pwd)"
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
step() { echo -e "\n${GREEN}▶ $1${NC}"; }
warn() { echo -e "${YELLOW}⚠ $1${NC}"; }
die()  { echo -e "${RED}✗ $1${NC}"; exit 1; }
gc()   { gcloud --project="$GCP_PROJECT" "$@"; }

secret_exists() { gc secrets describe "$1" >/dev/null 2>&1; }
create_secret() {  # name, value-from-stdin
  gc secrets create "$1" --replication-policy=automatic --data-file=- >/dev/null
}

MODE="${1:-auto}"
case "$MODE" in
  auto|all|app|backend|frontend|infra) ;;
  -h|--help) sed -n 2,21p "$0"; exit 0 ;;
  *) die "Unknown mode '$MODE'. Use: auto | backend | frontend | app | infra | all" ;;
esac

for tool in gcloud terraform npm; do
  command -v "$tool" >/dev/null || die "$tool is not installed"
done

# Image tag = commit; uncommitted changes get a unique suffix so a dirty build never overwrites a commit's image.
COMMIT=$(git -C "$ROOT" rev-parse --short HEAD 2>/dev/null || echo nogit)
image_tag() {  # dir
  if [ -n "$(git -C "$ROOT" status --porcelain -- "$1" 2>/dev/null)" ]; then
    echo "${COMMIT}-dirty-$(date +%Y%m%d%H%M%S)"
  else
    echo "$COMMIT"
  fi
}

# True when <dir> differs from the commit the running <service> was built from (or that can't be told).
needs_deploy() {  # service, dir
  local img tag
  img=$(gc run services describe "$1" --region="$GCP_REGION" \
    --format='value(spec.template.spec.containers[0].image)' 2>/dev/null) || return 0
  tag="${img##*:}"
  git -C "$ROOT" cat-file -e "${tag}^{commit}" 2>/dev/null || return 0
  [ -n "$(git -C "$ROOT" status --porcelain -- "$2")" ] && return 0
  ! git -C "$ROOT" diff --quiet "$tag" HEAD -- "$2"
}

# ── 1. Auth & project ─────────────────────────────────────────────────────────
step "1/9  Checking auth & project"
ACCOUNT=$(gcloud config get-value account 2>/dev/null)
[ -n "$ACCOUNT" ] || die "Not logged in. Run: gcloud auth login"
echo "Account: $ACCOUNT"

if ! gcloud projects describe "$GCP_PROJECT" >/dev/null 2>&1; then
  echo "Project $GCP_PROJECT not found — creating it..."
  gcloud projects create "$GCP_PROJECT" --name="CropSense AI"
fi
if [ "$(gcloud billing projects describe "$GCP_PROJECT" --format='value(billingEnabled)')" != "True" ]; then
  [ -n "$BILLING_ACCOUNT" ] || die "Billing is not enabled on $GCP_PROJECT. Re-run with BILLING_ACCOUNT=<id> (see: gcloud billing accounts list)"
  gcloud billing projects link "$GCP_PROJECT" --billing-account="$BILLING_ACCOUNT" >/dev/null
fi
PROJECT_NUMBER=$(gcloud projects describe "$GCP_PROJECT" --format='value(projectNumber)')

DO_INFRA=false; DO_BACKEND=false; DO_FRONTEND=false
case "$MODE" in
  all)      DO_INFRA=true; DO_BACKEND=true; DO_FRONTEND=true ;;
  infra)    DO_INFRA=true ;;
  app)      DO_BACKEND=true; DO_FRONTEND=true ;;
  backend)  DO_BACKEND=true ;;
  frontend) DO_FRONTEND=true ;;
  auto)
    if ! gc run services describe "$BACKEND_SERVICE" --region="$GCP_REGION" >/dev/null 2>&1 || \
       ! gc run services describe "$FRONTEND_SERVICE" --region="$GCP_REGION" >/dev/null 2>&1; then
      echo "First deploy — running everything."
      DO_INFRA=true; DO_BACKEND=true; DO_FRONTEND=true
    else
      needs_deploy "$BACKEND_SERVICE" python && DO_BACKEND=true
      needs_deploy "$FRONTEND_SERVICE" solidjs && DO_FRONTEND=true
    fi ;;
esac
echo "Plan: infra=$DO_INFRA backend=$DO_BACKEND frontend=$DO_FRONTEND"
if ! $DO_INFRA && ! $DO_BACKEND && ! $DO_FRONTEND; then
  echo -e "${GREEN}✓ Nothing changed in python/ or solidjs/ since the last deploy — nothing to do.${NC}"
  echo "  (After changing terraform/ or secrets, run: ./deploy-gcp.sh infra)"
  exit 0
fi

# ── 2. APIs ───────────────────────────────────────────────────────────────────
if $DO_INFRA; then
step "2/9  Enabling APIs"
gc services enable run.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com \
  sqladmin.googleapis.com secretmanager.googleapis.com bigquery.googleapis.com firestore.googleapis.com \
  aiplatform.googleapis.com compute.googleapis.com iam.googleapis.com cloudscheduler.googleapis.com \
  cloudfunctions.googleapis.com servicenetworking.googleapis.com cloudresourcemanager.googleapis.com

# ── 3. Artifact Registry + Cloud Build permissions ───────────────────────────
step "3/9  Artifact Registry & Cloud Build"
gc artifacts repositories describe "$GAR_REPO" --location="$GCP_REGION" >/dev/null 2>&1 || \
  gc artifacts repositories create "$GAR_REPO" --repository-format=docker --location="$GCP_REGION" \
    --description="CropSense container images"
# Newer projects run Cloud Build as the Compute default service account.
BUILD_SA="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"
for ROLE in roles/artifactregistry.writer roles/logging.logWriter roles/storage.objectViewer; do
  gc projects add-iam-policy-binding "$GCP_PROJECT" --member="serviceAccount:$BUILD_SA" \
    --role="$ROLE" --condition=None --quiet >/dev/null
done

# ── 4. Secrets (created once, never written to disk) ─────────────────────────
step "4/9  Secrets"
secret_exists cropsense-db-password || { openssl rand -base64 48 | tr -d '/+=\n' | head -c 32 | create_secret cropsense-db-password; echo "Generated DB password"; }
secret_exists cropsense-secret-key  || { openssl rand -hex 32 | tr -d '\n' | create_secret cropsense-secret-key; echo "Generated SECRET_KEY"; }
if ! secret_exists cropsense-openweather-key; then
  if [ -z "${OPENWEATHER_API_KEY:-}" ]; then
    read -r -s -p "OpenWeather API key (openweathermap.org → API keys): " OPENWEATHER_API_KEY; echo
  fi
  [ -n "$OPENWEATHER_API_KEY" ] || die "OpenWeather API key is required (the backend refuses to start without it)"
  printf '%s' "$OPENWEATHER_API_KEY" | create_secret cropsense-openweather-key
fi
if ! secret_exists cropsense-vapid-private-key; then
  # Web push keys: raw P-256 key pair, base64url, sliced out of the SEC1 DER key
  VAPID_KEYS=$(openssl ecparam -name prime256v1 -genkey -noout | openssl ec -outform DER 2>/dev/null \
    | python3 -c "import sys,base64; d=sys.stdin.buffer.read(); b=lambda x: base64.urlsafe_b64encode(x).rstrip(b'=').decode(); print(b(d[7:39]), b(d[-65:]))")
  printf '%s' "${VAPID_KEYS% *}" | create_secret cropsense-vapid-private-key
  printf '%s' "${VAPID_KEYS#* }" | create_secret cropsense-vapid-public-key
  unset VAPID_KEYS
  echo "Generated VAPID key pair (web push)"
fi

# ── 5. Terraform (SQL, VPC, IAM, Firestore, BigQuery) ────────────────────────
step "5/9  Terraform"
cd "$ROOT/terraform/gcp"
# Use the gcloud login directly, so no separate `application-default login` is needed.
GOOGLE_OAUTH_ACCESS_TOKEN="$(gcloud auth print-access-token)"
export GOOGLE_OAUTH_ACCESS_TOKEN
export TF_VAR_project_id="$GCP_PROJECT" TF_VAR_region="$GCP_REGION" TF_VAR_environment="production"
TF_VAR_db_password="$(gc secrets versions access latest --secret=cropsense-db-password)"
export TF_VAR_db_password
terraform init -input=false >/dev/null
terraform apply -input=false -auto-approve
cd "$ROOT"

for S in cropsense-db-password cropsense-secret-key cropsense-openweather-key cropsense-vapid-private-key cropsense-vapid-public-key; do
  gc secrets add-iam-policy-binding "$S" --member="serviceAccount:$RUN_SA" \
    --role=roles/secretmanager.secretAccessor >/dev/null
done

# Uploaded photos/documents: Cloud Run's disk is wiped on restart, so they go to a private bucket.
UPLOAD_BUCKET="${UPLOAD_BUCKET:-${GCP_PROJECT}-uploads}"
gc storage buckets describe "gs://$UPLOAD_BUCKET" >/dev/null 2>&1 || \
  gc storage buckets create "gs://$UPLOAD_BUCKET" --location="$GCP_REGION" --uniform-bucket-level-access
gc storage buckets add-iam-policy-binding "gs://$UPLOAD_BUCKET" --member="serviceAccount:$RUN_SA" \
  --role=roles/storage.objectAdmin >/dev/null
fi  # DO_INFRA

# Deploy settings from Terraform state (or directly query GCP if terraform state is uninitialized)
GOOGLE_OAUTH_ACCESS_TOKEN="$(gcloud auth print-access-token)"
export GOOGLE_OAUTH_ACCESS_TOKEN
DB_CONN=""
RUN_SA=""
if [ -d "$ROOT/terraform/gcp" ] && command -v terraform >/dev/null 2>&1; then
  cd "$ROOT/terraform/gcp"
  terraform init -input=false >/dev/null 2>&1 || true
  DB_CONN=$(terraform output -raw postgres_connection_name 2>/dev/null || true)
  RUN_SA=$(terraform output -raw run_service_account 2>/dev/null || true)
  cd "$ROOT"
fi

if [ -z "$DB_CONN" ]; then
  DB_CONN=$(gc sql instances describe "cropsense-postgres-db" --format='value(connectionName)' 2>/dev/null || echo "${GCP_PROJECT}:${GCP_REGION}:cropsense-postgres-db")
fi
if [ -z "$RUN_SA" ]; then
  RUN_SA="cropsense-run-sa@${GCP_PROJECT}.iam.gserviceaccount.com"
fi
UPLOAD_BUCKET="${UPLOAD_BUCKET:-${GCP_PROJECT}-uploads}"


# ── 6. Database schema (first deploy only) ───────────────────────────────────
if $DO_INFRA || $DO_BACKEND; then
step "6/9  Database schema"
TF_VAR_db_password="${TF_VAR_db_password:-$(gc secrets versions access latest --secret=cropsense-db-password)}"
PSQL=$(command -v psql || echo /opt/homebrew/opt/libpq/bin/psql)
if [ -x "$PSQL" ] && command -v cloud-sql-proxy >/dev/null; then
  # Keep the proxy's log: when psql says "server closed the connection", the reason is in here
  PROXY_LOG="$(mktemp -t cloud-sql-proxy.XXXXXX)"
  cloud-sql-proxy --port 55432 --token "$GOOGLE_OAUTH_ACCESS_TOKEN" "$DB_CONN" >"$PROXY_LOG" 2>&1 &
  PROXY_PID=$!
  trap 'kill $PROXY_PID 2>/dev/null || true' EXIT
  export PGPASSWORD="$TF_VAR_db_password"
  PSQL_ARGS=(-h 127.0.0.1 -p 55432 -U "$DB_USER" -d "$DB_NAME" -v ON_ERROR_STOP=1)
  show_proxy_log() { warn "cloud-sql-proxy log ($PROXY_LOG):"; tail -n 20 "$PROXY_LOG" >&2 || true; }
  # Wait until the proxy really accepts connections (up to 30 s) instead of a fixed sleep
  for _ in $(seq 1 30); do
    "$PSQL" "${PSQL_ARGS[@]}" -Atc "select 1" >/dev/null 2>&1 && break
    kill -0 $PROXY_PID 2>/dev/null || { show_proxy_log; die "cloud-sql-proxy exited"; }
    sleep 1
  done
  if [ "$("$PSQL" "${PSQL_ARGS[@]}" -Atc "select to_regclass('public.users') is not null")" = "t" ]; then
    echo "Schema already loaded — skipping (apply changes with a migration in database/migrations/)."
  else
    { echo "CREATE EXTENSION IF NOT EXISTS vector;"; cat database/structure.sql; echo
      cat database/relation.sql; echo; cat database/insert.sql; echo; } \
      | "$PSQL" "${PSQL_ARGS[@]}" --single-transaction -q -f -
    echo "Schema loaded."
  fi
  # Idempotent (CREATE ... IF NOT EXISTS) — safe to run on every deploy.
  # All in ONE connection (a small Cloud SQL instance shared with the live backend
  # can drop new connections), retried because every file is safe to re-run.
  MIGRATIONS=(
    database/migrations/create_push_subscriptions_table.sql
    database/migrations/2026-09-27-services-livestock-name.sql
    database/migrations/2026-09-27-crops-supporting-crop.sql
    database/migrations/2026-09-27-ndap-ingestion-tables.sql
    database/migrations/2026-09-27-voice-assist-logs.sql
    database/migrations/2026-09-27-crop-diagnoses.sql
    database/migrations/2026-09-27-satellite-observations.sql
  )
  EXISTING_MIGRATIONS=()
  for f in "${MIGRATIONS[@]}"; do
    [ -f "$f" ] && EXISTING_MIGRATIONS+=("$f")
  done
  if [ ${#EXISTING_MIGRATIONS[@]} -gt 0 ]; then
    migrated=false
    for attempt in 1 2 3; do
      if for f in "${EXISTING_MIGRATIONS[@]}"; do cat "$f"; echo; done | "$PSQL" "${PSQL_ARGS[@]}" -q -f -; then migrated=true; break; fi
      warn "Migrations failed (attempt $attempt/3) — retrying in 5 s"
      show_proxy_log
      sleep 5
    done
    $migrated || die "Migrations failed 3 times — see the proxy log above"
    echo "Migrations applied (${#EXISTING_MIGRATIONS[@]} files)."
  else
    echo "No pending migration files found — database up to date."
  fi
  kill $PROXY_PID 2>/dev/null || true; trap - EXIT

else
  warn "psql/cloud-sql-proxy not found — skipping schema check. First deploy needs: brew install libpq cloud-sql-proxy"
fi
fi  # DO_INFRA || DO_BACKEND

# ── 6b. Firebase (Google sign-in) web config ─────────────────────────────────
step "6b    Firebase web config (Google sign-in)"
fb_api() {  # method, url, [json body]
  curl -fsS -X "$1" -H "Authorization: Bearer $GOOGLE_OAUTH_ACCESS_TOKEN" \
    -H "x-goog-user-project: $GCP_PROJECT" -H "Content-Type: application/json" "$2" ${3:+-d "$3"}
}
FB="https://firebase.googleapis.com/v1beta1/projects/$GCP_PROJECT"
fb_api GET "$FB" >/dev/null 2>&1 || die "Firebase is not enabled on $GCP_PROJECT. Open https://console.firebase.google.com → Add project → pick $GCP_PROJECT, then Authentication → Get started → Google → Enable. Re-run this script afterwards."
WEB_APP_ID=$(fb_api GET "$FB/webApps" | python3 -c "import sys,json; a=json.load(sys.stdin).get('apps',[]); print(a[0]['appId'] if a else '')")
if [ -z "$WEB_APP_ID" ]; then
  echo "Registering Firebase web app..."
  fb_api POST "$FB/webApps" '{"displayName":"CropSense Web"}' >/dev/null
  for _ in $(seq 1 20); do
    sleep 3
    WEB_APP_ID=$(fb_api GET "$FB/webApps" | python3 -c "import sys,json; a=json.load(sys.stdin).get('apps',[]); print(a[0]['appId'] if a else '')")
    [ -n "$WEB_APP_ID" ] && break
  done
  [ -n "$WEB_APP_ID" ] || die "Firebase web app registration did not finish"
fi
FB_CONFIG=$(fb_api GET "$FB/webApps/$WEB_APP_ID/config")
FIREBASE_API_KEY=$(echo "$FB_CONFIG" | python3 -c "import sys,json; print(json.load(sys.stdin)['apiKey'])")
FIREBASE_AUTH_DOMAIN=$(echo "$FB_CONFIG" | python3 -c "import sys,json; print(json.load(sys.stdin)['authDomain'])")

# ── 7. Backend: build & deploy ───────────────────────────────────────────────
FRONTEND_URL_A="https://${FRONTEND_SERVICE}-${PROJECT_NUMBER}.${GCP_REGION}.run.app"
FRONTEND_URL_B=$(gc run services describe "$FRONTEND_SERVICE" --region="$GCP_REGION" --format='value(status.url)' 2>/dev/null || true)
ORIGINS="$FRONTEND_URL_A${FRONTEND_URL_B:+,$FRONTEND_URL_B},http://localhost:3000,http://localhost:5173"

if $DO_BACKEND; then
step "7/9  Backend (Cloud Build → Cloud Run)"
BACKEND_IMAGE="${GCP_REGION}-docker.pkg.dev/${GCP_PROJECT}/${GAR_REPO}/${BACKEND_SERVICE}:$(image_tag python)"
gc builds submit "$ROOT/python" --tag="$BACKEND_IMAGE" --timeout=1800s

# 4 uvicorn workers need ~1.1 GiB, so 1 GiB OOMs at startup.
# min-instances=1: a cold start takes ~30s, longer than the frontend waits for sign-in.
gc run deploy "$BACKEND_SERVICE" --image="$BACKEND_IMAGE" --region="$GCP_REGION" \
  --service-account="$RUN_SA" --add-cloudsql-instances="$DB_CONN" \
  --allow-unauthenticated --port=8000 --memory=2Gi --cpu=2 --min-instances=1 --max-instances=10 \
  --set-env-vars="^|^GOOGLE_CLOUD_PROJECT=$GCP_PROJECT|GOOGLE_CLOUD_REGION=$GCP_REGION|ENVIRONMENT=production|POSTGRES_SERVER=/cloudsql/$DB_CONN|POSTGRES_USER=$DB_USER|POSTGRES_DB=$DB_NAME|ALLOWED_ORIGINS=$ORIGINS|FIREBASE_PROJECT_ID=$GCP_PROJECT|FIREBASE_API_KEY=$FIREBASE_API_KEY|GCS_BUCKET=$UPLOAD_BUCKET|VAPID_SUBJECT=mailto:${VAPID_CONTACT_EMAIL:-$ACCOUNT}" \
  --set-secrets="POSTGRES_PASSWORD=cropsense-db-password:latest,SECRET_KEY=cropsense-secret-key:latest,OPENWEATHER_API_KEY=cropsense-openweather-key:latest,VAPID_PUBLIC_KEY=cropsense-vapid-public-key:latest,VAPID_PRIVATE_KEY=cropsense-vapid-private-key:latest"
else
  step "7/9  Backend — unchanged, skipped"
fi
BACKEND_URL=$(gc run services describe "$BACKEND_SERVICE" --region="$GCP_REGION" --format='value(status.url)')

# ── 8. Frontend: build & deploy ──────────────────────────────────────────────
if $DO_FRONTEND; then
step "8/9  Frontend (Vite build → nginx on Cloud Run)"
cd "$ROOT/solidjs"
[ -d node_modules ] || npm ci
VITE_API_URL="$BACKEND_URL" VITE_ENV=production \
  VITE_FIREBASE_API_KEY="$FIREBASE_API_KEY" VITE_FIREBASE_AUTH_DOMAIN="$FIREBASE_AUTH_DOMAIN" \
  VITE_FIREBASE_PROJECT_ID="$GCP_PROJECT" \
  VITE_DEMO_EMAIL="${DEMO_EMAIL:-}" VITE_DEMO_PASSWORD="${DEMO_PASSWORD:-}" \
  VITE_VAPID_PUBLIC_KEY="$(gc secrets versions access latest --secret=cropsense-vapid-public-key)" npx vite build
FRONTEND_IMAGE="${GCP_REGION}-docker.pkg.dev/${GCP_PROJECT}/${GAR_REPO}/${FRONTEND_SERVICE}:$(image_tag solidjs)"
gc builds submit . --tag="$FRONTEND_IMAGE"
gc run deploy "$FRONTEND_SERVICE" --image="$FRONTEND_IMAGE" --region="$GCP_REGION" \
  --allow-unauthenticated --port=8080 --memory=256Mi --cpu=1 --min-instances=0 --max-instances=5
cd "$ROOT"
else
  step "8/9  Frontend — unchanged, skipped"
fi

if $DO_INFRA || $DO_FRONTEND; then

# The service's second URL only exists after its first deploy; make sure CORS allows it.
FRONTEND_URL_B=$(gc run services describe "$FRONTEND_SERVICE" --region="$GCP_REGION" --format='value(status.url)')
case "$ORIGINS" in
  *"$FRONTEND_URL_B"*) ;;
  *) gc run services update "$BACKEND_SERVICE" --region="$GCP_REGION" \
       --update-env-vars="^|^ALLOWED_ORIGINS=$FRONTEND_URL_A,$FRONTEND_URL_B,http://localhost:3000,http://localhost:5173" ;;
esac

# Google sign-in only works from domains Firebase Auth trusts; add the Cloud Run frontend URLs.
IDT="https://identitytoolkit.googleapis.com/admin/v2/projects/$GCP_PROJECT/config"
DOMAINS=$(fb_api GET "$IDT" | python3 -c "
import sys, json
want = sys.argv[1:]
have = json.load(sys.stdin).get('authorizedDomains', [])
print(json.dumps({'authorizedDomains': have + [d for d in want if d not in have]}))
" "${FRONTEND_URL_A#https://}" "${FRONTEND_URL_B#https://}")
fb_api PATCH "$IDT?updateMask=authorizedDomains" "$DOMAINS" >/dev/null && echo "Authorized sign-in domains updated"

# Phone OTP: Firebase refuses to send SMS (surfacing as auth/internal-error) to regions not on this list.
SMS_REGIONS="${SMS_REGIONS:-IN}"
SMS_BODY=$(python3 -c "
import sys, json
print(json.dumps({'smsRegionConfig': {'allowlistOnly': {'allowedRegions': [r.strip() for r in sys.argv[1].split(',') if r.strip()]}}}))
" "$SMS_REGIONS")
fb_api PATCH "$IDT?updateMask=smsRegionConfig" "$SMS_BODY" >/dev/null && echo "SMS regions allowed: $SMS_REGIONS"
fi  # DO_INFRA || DO_FRONTEND

# ── 9. Smoke test ─────────────────────────────────────────────────────────────
step "9/9  Health check"
curl -fsS -m 60 "${BACKEND_URL}/health" >/dev/null || \
  die "Backend health check failed — logs: gcloud run services logs read $BACKEND_SERVICE --region=$GCP_REGION --project=$GCP_PROJECT"
curl -fsS -m 60 -o /dev/null "${FRONTEND_URL_A}/" || die "Frontend did not respond"
echo "Deployed: infra=$DO_INFRA backend=$DO_BACKEND frontend=$DO_FRONTEND"

echo -e "\n${GREEN}═══════════════════════════════════════════════${NC}"
echo -e "${GREEN}  ✓ CropSense AI deployed${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════${NC}"
echo "  Frontend : $FRONTEND_URL_A"
echo "  Backend  : $BACKEND_URL"
