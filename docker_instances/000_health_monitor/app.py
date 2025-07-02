import docker
import json
import os
import time
from datetime import datetime
from flask import Flask, render_template, jsonify
import threading

app = Flask(__name__)

# Docker Client initialisieren
client = docker.from_env()

# Container Status Cache
container_status_cache = {}

def get_container_status():
    """Holt den Status aller gs_compiler Container"""
    status_data = {
        'containers': [],
        'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'total_containers': 0,
        'running': 0,
        'stopped': 0,
        'error': 0
    }
    
    try:
        # Alle Container mit gs_compiler Prefix holen
        containers = client.containers.list(all=True, filters={'name': 'gs_compiler'})
        
        for container in containers:
            try:
                # Container Informationen sammeln
                container_info = {
                    'name': container.name,
                    'status': container.status,
                    'image': container.image.tags[0] if container.image.tags else 'unknown',
                    'created': container.attrs['Created'][:19].replace('T', ' '),
                    'ports': container.ports if hasattr(container, 'ports') else {},
                    'health': 'unknown'
                }
                
                # Health Check Status wenn verfügbar
                if container.attrs.get('State', {}).get('Health'):
                    container_info['health'] = container.attrs['State']['Health']['Status']
                
                # Logs der letzten 100 Zeilen (für Debug)
                try:
                    logs = container.logs(tail=5).decode('utf-8', errors='ignore')
                    container_info['recent_logs'] = logs.split('\n')[-5:] if logs else []
                except:
                    container_info['recent_logs'] = ['Logs nicht verfügbar']
                
                # Stats sammeln wenn Container läuft
                if container.status == 'running':
                    try:
                        stats = container.stats(stream=False)
                        # CPU Usage berechnen
                        cpu_percent = 0
                        if 'cpu_stats' in stats and 'precpu_stats' in stats:
                            cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - stats['precpu_stats']['cpu_usage']['total_usage']
                            system_delta = stats['cpu_stats']['system_cpu_usage'] - stats['precpu_stats']['system_cpu_usage']
                            if system_delta > 0:
                                cpu_percent = (cpu_delta / system_delta) * len(stats['cpu_stats']['cpu_usage']['percpu_usage']) * 100
                        
                        # Memory Usage
                        memory_usage = 0
                        memory_limit = 0
                        if 'memory_stats' in stats:
                            memory_usage = stats['memory_stats'].get('usage', 0)
                            memory_limit = stats['memory_stats'].get('limit', 0)
                        
                        container_info['stats'] = {
                            'cpu_percent': round(cpu_percent, 2),
                            'memory_usage_mb': round(memory_usage / 1024 / 1024, 2),
                            'memory_limit_mb': round(memory_limit / 1024 / 1024, 2),
                            'memory_percent': round((memory_usage / memory_limit * 100), 2) if memory_limit > 0 else 0
                        }
                    except:
                        container_info['stats'] = {'error': 'Stats nicht verfügbar'}
                
                status_data['containers'].append(container_info)
                
                # Counters aktualisieren
                status_data['total_containers'] += 1
                if container.status == 'running':
                    status_data['running'] += 1
                elif container.status in ['exited', 'stopped']:
                    status_data['stopped'] += 1
                else:
                    status_data['error'] += 1
                    
            except Exception as e:
                print(f"Fehler beim Verarbeiten von Container {container.name}: {e}")
                
    except Exception as e:
        status_data['error_message'] = f"Fehler beim Abrufen der Container: {e}"
        print(f"Docker API Fehler: {e}")
    
    return status_data

def update_status_cache():
    """Aktualisiert den Status Cache regelmäßig"""
    global container_status_cache
    while True:
        try:
            container_status_cache = get_container_status()
            
            # Status auch als JSON-Datei speichern
            output_dir = "/app/output"
            os.makedirs(output_dir, exist_ok=True)
            
            with open(os.path.join(output_dir, "000-health-status.json"), "w", encoding="utf-8") as f:
                json.dump(container_status_cache, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"Fehler beim Aktualisieren des Status Cache: {e}")
        
        time.sleep(30)  # Alle 30 Sekunden aktualisieren

@app.route('/')
def index():
    """Hauptseite mit Container Status"""
    return render_template('index.html', status=container_status_cache)

@app.route('/api/status')
def api_status():
    """API Endpoint für Container Status"""
    return jsonify(container_status_cache)

@app.route('/api/container/<container_name>')
def api_container_detail(container_name):
    """API Endpoint für Details eines spezifischen Containers"""
    for container in container_status_cache.get('containers', []):
        if container['name'] == container_name:
            return jsonify(container)
    return jsonify({'error': 'Container nicht gefunden'}), 404

@app.route('/api/restart/<container_name>')
def api_restart_container(container_name):
    """API Endpoint zum Neustarten eines Containers"""
    try:
        container = client.containers.get(container_name)
        container.restart()
        return jsonify({'success': True, 'message': f'Container {container_name} wurde neu gestartet'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    # Status Cache Update Thread starten
    update_thread = threading.Thread(target=update_status_cache, daemon=True)
    update_thread.start()
    
    # Initialer Status Cache
    container_status_cache = get_container_status()
    
    print("🔍 Health Monitor gestartet auf http://0.0.0.0:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)
