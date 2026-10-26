import json
import os
import time
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify
import threading
from pathlib import Path

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

app = Flask(__name__)

# Container Status Cache
container_status_cache = {}

# Registry file path (mounted from project root)
REGISTRY_FILE = Path("/app/configs/crawlers.yaml")


def load_containers_from_registry():
    """Load container definitions from crawlers.yaml registry."""
    if not HAS_YAML:
        print("Warning: PyYAML not installed, using fallback")
        return None

    if not REGISTRY_FILE.exists():
        print(f"Warning: Registry file not found at {REGISTRY_FILE}")
        return None

    try:
        with open(REGISTRY_FILE, 'r', encoding='utf-8') as f:
            registry = yaml.safe_load(f)

        containers = {}
        for crawler in registry.get('crawlers', []):
            # Skip health monitor itself
            if crawler['id'] == '000_health_monitor':
                continue

            # Pausierte Crawler (enabled: false) nicht überwachen, sonst gäbe es dauerhaft Alarm
            if not crawler.get('enabled', True):
                continue

            # Build container key (matching old format)
            cid = crawler['id']
            # Fallback removed, after Ferienpass Cleanup
            key = f"gs_compiler_{cid}"

            containers[key] = {
                'name': crawler['name'],
                'expected_files': crawler.get('expected_files', []),
                'source': crawler.get('source', ''),
                'schedule': crawler.get('schedule_human', crawler.get('schedule', '')),
                'type': crawler.get('type', '')
            }

        print(f"Loaded {len(containers)} crawlers from registry")
        return containers

    except Exception as e:
        print(f"Error loading registry: {e}")
        return None


# Try to load from registry, fall back to hardcoded if not available
CONTAINERS = load_containers_from_registry()

# Die Registry (crawlers.yaml) ist die einzige Quelle; ohne sie gibt es nichts zu überwachen
if CONTAINERS is None:
    print("Registry nicht verfügbar - es sind keine Crawler konfiguriert")
    CONTAINERS = {}


def get_container_status():
    """Überwacht Container Status durch Dateisystem-Monitoring"""
    status_data = {
        'containers': [],
        'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'total_containers': 0,
        'running': 0,
        'stopped': 0,
        'error': 0,
        'warning': 0
    }

    output_dir = "output/"

    try:
        for container_id, container_info in CONTAINERS.items():
            try:
                container_status = {
                    'name': container_id,
                    'display_name': container_info['name'],
                    'source': container_info['source'],
                    'schedule': container_info['schedule'],
                    'type': container_info['type'],
                    'expected_files': container_info['expected_files'],
                    'status': 'unknown',
                    'health': 'unknown',
                    'file_status': [],
                    'last_file_update': 'Nie',
                    'file_count': 0,
                    'total_size_mb': 0,
                    'issues': []
                }

                # Dateien überprüfen
                files_found = 0
                latest_file_time = None
                total_size = 0

                for expected_file in container_info['expected_files']:
                    file_path = os.path.join(output_dir, expected_file)
                    file_info = {
                        'name': expected_file,
                        'exists': False,
                        'size_mb': 0,
                        'last_modified': 'Nie',
                        'age_hours': 0
                    }

                    if os.path.exists(file_path):
                        file_info['exists'] = True
                        files_found += 1

                        # Dateigröße
                        size_bytes = os.path.getsize(file_path)
                        file_info['size_mb'] = round(size_bytes / 1024 / 1024, 2)
                        total_size += size_bytes

                        # Letzte Änderung
                        mtime = os.path.getmtime(file_path)
                        mtime_dt = datetime.fromtimestamp(mtime)
                        file_info['last_modified'] = mtime_dt.strftime('%Y-%m-%d %H:%M:%S')

                        # Alter in Stunden
                        age = datetime.now() - mtime_dt
                        file_info['age_hours'] = round(age.total_seconds() / 3600, 1)

                        # Neueste Datei tracken
                        if latest_file_time is None or mtime_dt > latest_file_time:
                            latest_file_time = mtime_dt

                    container_status['file_status'].append(file_info)

                container_status['file_count'] = files_found
                container_status['total_size_mb'] = round(total_size / 1024 / 1024, 2)

                if latest_file_time:
                    container_status['last_file_update'] = latest_file_time.strftime('%Y-%m-%d %H:%M:%S')

                # Status bestimmen basierend auf Dateien
                if files_found == 0:
                    container_status['status'] = 'error'
                    container_status['health'] = 'no_files'
                    container_status['issues'].append('Keine Output-Dateien gefunden')
                elif files_found < len(container_info['expected_files']):
                    container_status['status'] = 'warning'
                    container_status['health'] = 'missing_files'
                    missing = len(container_info['expected_files']) - files_found
                    container_status['issues'].append(f'{missing} erwartete Dateien fehlen')
                else:
                    # Prüfe Aktualität der Dateien
                    if latest_file_time:
                        age = datetime.now() - latest_file_time
                        hours_old = age.total_seconds() / 3600

                        if hours_old > 48:  # Älter als 2 Tage
                            container_status['status'] = 'error'
                            container_status['health'] = 'outdated'
                            container_status['issues'].append(f'Dateien sind {round(hours_old, 1)} Stunden alt')
                        elif hours_old > 24:  # Älter als 1 Tag
                            container_status['status'] = 'warning'
                            container_status['health'] = 'stale'
                            container_status['issues'].append(f'Dateien sind {round(hours_old, 1)} Stunden alt')
                        else:
                            container_status['status'] = 'running'
                            container_status['health'] = 'healthy'

                # Zusätzliche Validierung für JSON-Dateien
                for file_info in container_status['file_status']:
                    if file_info['exists'] and file_info['name'].endswith('.json'):
                        file_path = os.path.join(output_dir, file_info['name'])
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                json.load(f)
                            file_info['valid_json'] = True
                        except:
                            file_info['valid_json'] = False
                            container_status['issues'].append(f'{file_info["name"]} ist kein gültiges JSON')
                            if container_status['status'] == 'running':
                                container_status['status'] = 'warning'

                status_data['containers'].append(container_status)

                # Counters aktualisieren
                status_data['total_containers'] += 1
                if container_status['status'] == 'running':
                    status_data['running'] += 1
                elif container_status['status'] == 'warning':
                    status_data['warning'] += 1
                elif container_status['status'] == 'error':
                    status_data['error'] += 1
                else:
                    status_data['stopped'] += 1

            except Exception as e:
                print(f"Fehler beim Verarbeiten von Container {container_id}: {e}")

    except Exception as e:
        status_data['error_message'] = f"Fehler beim Abrufen der Container-Status: {e}"
        print(f"Monitor Fehler: {e}")

    return status_data

