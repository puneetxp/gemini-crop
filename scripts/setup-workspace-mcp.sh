#!/usr/bin/env bash
# Configure Google Workspace remote MCP servers for Claude Code.
# Ref: https://developers.google.com/workspace/guides/configure-mcp-servers
#
# Prereq (manual, Cloud Console — cannot be scripted):
#   1. APIs & Services > OAuth consent screen: configure (add yourself as test user).
#   2. Credentials > Create OAuth client ID > "Web application"
#      Authorized redirect URIs:
#        http://localhost:8765/callback                 (Claude Code CLI / desktop)
#        https://claude.ai/api/mcp/auth_callback        (claude.ai custom connectors)
#   3. Copy the client ID + secret.
#
# Usage:
#   GCP_PROJECT=cropsense-ai-a4d5cf ./scripts/setup-workspace-mcp.sh enable
#   MCP_CLIENT_ID=xxx.apps.googleusercontent.com MCP_CLIENT_SECRET=yyy \
#     ./scripts/setup-workspace-mcp.sh add [local|user|project]
set -euo pipefail

GCP_PROJECT="${GCP_PROJECT:-cropsense-ai-a4d5cf}"
CALLBACK_PORT="${CALLBACK_PORT:-8765}"

# name  api-service  mcp-service  url
SERVERS=(
  "gmail    gmail.googleapis.com         gmailmcp.googleapis.com    https://gmailmcp.googleapis.com/mcp/v1"
  "drive    drive.googleapis.com         drivemcp.googleapis.com    https://drivemcp.googleapis.com/mcp/v1"
  "docs     docs.googleapis.com          docsmcp.googleapis.com     https://docsmcp.googleapis.com/mcp/v1"
  "sheets   sheets.googleapis.com        sheetsmcp.googleapis.com   https://sheetsmcp.googleapis.com/mcp/v1"
  "slides   slides.googleapis.com        slidesmcp.googleapis.com   https://slidesmcp.googleapis.com/mcp/v1"
  "calendar calendar-json.googleapis.com calendarmcp.googleapis.com https://calendarmcp.googleapis.com/mcp/v1"
  "chat     chat.googleapis.com          chatmcp.googleapis.com     https://chatmcp.googleapis.com/mcp/v1"
  "people   people.googleapis.com        people.googleapis.com      https://people.googleapis.com/mcp/v1"
)

cmd="${1:-}"
case "$cmd" in
  enable)
    echo "gcloud: $(command -v gcloud)  account: $(gcloud config get-value account 2>/dev/null)"
    echo "Enabling Workspace APIs + MCP services on project: $GCP_PROJECT"
    services=()
    for row in "${SERVERS[@]}"; do
      read -r _ api mcp _ <<<"$row"
      services+=("$api" "$mcp")
    done
    # de-dup (people uses same service for API + MCP)
    gcloud services enable $(printf '%s\n' "${services[@]}" | sort -u) --project="$GCP_PROJECT"
    ;;
  add)
    scope="${2:-user}"
    : "${MCP_CLIENT_ID:?set MCP_CLIENT_ID}"
    : "${MCP_CLIENT_SECRET:?set MCP_CLIENT_SECRET}"
    export MCP_CLIENT_SECRET
    for row in "${SERVERS[@]}"; do
      read -r name _ _ url <<<"$row"
      claude mcp remove "google-$name" -s "$scope" >/dev/null 2>&1 || true
      claude mcp add --transport http -s "$scope" \
        --client-id "$MCP_CLIENT_ID" --client-secret --callback-port "$CALLBACK_PORT" \
        "google-$name" "$url"
    done
    echo "Done. Run /mcp in an interactive 'claude' session to authenticate each server."
    ;;
  *)
    sed -n '2,17p' "$0"; exit 1 ;;
esac
