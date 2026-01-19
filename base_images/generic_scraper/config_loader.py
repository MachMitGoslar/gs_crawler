"""
Config loader for generic scraper.
Handles YAML config parsing and crontab generation.
"""
import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional


CONFIG_DIR = os.environ.get('CONFIG_DIR', '/app/configs')
CRONTAB_PATH = '/etc/cron.d/scraper'


def load_config(config_path: str) -> Dict[str, Any]:
    """Load and validate a crawler config file."""
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    # Validate required fields
    required = ['id', 'url', 'selectors', 'output']
    for field in required:
        if field not in config:
            raise ValueError(f"Missing required field '{field}' in {config_path}")

    # Set defaults
    config.setdefault('name', config['id'])
    config.setdefault('base_url', config['url'])
    config.setdefault('schedule', '0 9 * * *')  # Default: daily at 9am
    config.setdefault('run_on_start', True)
    config.setdefault('type', 'simple')
    config.setdefault('selection', {'strategy': 'random'})
    config.setdefault('post_process', {})

    return config


def load_all_configs() -> Dict[str, Dict[str, Any]]:
    """Load all config files from CONFIG_DIR."""
    configs = {}
    config_dir = Path(CONFIG_DIR)

    if not config_dir.exists():
        print(f"Warning: Config directory {CONFIG_DIR} does not exist")
        return configs

    for config_file in config_dir.glob('*.yaml'):
        try:
            config = load_config(str(config_file))
            configs[config['id']] = config
            configs[config['id']]['_path'] = str(config_file)
            print(f"Loaded config: {config['id']} from {config_file.name}")
        except Exception as e:
            print(f"Error loading {config_file}: {e}")

    return configs


def generate_crontab():
    """Generate crontab file from all configs."""
    configs = load_all_configs()

    if not configs:
        print("No configs found, skipping crontab generation")
        return

    cron_lines = [
        "# Auto-generated crontab for generic scraper",
        "# Do not edit manually - regenerated on container start",
        "",
        "SHELL=/bin/sh",
        "PATH=/usr/local/bin:/usr/bin:/bin",
        ""
    ]

    for crawler_id, config in configs.items():
        schedule = config.get('schedule', '0 9 * * *')
        config_path = config['_path']

        # Cron line format: schedule command
        cron_line = f"{schedule} cd /app && python3 scraper.py {config_path} >> /var/log/cron/scraper.log 2>&1"
        cron_lines.append(f"# {config.get('name', crawler_id)}")
        cron_lines.append(cron_line)
        cron_lines.append("")

    # Write crontab
    crontab_content = '\n'.join(cron_lines) + '\n'

    with open(CRONTAB_PATH, 'w') as f:
        f.write(crontab_content)

    # Set permissions and install crontab
    os.chmod(CRONTAB_PATH, 0o644)
    os.system(f'crontab {CRONTAB_PATH}')

    print(f"Generated crontab with {len(configs)} crawlers")


def get_selector_config(selectors: Dict, field: str) -> Dict[str, Any]:
    """Get selector config for a field, handling both simple and complex formats."""
    selector_def = selectors.get(field, {})

    if isinstance(selector_def, str):
        # Simple format: just the CSS selector
        return {
            'selector': selector_def,
            'attribute': 'text',
            'prefix': '',
            'fallback': None
        }
    elif isinstance(selector_def, dict):
        # Complex format with options
        return {
            'selector': selector_def.get('selector', ''),
            'attribute': selector_def.get('attribute', 'text'),
            'prefix': selector_def.get('prefix', ''),
            'fallback': selector_def.get('fallback'),
            'default': selector_def.get('default'),
            'template': selector_def.get('template'),
            'item_id_attribute': selector_def.get('item_id_attribute')
        }

    return {'selector': '', 'attribute': 'text', 'prefix': '', 'fallback': None}


if __name__ == '__main__':
    # When run directly, generate crontab
    generate_crontab()
