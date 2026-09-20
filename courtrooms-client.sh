#!/usr/bin/env bash
set -euo pipefail

SERVICE_NAME="courtrooms-client"

if [[ $# -lt 1 ]]; then
    echo "Usage: $0 install|start|stop|status" >&2
    exit 1
fi

ACTION="$1"
PROJECT_DIR="$(cd "$(dirname "$(readlink -f "$0")")" && pwd)"

case "$ACTION" in
    install)
        UNIT_PATH="/etc/systemd/system/${SERVICE_NAME}.service"

        if [[ ! -f "$PROJECT_DIR/client.py" ]]; then
            echo "ERROR: $PROJECT_DIR/client.py not found." >&2
            exit 1
        fi

        cat > "$UNIT_PATH" <<EOF
[Unit]
Description=Courtrooms client
After=network.target

[Service]
ExecStart=/usr/bin/python3 ${PROJECT_DIR}/client.py
Restart=always
User=root
WorkingDirectory=${PROJECT_DIR}

[Install]
WantedBy=multi-user.target
EOF

        echo "Wrote ${UNIT_PATH}"
        systemctl daemon-reload
        systemctl enable "$SERVICE_NAME"
        echo "Service '${SERVICE_NAME}' enabled."
        ;;
    start)
        systemctl start "$SERVICE_NAME"
        systemctl status "$SERVICE_NAME" --no-pager
        ;;
    stop)
        systemctl stop "$SERVICE_NAME"
        systemctl status "$SERVICE_NAME" --no-pager
        ;;
    status)
        systemctl status "$SERVICE_NAME" --no-pager
        ;;
    *)
        echo "Usage: $0 install|start|stop|status" >&2
        exit 1
        ;;
esac