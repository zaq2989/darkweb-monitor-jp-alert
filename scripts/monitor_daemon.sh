#!/bin/bash
#
# Darkweb Monitor Daemon
# Runs continuously in background
#

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
PIDFILE="$PROJECT_DIR/monitor.pid"
LOGFILE="$PROJECT_DIR/logs/monitor_daemon.log"

start() {
    if [ -f $PIDFILE ] && kill -0 $(cat $PIDFILE) 2>/dev/null; then
        echo "Monitor is already running (PID: $(cat $PIDFILE))"
        return 1
    fi
    
    echo "Starting Darkweb Monitor daemon..."
    cd "$PROJECT_DIR"
    source "$PROJECT_DIR/venv/bin/activate"
    
    nohup python "$PROJECT_DIR/scripts/start_monitoring_free.py" \
        >> "$LOGFILE" 2>&1 &
    
    echo $! > $PIDFILE
    echo "Started with PID: $(cat $PIDFILE)"
    echo "Logs: tail -f $LOGFILE"
}

stop() {
    if [ ! -f $PIDFILE ]; then
        echo "Monitor is not running"
        return 1
    fi
    
    PID=$(cat $PIDFILE)
    if kill -0 $PID 2>/dev/null; then
        echo "Stopping Monitor (PID: $PID)..."
        kill $PID
        rm -f $PIDFILE
        echo "Stopped"
    else
        echo "Monitor is not running (stale PID file)"
        rm -f $PIDFILE
    fi
}

status() {
    if [ -f $PIDFILE ] && kill -0 $(cat $PIDFILE) 2>/dev/null; then
        echo "Monitor is running (PID: $(cat $PIDFILE))"
        echo "Uptime: $(ps -p $(cat $PIDFILE) -o etime= | xargs)"
    else
        echo "Monitor is not running"
    fi
}

case "$1" in
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
        echo "Usage: $0 {start|stop|restart|status}"
        exit 1
        ;;
esac
