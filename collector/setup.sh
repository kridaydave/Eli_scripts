#!/usr/bin/env bash
set -euo pipefail
pip3 install -r "$(dirname "$0")/requirements.txt"
echo "Dependencies installed."
