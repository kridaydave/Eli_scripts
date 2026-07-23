#!/usr/bin/env bash
set -euo pipefail

# Upload training data to a cloud ML box (Colab, Kaggle, Lightning.ai)
#
# Usage:
#   ./upload.sh colab        # generates download link for Colab
#   ./upload.sh kaggle       # copies to Kaggle dataset mount
#   ./upload.sh lightning    # rsync to Lightning.ai instance
#   ./upload.sh all          # run all configured destinations

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$SCRIPT_DIR/.."
PROCESSED="$ROOT/processed"
CONFIG="$SCRIPT_DIR/upload-config.sh"

if [ -f "$CONFIG" ]; then
    source "$CONFIG"
fi

# Defaults
: "${DEST_COLAB:=}"           # gsutil URL or similar
: "${DEST_KAGGLE:=/kaggle/input/epoch-training}"
: "${DEST_LIGHTNING:=user@lightning-instance:~/epoch-training}"

echo "=== Epoch Training Data Upload ==="
echo "Files to upload:"
ls -lh "$PROCESSED"/*.jsonl "$PROCESSED"/dataset-stats.json 2>/dev/null || echo "  No training files yet"

upload_colab() {
    if [ -z "${DEST_COLAB}" ]; then
        echo "[colab] No DEST_COLAB configured. Generating direct download archive..."
        ARCHIVE="$ROOT/epoch-training-data.tar.gz"
        tar czf "$ARCHIVE" -C "$ROOT" processed/ eli-training-data-consolidated.txt
        echo "[colab] Archive created: $ARCHIVE ($(du -h "$ARCHIVE" | cut -f1))"
        echo "[colab] Upload to Google Drive or use wget from Colab:"
        echo "  !wget <your-url>/epoch-training-data.tar.gz"
        echo "  !tar xzf epoch-training-data.tar.gz"
    else
        echo "[colab] Uploading to $DEST_COLAB..."
        gsutil cp "$PROCESSED"/*.jsonl "$DEST_COLAB/" 2>/dev/null || \
            echo "  gsutil not available. Try manual upload."
    fi
}

upload_kaggle() {
    if [ -d "$DEST_KAGGLE" ]; then
        echo "[kaggle] Copying to $DEST_KAGGLE..."
        cp "$PROCESSED"/*.jsonl "$DEST_KAGGLE/"
        echo "[kaggle] Done."
    else
        echo "[kaggle] $DEST_KAGGLE not found. Mount Kaggle dataset first."
        echo "  Or upload manually: kaggle datasets create"
    fi
}

upload_lightning() {
    if [ -z "${DEST_LIGHTNING%%:*}" ]; then
        echo "[lightning] Rsyncing to $DEST_LIGHTNING..."
        rsync -avzP "$PROCESSED"/*.jsonl "$DEST_LIGHTNING/"
    else
        echo "[lightning] No SSH destination configured."
        echo "  Set DEST_LIGHTNING=user@host:path in upload-config.sh"
    fi
}

case "${1:-help}" in
    colab)    upload_colab ;;
    kaggle)   upload_kaggle ;;
    lightning) upload_lightning ;;
    all)
        upload_colab
        upload_kaggle
        upload_lightning
        ;;
    *)
        echo "Usage: $0 {colab|kaggle|lightning|all}"
        exit 1
        ;;
esac
