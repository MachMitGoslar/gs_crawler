# Crawler Configuration Schema

This document describes the YAML configuration schema for generic crawlers.

## Basic Structure

```yaml
# Crawler identification
id: "002_gz"                    # Unique identifier (used in output filenames)
name: "Goslarsche Zeitung"      # Human-readable name

# Target configuration
url: "https://example.com/page"
base_url: "https://example.com" # Optional: for relative URL resolution

# Scheduling (cron format)
schedule: "0 * * * *"           # Hourly
run_on_start: true              # Execute immediately on container start

# Selectors - CSS selectors for data extraction
selectors:
  # Container selector - the repeating element containing each item
  container: "article.StoryPreviewBox"

  # Field selectors (relative to container)
  title:
    selector: "h2.article-heading a"
    attribute: "text"           # text, href, src, or any attribute

  description:
    selector: "div.article-preview"
    attribute: "text"

  image_url:
    selector: "div.PictureContainer img"
    attribute: "src"
    prefix: ""                  # Optional: prepend to value

  call_to_action_url:
    selector: "h2.article-heading a"
    attribute: "href"
    prefix: ""                  # Optional: prepend to value

# Output configuration
output:
  single:
    enabled: true
    filename: "002_goslarsche.json"
    # For single output, redirect CTA to the "all" file
    cta_override: "https://crawler.goslar.app/crawler/{all_filename}"

  all:
    enabled: true
    filename: "002_goslarsche-alle.json"

# Selection strategy for single output
selection:
  strategy: "first"             # first, random, latest

# Post-processing
post_process:
  # Modify description for single output
  single_description_prefix: ""  # e.g., "{count} Angebote, z. B.\n\n"

  # Date parsing (optional)
  date_format: "%d.%m.%Y"       # German date format
  date_selector: "span.date"

  # URL handling
  resolve_relative_urls: true   # Resolve relative URLs using base_url
```

## Field Selector Options

### Basic selector
```yaml
title:
  selector: "h2 a"
  attribute: "text"
```

### With prefix/suffix
```yaml
image_url:
  selector: "img"
  attribute: "src"
  prefix: "https://example.com"
```

### Nested selectors (for complex structures)
```yaml
title:
  selector: "div.container h3"
  fallback: "Default Title"     # Use if selector returns nothing
```

## Selection Strategies

- `first`: Always pick the first item
- `random`: Pick a random item from all scraped items
- `latest`: Pick based on date (requires date_selector)

## Examples

See individual crawler configs in this directory for real-world examples.
