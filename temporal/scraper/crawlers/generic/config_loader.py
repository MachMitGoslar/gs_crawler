import logging

from crawlers.generic.models import GenericCrawlerConfig
from pathlib import Path
import yaml

def load_all_configs(config_dir: Path) -> dict[str, GenericCrawlerConfig]:
    configs: dict[str, GenericCrawlerConfig] = {}
    for config_file in config_dir.glob("*.yaml"):
        with open(config_file) as f:
            cfg = GenericCrawlerConfig.model_validate(yaml.safe_load(f))
        if cfg.id in configs:
            logging.warning(f"Warning: duplicate config id '{cfg.id}' ({config_file})")
        configs[cfg.id] = cfg
        logging.info(f"Loaded config: {cfg.id} from {config_file.name}")

    return configs