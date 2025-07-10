#!/bin/bash
#
# ダークウェブモニター スケジュール設定スクリプト
#

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
VENV_PATH="$PROJECT_DIR/venv"
MONITOR_SCRIPT="$PROJECT_DIR/scripts/start_monitoring_free.py"
USER=$(whoami)

echo "=========================================="
echo "Darkweb Monitor Schedule Setup"
echo "=========================================="
echo "Project: $PROJECT_DIR"
echo "User: $USER"
echo ""

# Function to setup crontab
setup_crontab() {
    echo "Setting up crontab..."
    
    # Create cron job script
    cat > "$PROJECT_DIR/scripts/cron_monitor.sh" << EOF
#!/bin/bash
# Darkweb Monitor Cron Script
cd "$PROJECT_DIR"
source "$VENV_PATH/bin/activate"
python "$MONITOR_SCRIPT" --once >> "$PROJECT_DIR/logs/monitor_cron.log" 2>&1
EOF
    
    chmod +x "$PROJECT_DIR/scripts/cron_monitor.sh"
    
    # Add to crontab (every 15 minutes)
    CRON_CMD="*/15 * * * * $PROJECT_DIR/scripts/cron_monitor.sh"
    
    # Check if already exists
    if crontab -l 2>/dev/null | grep -q "cron_monitor.sh"; then
        echo "✓ Cron job already exists"
    else
        (crontab -l 2>/dev/null; echo "$CRON_CMD") | crontab -
        echo "✓ Added cron job (runs every 15 minutes)"
    fi
    
    # Create log directory
    mkdir -p "$PROJECT_DIR/logs"
    
    echo ""
    echo "Crontab entry:"
    echo "$CRON_CMD"
    echo ""
    echo "View logs: tail -f $PROJECT_DIR/logs/monitor_cron.log"
    echo "Edit cron: crontab -e"
    echo "Remove cron: crontab -l | grep -v cron_monitor.sh | crontab -"
}

# Function to setup systemd
setup_systemd() {
    echo "Setting up systemd service..."
    
    # Create systemd service file
    SERVICE_FILE="/etc/systemd/system/darkweb-monitor.service"
    TIMER_FILE="/etc/systemd/system/darkweb-monitor.timer"
    
    # Service file content
    cat > /tmp/darkweb-monitor.service << EOF
[Unit]
Description=Darkweb Monitor for Japanese Companies
After=network.target

[Service]
Type=oneshot
User=$USER
WorkingDirectory=$PROJECT_DIR
Environment="PATH=$VENV_PATH/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=$VENV_PATH/bin/python $MONITOR_SCRIPT --once
StandardOutput=append:$PROJECT_DIR/logs/monitor_systemd.log
StandardError=append:$PROJECT_DIR/logs/monitor_systemd.log

[Install]
WantedBy=multi-user.target
EOF

    # Timer file content
    cat > /tmp/darkweb-monitor.timer << EOF
[Unit]
Description=Run Darkweb Monitor every 15 minutes
Requires=darkweb-monitor.service

[Timer]
OnBootSec=5min
OnUnitActiveSec=15min
Unit=darkweb-monitor.service

[Install]
WantedBy=timers.target
EOF

    echo ""
    echo "Systemd service files created in /tmp/"
    echo ""
    echo "To install (requires sudo):"
    echo "  sudo cp /tmp/darkweb-monitor.service $SERVICE_FILE"
    echo "  sudo cp /tmp/darkweb-monitor.timer $TIMER_FILE"
    echo "  sudo systemctl daemon-reload"
    echo "  sudo systemctl enable darkweb-monitor.timer"
    echo "  sudo systemctl start darkweb-monitor.timer"
    echo ""
    echo "To check status:"
    echo "  sudo systemctl status darkweb-monitor.timer"
    echo "  sudo journalctl -u darkweb-monitor.service -f"
}

