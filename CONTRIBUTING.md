# Contributing to GS Crawler

## Local Development Setup

### Prerequisites

- Docker Desktop (with Docker Compose v2)
- Python 3.13+ (for running tests without Docker)
- Git

### Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/MachMitGoslar/gs_crawler.git
cd gs_crawler

# 2. First-time setup (builds base images locally)
./scripts/dev.sh setup

# 3. Start all containers
./scripts/dev.sh up

# 4. View logs
./scripts/dev.sh logs
```

### Development Commands

| Command | Description |
|---------|-------------|
| `./scripts/dev.sh setup` | First-time setup - builds all base images locally |
| `./scripts/dev.sh up` | Start all containers |
| `./scripts/dev.sh down` | Stop all containers |
| `./scripts/dev.sh logs` | Follow all logs |
| `./scripts/dev.sh logs <service>` | Follow logs for specific service |
| `./scripts/dev.sh build` | Rebuild all containers |
| `./scripts/dev.sh ps` | Show running containers |
| `./scripts/dev.sh test` | Run scraper tests (no Docker needed) |
| `./scripts/dev.sh shell <service>` | Open shell in container |
| `./scripts/dev.sh restart` | Restart all containers |

### Testing Without Docker

For faster iteration on scraper configs, you can test without Docker:

```bash
# Test a single config
./scripts/test-scraper-local.sh 002_gz

# Test all configs
./scripts/test-all-configs.sh
```

This runs the Python scraper directly and outputs to `test_output/`.

### Adding a New Crawler

#### Option 1: Config-Driven (Recommended for simple scrapers)

```bash
# Interactive wizard
./scripts/add-crawler.sh

# Or manually create a YAML config in crawler_configs/simple/
```

See [crawler_configs/schema.md](crawler_configs/schema.md) for config format.

#### Option 2: Custom Container (For complex scrapers)

1. Create directory: `docker_instances/XXX_name/`
2. Add `Dockerfile`, `script.py`, `crontab`
3. Add service to `compose.dev.yaml`
4. Run `./scripts/dev.sh build`

### Project Structure

```
gs_crawler/
├── base_images/              # Docker base images
│   ├── python_basic_crawler/ # Standard Python crawler
│   ├── python_selenium_crawler/ # Browser automation
│   ├── generic_scraper/      # Config-driven scraper engine
│   └── ...
├── crawler_configs/          # YAML configs for generic scraper
│   ├── simple/               # Simple BeautifulSoup scrapers
│   └── tschuessschule/       # Nested structure scrapers
├── docker_instances/         # Custom container implementations
├── scripts/                  # Development scripts
├── httpdocs/crawler/         # Output directory (gitignored)
├── compose.dev.yaml          # Local development
├── compose.yaml              # Production (pre-built images)
└── compose.consolidated.yaml # New consolidated architecture
```

### Ports

| Port | Service |
|------|---------|
| 5015 | Health Monitor Dashboard |
| 5016 | Altstadtfest API |

### Output Files

Crawler output is written to `httpdocs/crawler/`. This directory is:
- Mounted as a volume in all containers
- Gitignored (not committed)
- Accessible via the Health Monitor at http://localhost:5015

### Troubleshooting

#### "Base images not found"
Run `./scripts/dev.sh setup` to build base images locally.

#### Container won't start
Check logs: `./scripts/dev.sh logs <service_name>`

#### Changes not reflected
Rebuild the specific container:
```bash
docker compose -f compose.dev.yaml build <service_name>
docker compose -f compose.dev.yaml up -d <service_name>
```

### Code Style

- Python: Follow existing patterns in the codebase
- YAML configs: Use 2-space indentation
- Commit messages: Use conventional commits (feat:, fix:, chore:, etc.)

### Pull Request Process

1. Create a feature branch from `main`
2. Make your changes
3. Test locally with `./scripts/dev.sh test`
4. Push and create a PR
5. CI will run automated tests
