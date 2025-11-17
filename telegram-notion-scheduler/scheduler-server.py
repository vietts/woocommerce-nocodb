"""
Scheduler Server - Backend API for Telegram-Notion Scheduler
Provides REST API endpoints for managing the scheduler
"""

import os
import subprocess
import json
from datetime import datetime
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import psutil

app = Flask(__name__)
CORS(app)

# Serve static files (HTML, CSS, JS)
HTML_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scheduler-launcher.html')

SCHEDULER_DIR = os.path.dirname(os.path.abspath(__file__))
SCHEDULER_PY = os.path.join(SCHEDULER_DIR, 'scheduler.py')
SCHEDULER_LOG = os.path.join(SCHEDULER_DIR, 'scheduler.log')
LOCKFILE = os.path.join(SCHEDULER_DIR, '.scheduler.lock')
ENV_FILE = os.path.join(SCHEDULER_DIR, '.env')


def get_lockfile_pid():
    """Get PID from lockfile if it exists and process is running"""
    try:
        if os.path.exists(LOCKFILE):
            with open(LOCKFILE, 'r') as f:
                pid = int(f.read().strip())
                # Verify process is actually running
                if psutil.pid_exists(pid):
                    return pid
                else:
                    # Stale lockfile
                    try:
                        os.remove(LOCKFILE)
                    except:
                        pass
                    return None
    except:
        pass
    return None