def update_status_cache():
    """Aktualisiert den Status Cache regelmäßig"""
    global container_status_cache
    while True:
        try:
            container_status_cache = get_container_status()

            # Status auch als JSON-Datei speichern
            # eigener Ordner: der Rest von output/ ist für den Health Monitor nur lesbar gemountet
            output_dir = "output/000_health_monitor/"
            os.makedirs(output_dir, exist_ok=True)

            with open(os.path.join(output_dir, "000-health-status.json"), "w", encoding="utf-8") as f:
                json.dump(container_status_cache, f, ensure_ascii=False, indent=2)

        except Exception as e:
            print(f"Fehler beim Aktualisieren des Status Cache: {e}")

        time.sleep(30)  # Alle 30 Sekunden aktualisieren

@app.route('/health')
def index():
    """Hauptseite mit Container Status"""
    return render_template('index.html', status=container_status_cache)

@app.route('/health/status')
def api_status():
    """API Endpoint für Container Status"""
    return jsonify(container_status_cache)

@app.route('/health/container/<container_name>')
def api_container_detail(container_name):
    """API Endpoint für Details eines spezifischen Containers"""
    for container in container_status_cache.get('containers', []):
        if container['name'] == container_name:
            return jsonify(container)
    return jsonify({'error': 'Container nicht gefunden'}), 404

@app.route('/health/restart/<container_name>')
def api_restart_container(container_name):
    """API Endpoint zum Neustarten eines Containers - Nicht verfügbar ohne Docker Socket"""
    return jsonify({
        'success': False,
        'error': 'Container-Neustart nicht verfügbar - Docker Socket Zugriff nicht möglich',
        'message': 'Diese Funktion benötigt direkten Zugriff auf Docker, der in dieser Umgebung nicht verfügbar ist.'
    }), 503

@app.route('/health/files/<container_name>')
def api_container_files(container_name):
    """API Endpoint für Dateien eines spezifischen Containers"""
    for container in container_status_cache.get('containers', []):
        if container['name'] == container_name:
            return jsonify({
                'container': container_name,
                'files': container.get('file_status', []),
                'total_size_mb': container.get('total_size_mb', 0),
                'file_count': container.get('file_count', 0),
                'last_update': container.get('last_file_update', 'Nie')
            })
    return jsonify({'error': 'Container nicht gefunden'}), 404

@app.route('/health/system')
def api_health():
    """API Endpoint für System Health Check"""
    stats = container_status_cache
    health_score = 0

    if stats.get('total_containers', 0) > 0:
        running = stats.get('running', 0)
        warning = stats.get('warning', 0)
        total = stats.get('total_containers', 1)

        # Health Score berechnen (0-100)
        health_score = round((running + (warning * 0.5)) / total * 100, 1)

    return jsonify({
        'health_score': health_score,
        'status': 'healthy' if health_score >= 80 else 'warning' if health_score >= 60 else 'critical',
        'summary': {
            'total': stats.get('total_containers', 0),
            'running': stats.get('running', 0),
            'warning': stats.get('warning', 0),
            'error': stats.get('error', 0),
            'stopped': stats.get('stopped', 0)
        },
        'last_updated': stats.get('last_updated', 'Nie')
    })

if __name__ == '__main__':
    # Status Cache Update Thread starten
    update_thread = threading.Thread(target=update_status_cache, daemon=True)
    update_thread.start()

    # Initialer Status Cache
    container_status_cache = get_container_status()

    print("Health Monitor gestartet auf http://0.0.0.0:5000")
    app.run(host='0.0.0.0', port=5000, debug=False)
