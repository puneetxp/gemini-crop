#!/usr/bin/env bash
# CropSense AI — Root Pipeline Wrapper
# Usage: ./pipeline.sh [all|check|sanitize-screens|sync-index|generate|test-backend|build-frontend]

set -e

# Prepend Node/NPM & Homebrew paths
export PATH="$HOME/.nvm/versions/node/v24.20.0/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

python3 "$DIR/scripts/pipeline.py" "$@"
