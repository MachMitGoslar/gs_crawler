"""
Config loader for generic scraper.
Handles YAML config parsing.
"""
import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional


CONFIG_DIR = os.environ.get('CONFIG_DIR', '/app/configs')


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
            'regex': selector_def.get('regex'),
            'date_format': selector_def.get('date_format'),
            'fallback': selector_def.get('fallback'),
            'default': selector_def.get('default'),
            'template': selector_def.get('template'),
            'item_id_attribute': selector_def.get('item_id_attribute')
        }

    return {'selector': '', 'attribute': 'text', 'prefix': '', 'fallback': None}
