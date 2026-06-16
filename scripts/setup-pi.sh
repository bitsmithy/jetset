#!/bin/bash
# setup-pi.sh: Run locally on the Pi after `make deploy`
# Installs system deps, builds rpi-rgb-led-matrix, and adds it to the project.
set -e

# 1. Add swap if missing
SWAPON=$(command -v swapon 2>/dev/null || echo "/usr/sbin/swapon")
if [ -x "$SWAPON" ]; then
    if ! $SWAPON --show 2>/dev/null | grep -q /swapfile; then
        echo "=== Creating 1GB swapfile ==="
        sudo fallocate -l 1G /swapfile 2>/dev/null || sudo dd if=/dev/zero of=/swapfile bs=1M count=1024
        sudo chmod 600 /swapfile
        sudo mkswap /swapfile 2>/dev/null || true
        sudo swapon /swapfile 2>/dev/null || true
    fi
else
    echo "=== Skipping swap (swapon not available) ==="
fi

# 2. Install system deps
sudo apt update && sudo apt install -y python3-dev python3-pil cython3 build-essential cmake

# 3. Install uv if missing
if ! command -v uv &> /dev/null; then
    echo "=== Installing uv ==="
    curl -LsSf https://astral.sh/uv/install.sh | sh
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
    export PATH="$HOME/.local/bin:$PATH"
else
    export PATH="$HOME/.local/bin:$PATH"
fi

# 4. Sync project deps and add scikit-build-core
cd ~/jetset
# Fix permissions if previous builds ran as root
sudo chown -R $(whoami):$(whoami) .venv 2>/dev/null || true
uv sync
uv pip install scikit-build-core

# 5. Clone, build, and add rgbmatrix to the project
WHEEL_FILE=$(ls ~/jetset/wheels/rgbmatrix-*.whl 2>/dev/null | head -1)
if [ ! -f "$WHEEL_FILE" ]; then
    echo "=== Building rpi-rgb-led-matrix ==="
    [ -d "$HOME/rpi-rgb-led-matrix" ] || git clone https://github.com/hzeller/rpi-rgb-led-matrix.git
    cd ~/rpi-rgb-led-matrix
    make -j4
    cd ~/jetset

    # Ensure Pillow headers are available for the pillow shim
    if [ ! -d "/tmp/Pillow" ]; then
        git clone --depth 1 https://github.com/python-pillow/Pillow.git /tmp/Pillow
    fi

    # Build a local wheel so it becomes a proper project dependency
    mkdir -p wheels
    CFLAGS="-I/tmp/Pillow/src/libImaging" uv build --no-build-isolation --wheel \
        "$HOME/rpi-rgb-led-matrix" --out-dir "$PWD/wheels"

    # Add wheel as a path dependency in pyproject.toml (persists across uv sync)
    uv add ./wheels/rgbmatrix-*.whl

    # Free up space
    rm -rf /tmp/Pillow
else
    echo "=== rgbmatrix wheel already built ==="
fi

echo "=== Setup complete! Run \`make start\` ==="
