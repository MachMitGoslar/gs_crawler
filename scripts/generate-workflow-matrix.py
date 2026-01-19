#!/usr/bin/env python3
"""
Generate GitHub Actions workflow matrix data from crawlers.yaml registry.

This script outputs JSON data that can be used in GitHub Actions workflows
to dynamically build the list of containers, expected files, etc.

Usage:
    python scripts/generate-workflow-matrix.py --containers    # List all container IDs
    python scripts/generate-workflow-matrix.py --custom        # List custom container IDs
    python scripts/generate-workflow-matrix.py --config-dirs   # List config directories
    python scripts/generate-workflow-matrix.py --expected-files # Map of container -> expected files
    python scripts/generate-workflow-matrix.py --base-images   # List base images
"""

import argparse
import json
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("Error: PyYAML not installed", file=sys.stderr)
    sys.exit(1)

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
REGISTRY_FILE = PROJECT_ROOT / "crawlers.yaml"


def load_registry():
    """Load the crawler registry."""
    with open(REGISTRY_FILE, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def get_all_containers(registry):
    """Get all container IDs (custom implementation only)."""
    containers = []
    for crawler in registry['crawlers']:
        if crawler.get('implementation') == 'custom':
            cid = crawler['id']
            # Map to directory name
            if cid == '002_ferienpass':
                containers.append('002_ferienpass')
            else:
                containers.append(cid)
    return containers


def get_custom_containers(registry):
    """Get custom container IDs that have docker_instances directories."""
    return get_all_containers(registry)


def get_config_dirs(registry):
    """Get unique config directories used by config-driven crawlers."""
    dirs = set()
    for crawler in registry['crawlers']:
        if crawler.get('implementation') == 'config':
            dirs.add(crawler.get('config_dir', 'simple'))
    return sorted(dirs)


def get_expected_files(registry):
    """Get mapping of crawler ID to expected output files."""
    files = {}
    for crawler in registry['crawlers']:
        cid = crawler['id']
        expected = crawler.get('expected_files', [])
        if expected:
            files[cid] = expected
    return files


def get_base_images():
    """Get list of base images from base_images directory."""
    base_dir = PROJECT_ROOT / "base_images"
    images = []
    for d in base_dir.iterdir():
        if d.is_dir() and (d / "Dockerfile").exists():
            images.append(d.name)
    return sorted(images)


def main():
    parser = argparse.ArgumentParser(description='Generate workflow matrix data')
    parser.add_argument('--containers', action='store_true', help='List all container IDs')
    parser.add_argument('--custom', action='store_true', help='List custom container IDs')
    parser.add_argument('--config-dirs', action='store_true', help='List config directories')
    parser.add_argument('--expected-files', action='store_true', help='Map of expected files')
    parser.add_argument('--base-images', action='store_true', help='List base images')
    parser.add_argument('--all', action='store_true', help='Output all data as JSON object')

    args = parser.parse_args()

    registry = load_registry()

    if args.all:
        data = {
            'containers': get_all_containers(registry),
            'custom_containers': get_custom_containers(registry),
            'config_dirs': get_config_dirs(registry),
            'expected_files': get_expected_files(registry),
            'base_images': get_base_images(),
        }
        print(json.dumps(data, indent=2))
    elif args.containers:
        print(json.dumps(get_all_containers(registry)))
    elif args.custom:
        print(json.dumps(get_custom_containers(registry)))
    elif args.config_dirs:
        print(json.dumps(get_config_dirs(registry)))
    elif args.expected_files:
        print(json.dumps(get_expected_files(registry), indent=2))
    elif args.base_images:
        print(json.dumps(get_base_images()))
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
