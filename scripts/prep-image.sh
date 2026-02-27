#!/bin/bash
#
# Download, compress, and prepare an image for Time Slices.
# Outputs JSON snippet with dimensions ready to paste into entry.
#
# Usage:
#   ./scripts/prep-image.sh <source_url_or_path> <entry_id> [alt_text]
#
# Examples:
#   ./scripts/prep-image.sh https://example.com/image.jpg 1504-florence "David by Michelangelo"
#   ./scripts/prep-image.sh /tmp/downloaded.png 1687-london "Newton's Principia"
#
# Output:
#   - Saves compressed image to images/<entry_id>.jpg
#   - Prints JSON snippet with url, alt, width, height

set -e

if [ $# -lt 2 ]; then
    echo "Usage: $0 <source_url_or_path> <entry_id> [alt_text]" >&2
    exit 1
fi

SOURCE="$1"
ENTRY_ID="$2"
ALT_TEXT="${3:-}"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
IMAGES_DIR="$PROJECT_DIR/images"
OUTPUT="$IMAGES_DIR/$ENTRY_ID.jpg"

mkdir -p "$IMAGES_DIR"

# Download if URL, otherwise use local path
if [[ "$SOURCE" =~ ^https?:// ]]; then
    echo "⬇️  Downloading..."
    TMP_FILE=$(mktemp /tmp/prep-image-XXXXXX)
    curl -sL "$SOURCE" -o "$TMP_FILE"
    SOURCE="$TMP_FILE"
    CLEANUP=1
else
    CLEANUP=0
fi

# Compress: max 1200px width, quality 85
echo "🔧 Compressing..."
convert "$SOURCE" -resize '1200x>' -quality 85 "$OUTPUT"

# Cleanup temp file if we downloaded
if [ "$CLEANUP" -eq 1 ]; then
    rm -f "$TMP_FILE"
fi

# Get dimensions
DIMS=$(identify -format '%w %h' "$OUTPUT")
WIDTH=$(echo "$DIMS" | cut -d' ' -f1)
HEIGHT=$(echo "$DIMS" | cut -d' ' -f2)
SIZE=$(du -h "$OUTPUT" | cut -f1)

echo ""
echo "✅ Saved: images/$ENTRY_ID.jpg ($SIZE, ${WIDTH}x${HEIGHT})"
echo ""
echo "📋 Image JSON:"
echo "  \"image\": {"
echo "    \"url\": \"images/$ENTRY_ID.jpg\","
if [ -n "$ALT_TEXT" ]; then
    echo "    \"alt\": \"$ALT_TEXT\","
else
    echo "    \"alt\": \"<describe the image>\","
fi
echo "    \"width\": $WIDTH,"
echo "    \"height\": $HEIGHT"
echo "  }"