# Function to create Docker setup
setup_docker() {
    echo "Creating Docker configuration..."
    
    # Create Dockerfile
    cat > "$PROJECT_DIR/Dockerfile" << 'EOF'
FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tor \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create directories
RUN mkdir -p logs watch_files

# Environment variables
ENV PYTHONUNBUFFERED=1

# Run script
CMD ["python", "scripts/start_monitoring_free.py", "--interval", "15"]
EOF

    # Create docker-compose.yml
    cat > "$PROJECT_DIR/docker-compose.yml" << EOF
version: '3.8'

services:
  darkweb-monitor:
    build: .
    container_name: darkweb-monitor-jp
    restart: unless-stopped
    environment:
      - SLACK_WEBHOOK_URL=\${SLACK_WEBHOOK_URL}
      - TZ=Asia/Tokyo
    volumes:
      - ./logs:/app/logs
      - ./watch_files:/app/watch_files
      - ./.env:/app/.env:ro
    networks:
      - monitor-network

  tor-proxy:
    image: dperson/torproxy:latest
    container_name: tor-proxy
    restart: unless-stopped
    networks:
      - monitor-network
    ports:
      - "9050:9050"
      - "9051:9051"

networks:
  monitor-network:
    driver: bridge
EOF

    # Create .dockerignore
    cat > "$PROJECT_DIR/.dockerignore" << EOF
venv/
__pycache__/
*.pyc
*.pyo
*.pyd
.git/
.gitignore
logs/*
processed_*.txt
processed_*.json
*_cache.json
test_*.py
EOF

    echo "✓ Docker files created"
    echo ""
    echo "To run with Docker:"
    echo "  docker-compose build"
    echo "  docker-compose up -d"
    echo ""
    echo "To view logs:"
    echo "  docker-compose logs -f darkweb-monitor"
}

# Function to create standalone daemon script
setup_daemon() {
    echo "Creating standalone daemon script..."
    
    cat > "$PROJECT_DIR/scripts/monitor_daemon.sh" << EOF
#!/bin/bash
#
# Darkweb Monitor Daemon
# Runs continuously in background
#

SCRIPT_DIR="\$( cd "\$( dirname "\${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="\$(dirname "\$SCRIPT_DIR")"
PIDFILE="\$PROJECT_DIR/monitor.pid"
LOGFILE="\$PROJECT_DIR/logs/monitor_daemon.log"

start() {
    if [ -f \$PIDFILE ] && kill -0 \$(cat \$PIDFILE) 2>/dev/null; then
        echo "Monitor is already running (PID: \$(cat \$PIDFILE))"
        return 1
    fi
    
    echo "Starting Darkweb Monitor daemon..."
    cd "\$PROJECT_DIR"
    source "\$PROJECT_DIR/venv/bin/activate"
    
    nohup python "\$PROJECT_DIR/scripts/start_monitoring_free.py" \\
        >> "\$LOGFILE" 2>&1 &
    
    echo \$! > \$PIDFILE
    echo "Started with PID: \$(cat \$PIDFILE)"
    echo "Logs: tail -f \$LOGFILE"
}

stop() {
    if [ ! -f \$PIDFILE ]; then
        echo "Monitor is not running"
        return 1
    fi
    
    PID=\$(cat \$PIDFILE)
    if kill -0 \$PID 2>/dev/null; then
        echo "Stopping Monitor (PID: \$PID)..."
        kill \$PID
        rm -f \$PIDFILE
        echo "Stopped"
    else
        echo "Monitor is not running (stale PID file)"
        rm -f \$PIDFILE
    fi
}

status() {
    if [ -f \$PIDFILE ] && kill -0 \$(cat \$PIDFILE) 2>/dev/null; then
        echo "Monitor is running (PID: \$(cat \$PIDFILE))"
        echo "Uptime: \$(ps -p \$(cat \$PIDFILE) -o etime= | xargs)"
    else
        echo "Monitor is not running"
    fi
}

case "\$1" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        stop
        sleep 2
        start
        ;;
    status)
        status
        ;;
    *)
        echo "Usage: \$0 {start|stop|restart|status}"
        exit 1
        ;;
esac
EOF

    chmod +x "$PROJECT_DIR/scripts/monitor_daemon.sh"
    
    echo "✓ Daemon script created"
    echo ""
    echo "Usage:"
    echo "  $PROJECT_DIR/scripts/monitor_daemon.sh start"
    echo "  $PROJECT_DIR/scripts/monitor_daemon.sh stop"
    echo "  $PROJECT_DIR/scripts/monitor_daemon.sh status"
}

# Main menu
echo "Select setup method:"
echo "1) Crontab (simple, user-level)"
echo "2) Systemd (system service, requires sudo)"
echo "3) Docker (containerized)"
echo "4) Standalone daemon"
echo "5) All configurations"
echo ""
read -p "Enter choice [1-5]: " choice

case $choice in
    1)
        setup_crontab
        ;;
    2)
        setup_systemd
        ;;
    3)
        setup_docker
        ;;
    4)
        setup_daemon
        ;;
    5)
        setup_crontab
        echo ""
        setup_systemd
        echo ""
        setup_docker
        echo ""
        setup_daemon
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "Setup complete!"