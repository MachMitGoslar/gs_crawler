#!/bin/bash
# Interactive script to add a new crawler configuration
# Usage: ./scripts/add-crawler.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "Add New Crawler Configuration"
echo "=============================="
echo ""

# Get crawler ID
read -p "Crawler ID (e.g., 060_mysite): " CRAWLER_ID
if [ -z "$CRAWLER_ID" ]; then
    echo "Error: Crawler ID is required"
    exit 1
fi

# Get crawler name
read -p "Crawler name (e.g., My Site News): " CRAWLER_NAME
CRAWLER_NAME="${CRAWLER_NAME:-$CRAWLER_ID}"

# Get URL
read -p "Target URL: " CRAWLER_URL
if [ -z "$CRAWLER_URL" ]; then
    echo "Error: URL is required"
    exit 1
fi

# Get schedule
read -p "Cron schedule [0 9 * * *]: " CRAWLER_SCHEDULE
CRAWLER_SCHEDULE="${CRAWLER_SCHEDULE:-0 9 * * *}"

# Get container selector
read -p "Container CSS selector (e.g., article.post): " CONTAINER_SELECTOR
if [ -z "$CONTAINER_SELECTOR" ]; then
    echo "Error: Container selector is required"
    exit 1
fi

# Get title selector
read -p "Title selector (relative to container, e.g., h2 a): " TITLE_SELECTOR
TITLE_SELECTOR="${TITLE_SELECTOR:-h2 a}"

# Get description selector
read -p "Description selector [p]: " DESC_SELECTOR
DESC_SELECTOR="${DESC_SELECTOR:-p}"

# Get image selector
read -p "Image selector [img]: " IMG_SELECTOR
IMG_SELECTOR="${IMG_SELECTOR:-img}"

# Get link selector
read -p "Link selector [a]: " LINK_SELECTOR
LINK_SELECTOR="${LINK_SELECTOR:-a}"

# Select type
echo ""
echo "Config location:"
echo "  1) simple (standard BeautifulSoup scrapers)"
echo "  2) tschuessschule (nested structure)"
read -p "Select [1]: " CONFIG_TYPE
CONFIG_TYPE="${CONFIG_TYPE:-1}"

if [ "$CONFIG_TYPE" == "1" ]; then
    CONFIG_DIR="$PROJECT_ROOT/crawler_configs/simple"
else
    CONFIG_DIR="$PROJECT_ROOT/crawler_configs/tschuessschule"
fi

CONFIG_FILE="$CONFIG_DIR/${CRAWLER_ID}.yaml"

# Generate config file
cat > "$CONFIG_FILE" << EOF
# ${CRAWLER_NAME}
id: "${CRAWLER_ID}"
name: "${CRAWLER_NAME}"

url: "${CRAWLER_URL}"
base_url: "${CRAWLER_URL}"

schedule: "${CRAWLER_SCHEDULE}"
run_on_start: true

selectors:
  container: "${CONTAINER_SELECTOR}"

  title:
    selector: "${TITLE_SELECTOR}"
    attribute: "text"

  description:
    selector: "${DESC_SELECTOR}"
    attribute: "text"

  image_url:
    selector: "${IMG_SELECTOR}"
    attribute: "src"

  call_to_action_url:
    selector: "${LINK_SELECTOR}"
    attribute: "href"

output:
  single:
    enabled: true
    filename: "${CRAWLER_ID}.json"
    cta_override: "https://crawler.goslar.app/crawler/${CRAWLER_ID}-alle.json"

  all:
    enabled: true
    filename: "${CRAWLER_ID}-alle.json"

selection:
  strategy: "random"
EOF

echo ""
echo "Created config file: $CONFIG_FILE"
echo ""
echo "Test it with:"
echo "  ./scripts/test-scraper-local.sh $CRAWLER_ID"
