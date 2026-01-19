#!/usr/bin/env python3
"""
Test crawlers locally without Docker.

Usage:
    python scripts/test-crawler.py                    # List all crawlers
    python scripts/test-crawler.py 002_gz            # Test single crawler
    python scripts/test-crawler.py --all             # Test all crawlers
    python scripts/test-crawler.py --config          # Test only config-driven
    python scripts/test-crawler.py --custom          # Test only custom crawlers
    python scripts/test-crawler.py --category news   # Test by category
"""

import argparse
import os
import sys
import subprocess
import json
from pathlib import Path
from datetime import datetime

# Add colors for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

try:
    import yaml
except ImportError:
    print("PyYAML not installed. Run: pip3 install pyyaml")
    sys.exit(1)

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
REGISTRY_FILE = PROJECT_ROOT / "crawlers.yaml"
TEST_OUTPUT_DIR = PROJECT_ROOT / "test_output"
GENERIC_SCRAPER_DIR = PROJECT_ROOT / "base_images" / "generic_scraper"


def load_registry():
    """Load the crawler registry."""
    with open(REGISTRY_FILE, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def get_venv_python():
    """Get or create virtual environment for generic scraper."""
    venv_path = GENERIC_SCRAPER_DIR / ".venv"
    python_path = venv_path / "bin" / "python"

    if not venv_path.exists():
        print(f"{Colors.YELLOW}Creating virtual environment...{Colors.RESET}")
        subprocess.run([sys.executable, "-m", "venv", str(venv_path)], check=True)
        subprocess.run([
            str(venv_path / "bin" / "pip"), "install", "-r",
            str(GENERIC_SCRAPER_DIR / "requirements.txt")
        ], check=True)

    return str(python_path)


def test_config_crawler(crawler, venv_python):
    """Test a config-driven crawler."""
    config_dir = crawler.get('config_dir', 'simple')
    config_path = PROJECT_ROOT / "crawler_configs" / config_dir / f"{crawler['id']}.yaml"

    if not config_path.exists():
        return False, f"Config file not found: {config_path}"

    env = os.environ.copy()
    env['OUTPUT_DIR'] = str(TEST_OUTPUT_DIR)

    try:
        result = subprocess.run(
            [venv_python, "scraper.py", str(config_path)],
            cwd=str(GENERIC_SCRAPER_DIR),
            env=env,
            capture_output=True,
            text=True,
            timeout=120
        )

        if result.returncode != 0:
            return False, result.stderr or result.stdout

        # Check if expected files were created
        expected_files = crawler.get('expected_files', [])
        missing = []
        for f in expected_files:
            if not (TEST_OUTPUT_DIR / f).exists():
                missing.append(f)

        if missing:
            return False, f"Missing output files: {', '.join(missing)}"

        return True, result.stdout

    except subprocess.TimeoutExpired:
        return False, "Timeout after 120 seconds"
    except Exception as e:
        return False, str(e)


def get_base_image_requirements(docker_dir):
    """Determine requirements file based on Dockerfile base image."""
    dockerfile = docker_dir / "Dockerfile"
    if not dockerfile.exists():
        return None

    try:
        content = dockerfile.read_text()
        if "python_basic_crawler" in content:
            return PROJECT_ROOT / "base_images" / "python_basic_crawler" / "requirements.txt"
        elif "python_selenium_crawler" in content:
            return PROJECT_ROOT / "base_images" / "python_selenium_crawler" / "requirements.txt"
        elif "flask_monitor" in content:
            return PROJECT_ROOT / "base_images" / "flask_monitor" / "requirements.txt"
        elif "generic_scraper" in content:
            return PROJECT_ROOT / "base_images" / "generic_scraper" / "requirements.txt"
    except Exception:
        pass

    return None


def test_custom_crawler(crawler):
    """Test a custom container crawler by running its script directly."""
    crawler_id = crawler['id']

    # Special case for ferienpass
    if crawler_id == '002_ferienpass':
        docker_dir = PROJECT_ROOT / "docker_instances" / "002_ferienpass"
    else:
        docker_dir = PROJECT_ROOT / "docker_instances" / crawler_id

    if not docker_dir.exists():
        return False, f"Directory not found: {docker_dir}"

    script_path = docker_dir / "script.py"
    if not script_path.exists():
        # Check for alternative scripts
        for alt in ["app.py", "main.py"]:
            alt_path = docker_dir / alt
            if alt_path.exists():
                script_path = alt_path
                break
        else:
            return None, "No Python script found (skip)"

    # Check for requirements - local first, then base image
    requirements_path = docker_dir / "requirements.txt"
    if not requirements_path.exists():
        requirements_path = get_base_image_requirements(docker_dir)

    venv_path = docker_dir / ".venv"

    venv_python = venv_path / "bin" / "python"

    if requirements_path and requirements_path.exists():
        # Check if venv exists and is complete
        if not venv_python.exists():
            print(f"  {Colors.YELLOW}Creating venv for {crawler_id}...{Colors.RESET}")
            try:
                # Remove incomplete venv if exists
                if venv_path.exists():
                    import shutil
                    shutil.rmtree(venv_path)
                subprocess.run([sys.executable, "-m", "venv", str(venv_path)], check=True)
                subprocess.run([
                    str(venv_python), "-m", "pip", "install", "-q", "-r", str(requirements_path)
                ], check=True, capture_output=True)
            except Exception as e:
                return False, f"Failed to create venv: {e}"
        python_path = str(venv_python)
    elif venv_python.exists():
        # Use existing complete venv
        python_path = str(venv_python)
    else:
        python_path = sys.executable

    env = os.environ.copy()
    env['OUTPUT_DIR'] = str(TEST_OUTPUT_DIR)

    # Many custom scripts use hardcoded ./output/ path
    # Create symlink from docker_dir/output to test_output
    local_output = docker_dir / "output"
    symlink_created = False
    if not local_output.exists():
        try:
            local_output.symlink_to(TEST_OUTPUT_DIR)
            symlink_created = True
        except Exception:
            pass

    try:
        result = subprocess.run(
            [python_path, str(script_path)],
            cwd=str(docker_dir),
            env=env,
            capture_output=True,
            text=True,
            timeout=180
        )

        if result.returncode != 0:
            error_msg = result.stderr or result.stdout
            # Some scripts exit with errors due to missing dependencies (selenium, etc)
            if "selenium" in error_msg.lower() or "chrome" in error_msg.lower():
                return None, "Requires Selenium (skip)"
            if "firefox" in error_msg.lower() or "geckodriver" in error_msg.lower():
                return None, "Requires Firefox/geckodriver (skip)"
            return False, error_msg[:500]

        # Check if expected files were created
        expected_files = crawler.get('expected_files', [])
        if expected_files:
            found = 0
            for f in expected_files:
                # Check both test_output and local output dir
                if (TEST_OUTPUT_DIR / f).exists():
                    found += 1
                elif (local_output / f).exists():
                    found += 1
            if found == 0:
                return False, "No expected output files created"

        return True, "Success"

    except subprocess.TimeoutExpired:
        return False, "Timeout after 180 seconds"
    except Exception as e:
        return False, str(e)


def list_crawlers(registry):
    """List all available crawlers."""
    crawlers = registry['crawlers']
    categories = registry['categories']

    print(f"\n{Colors.BOLD}Available Crawlers ({len(crawlers)} total){Colors.RESET}\n")

    # Group by category
    by_category = {}
    for crawler in crawlers:
        cat = crawler['category']
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(crawler)

    for cat_id, cat_info in categories.items():
        cat_crawlers = by_category.get(cat_id, [])
        if not cat_crawlers:
            continue

        print(f"{Colors.BLUE}{cat_info['name']}{Colors.RESET}")
        for crawler in cat_crawlers:
            impl = crawler.get('implementation', 'unknown')
            impl_badge = f"[config]" if impl == 'config' else f"[custom]"
            print(f"  {crawler['id']:30} {impl_badge:10} {crawler['name']}")
        print()


def run_tests(crawlers, registry, test_config=True, test_custom=True):
    """Run tests for the specified crawlers."""
    TEST_OUTPUT_DIR.mkdir(exist_ok=True)

    venv_python = get_venv_python() if test_config else None

    results = {
        'passed': [],
        'failed': [],
        'skipped': []
    }

    print(f"\n{Colors.BOLD}Testing {len(crawlers)} crawler(s){Colors.RESET}\n")

    for crawler in crawlers:
        crawler_id = crawler['id']
        impl = crawler.get('implementation', 'custom')

        # Skip health monitor
        if crawler_id == '000_health_monitor':
            continue

        print(f"{Colors.BOLD}Testing: {crawler_id}{Colors.RESET} ({crawler['name']})")

        if impl == 'config' and test_config:
            success, message = test_config_crawler(crawler, venv_python)
        elif impl == 'custom' and test_custom:
            success, message = test_custom_crawler(crawler)
        else:
            results['skipped'].append((crawler_id, "Filtered out"))
            print(f"  {Colors.YELLOW}SKIPPED{Colors.RESET}: Filtered out\n")
            continue

        if success is None:
            results['skipped'].append((crawler_id, message))
            print(f"  {Colors.YELLOW}SKIPPED{Colors.RESET}: {message}\n")
        elif success:
            results['passed'].append(crawler_id)
            print(f"  {Colors.GREEN}PASSED{Colors.RESET}\n")
        else:
            results['failed'].append((crawler_id, message))
            print(f"  {Colors.RED}FAILED{Colors.RESET}: {message[:200]}\n")

    return results


def print_summary(results):
    """Print test summary."""
    print(f"\n{Colors.BOLD}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}Test Summary{Colors.RESET}")
    print(f"{'='*60}")

    print(f"{Colors.GREEN}Passed:{Colors.RESET}  {len(results['passed'])}")
    print(f"{Colors.RED}Failed:{Colors.RESET}  {len(results['failed'])}")
    print(f"{Colors.YELLOW}Skipped:{Colors.RESET} {len(results['skipped'])}")

    if results['failed']:
        print(f"\n{Colors.RED}Failed crawlers:{Colors.RESET}")
        for crawler_id, error in results['failed']:
            print(f"  - {crawler_id}")

    if results['skipped']:
        print(f"\n{Colors.YELLOW}Skipped crawlers:{Colors.RESET}")
        for crawler_id, reason in results['skipped']:
            print(f"  - {crawler_id}: {reason}")

    print()
    return len(results['failed']) == 0


def main():
    parser = argparse.ArgumentParser(description='Test crawlers locally')
    parser.add_argument('crawler_id', nargs='?', help='Specific crawler ID to test')
    parser.add_argument('--all', '-a', action='store_true', help='Test all crawlers')
    parser.add_argument('--config', '-c', action='store_true', help='Test only config-driven crawlers')
    parser.add_argument('--custom', '-u', action='store_true', help='Test only custom crawlers')
    parser.add_argument('--category', '-t', help='Test crawlers in specific category')
    parser.add_argument('--list', '-l', action='store_true', help='List available crawlers')

    args = parser.parse_args()

    registry = load_registry()
    crawlers = registry['crawlers']

    # List mode
    if args.list or (not args.crawler_id and not args.all and not args.config
                     and not args.custom and not args.category):
        list_crawlers(registry)
        return

    # Filter crawlers
    test_crawlers = crawlers

    if args.crawler_id:
        test_crawlers = [c for c in crawlers if c['id'] == args.crawler_id]
        if not test_crawlers:
            print(f"Crawler not found: {args.crawler_id}")
            list_crawlers(registry)
            sys.exit(1)

    if args.category:
        test_crawlers = [c for c in test_crawlers if c['category'] == args.category]

    if args.config:
        test_crawlers = [c for c in test_crawlers if c.get('implementation') == 'config']

    if args.custom:
        test_crawlers = [c for c in test_crawlers if c.get('implementation') == 'custom']

    # Determine what to test
    test_config = not args.custom
    test_custom = not args.config

    # Run tests
    results = run_tests(test_crawlers, registry, test_config, test_custom)

    # Print summary
    success = print_summary(results)

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
