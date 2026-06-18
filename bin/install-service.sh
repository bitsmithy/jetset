#!/bin/bash
# Render scripts/jetset.service.template (@HOME@ -> $HOME) and install + enable
# the systemd unit. Idempotent; run on the Pi. Callers restart the service.
set -e
cd "$(dirname "$0")/.."

sed "s|@HOME@|$HOME|g" scripts/jetset.service.template \
    | sudo tee /etc/systemd/system/jetset.service > /dev/null
sudo systemctl daemon-reload
sudo systemctl enable jetset