def get_scheduler_pid():
    """Get PID of running scheduler process"""
    try:
        result = subprocess.run(
            ['pgrep', '-f', 'python3 scheduler.py'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return int(result.stdout.strip().split('\n')[0])
    except:
        pass
    return None


def is_scheduler_running():
    """Check if scheduler is currently running using lockfile"""
    # Primary check: lockfile with valid PID (most reliable)
    lockfile_pid = get_lockfile_pid()
    if lockfile_pid:
        return True

    # Fallback: check running processes
    pid = get_scheduler_pid()
    if pid:
        try:
            return psutil.Process(pid).is_running()
        except:
            pass
    return False


def get_last_log_lines(n=50):
    """Get last n lines from scheduler.log"""
    try:
        if not os.path.exists(SCHEDULER_LOG):
            return "Log file not found yet"

        with open(SCHEDULER_LOG, 'r') as f:
            lines = f.readlines()
            return ''.join(lines[-n:])
    except Exception as e:
        return f"Error reading log: {str(e)}"


def get_last_check_time():
    """Get the time of last scheduler check from log"""
    try:
        if not os.path.exists(SCHEDULER_LOG):
            return None

        with open(SCHEDULER_LOG, 'r') as f:
            for line in reversed(f.readlines()):
                if 'Checking for scheduled posts' in line:
                    # Extract timestamp from log line
                    # Format: 2025-11-17 13:35:32,903
                    parts = line.split(' - ')
                    if parts:
                        return parts[0].strip()
        return None
    except:
        return None


@app.route('/api/status', methods=['GET'])
def get_status():
    """Get current scheduler status"""
    running = is_scheduler_running()
    last_check = get_last_check_time()
    lockfile_pid = get_lockfile_pid()

    return jsonify({
        'running': running,
        'status': 'Attivo' if running else 'Arrestato',
        'lockfile_pid': lockfile_pid if lockfile_pid else None,
        'lockfile_exists': os.path.exists(LOCKFILE),
        'last_check': last_check or 'No checks yet',
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/next-posts', methods=['GET'])
def get_next_posts_endpoint():
    """Get the next scheduled posts"""
    try:
        posts = get_next_posts()
        return jsonify({
            'success': True,
            'count': len(posts),
            'posts': posts
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'posts': []
        }), 500


@app.route('/api/execute', methods=['POST'])
def execute_action():
    """Execute scheduler management actions"""
    try:
        data = request.json
        action = data.get('action')

        if action == 'start':
            return start_scheduler()
        elif action == 'stop':
            return stop_scheduler()
        elif action == 'status':
            return check_status()
        elif action == 'logs':
            return get_logs()
        elif action == 'test':
            return test_connection()
        elif action == 'config':
            return get_config()
        else:
            return jsonify({'error': f'Unknown action: {action}'}), 400

    except Exception as e:
        return jsonify({'error': str(e)}), 500


def start_scheduler():
    """Start the scheduler in background"""
    try:
        # Check lockfile first (most reliable)
        lockfile_pid = get_lockfile_pid()
        if lockfile_pid:
            return jsonify({
                'error': f'Scheduler is already running (PID: {lockfile_pid})',
                'running': True,
                'pid': lockfile_pid
            }), 400

        # Fallback: check running processes
        if is_scheduler_running():
            return jsonify({'error': 'Scheduler is already running'}), 400

        # Start scheduler in background
        subprocess.Popen(
            ['python3', SCHEDULER_PY],
            cwd=SCHEDULER_DIR,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        return jsonify({'success': True, 'message': 'Scheduler started'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def stop_scheduler():
    """Stop the scheduler"""
    try:
        result = subprocess.run(
            ['pkill', '-f', 'python3 scheduler.py'],
            capture_output=True,
            text=True,
            timeout=5
        )

        return jsonify({'success': True, 'message': 'Scheduler stopped'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def check_status():
    """Check scheduler status and running instances"""
    try:
        result = subprocess.run(
            ['bash', os.path.join(SCHEDULER_DIR, 'check_scheduler.sh')],
            capture_output=True,
            text=True,
            timeout=5
        )

        output = result.stdout + result.stderr
        return jsonify({'success': True, 'output': output})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def get_logs():
    """Get recent log entries"""
    try:
        logs = get_last_log_lines(50)
        return jsonify({'success': True, 'output': logs})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def test_connection():
    """Test Notion and Telegram connections"""
    try:
        result = subprocess.run(
            ['python3', 'test_connection.py'],
            cwd=SCHEDULER_DIR,
            capture_output=True,
            text=True,
            timeout=15
        )

        output = result.stdout + (result.stderr if result.returncode != 0 else '')
        return jsonify({'success': True, 'output': output})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def get_next_posts():
    """Get the next scheduled posts ready to be published"""
    try:
        # Import NotionClient
        from notion_handler import NotionClient

        client = NotionClient(
            token=os.getenv("NOTION_TOKEN"),
            data_source_id=os.getenv("NOTION_DATA_SOURCE_ID")
        )

        # Get scheduled posts
        posts = client.get_scheduled_posts()

        # Return first 5 posts with relevant info
        next_posts = []
        for post in posts[:5]:
            next_posts.append({
                'title': post.get('title', 'Untitled'),
                'type': post.get('type', 'Unknown'),
                'publish_date': post.get('publish_date', 'Unknown'),
                'message': post.get('message', '')[:100] + ('...' if len(post.get('message', '')) > 100 else '')
            })

        return next_posts
    except Exception as e:
        return []


def get_config():
    """Get scheduler configuration"""
    try:
        config_info = "📋 SCHEDULER CONFIGURATION\n"
        config_info += "=" * 50 + "\n\n"

        # Read environment variables
        if os.path.exists(ENV_FILE):
            config_info += "🔐 Environment Variables (.env):\n"
            config_info += "-" * 50 + "\n"

            with open(ENV_FILE, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # Hide sensitive values
                        if '=' in line:
                            key, value = line.split('=', 1)
                            if any(sensitive in key.lower() for sensitive in ['token', 'key', 'secret', 'password']):
                                config_info += f"{key}=***REDACTED***\n"
                            else:
                                config_info += f"{line}\n"

        config_info += "\n📁 File Paths:\n"
        config_info += "-" * 50 + "\n"
        config_info += f"Project Dir:  {SCHEDULER_DIR}\n"
        config_info += f"Scheduler:    {SCHEDULER_PY}\n"
        config_info += f"Log File:     {SCHEDULER_LOG}\n"
        config_info += f"Env File:     {ENV_FILE}\n"

        config_info += "\n⚙️ System Info:\n"
        config_info += "-" * 50 + "\n"
        config_info += f"Python Version: {os.popen('python3 --version').read().strip()}\n"

        # Check installed packages
        try:
            import notion_handler
            config_info += "✅ Notion Handler: OK\n"
        except:
            config_info += "❌ Notion Handler: MISSING\n"

        try:
            import telegram_handler
            config_info += "✅ Telegram Handler: OK\n"
        except:
            config_info += "❌ Telegram Handler: MISSING\n"

        config_info += f"🔍 Scheduler Running: {'✅ YES' if is_scheduler_running() else '❌ NO'}\n"

        return jsonify({'success': True, 'output': config_info})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/', methods=['GET'])
def serve_ui():
    """Serve the main UI HTML file"""
    if os.path.exists(HTML_FILE):
        return send_file(HTML_FILE, mimetype='text/html')
    else:
        return jsonify({'error': 'scheduler-launcher.html not found'}), 404


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'scheduler_running': is_scheduler_running(),
        'timestamp': datetime.now().isoformat()
    })


if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("🚀 Scheduler Server Started")
    print("=" * 60)
    print(f"📍 Web UI: http://localhost:5555")
    print(f"📍 API Base: http://localhost:5555/api")
    print(f"📂 Project: {SCHEDULER_DIR}")
    print(f"🔍 Scheduler: {'✅ RUNNING' if is_scheduler_running() else '❌ STOPPED'}")
    print("\n💡 Apri nel browser: http://localhost:5555")
    print("=" * 60 + "\n")

    app.run(host='localhost', port=5555, debug=False)
