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

# 2. Install system deps (Cython and Pillow live in the venv, not here)
sudo apt update && sudo apt install -y python3-dev build-essential cmake

# 3. Install uv if missing
if ! command -v uv &> /dev/null; then
    echo "=== Installing uv ==="
    curl -LsSf https://astral.sh/uv/install.sh | sh
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
    export PATH="$HOME/.local/bin:$PATH"
else
    export PATH="$HOME/.local/bin:$PATH"
fi

# 4. Sync project deps and add the rgbmatrix build backend (into the venv —
# the wheel builds with --no-build-isolation, so Cython/scikit-build-core must
# live in the venv, not just the system Python from apt).
cd ~/jetset
# Fix permissions if previous builds ran as root
sudo chown -R $(whoami):$(whoami) .venv 2>/dev/null || true
uv sync
uv pip install scikit-build-core cython

# 5. Clone, build, and add rgbmatrix to the project
WHEEL_FILE=$(ls ~/jetset/wheels/rgbmatrix-*.whl 2>/dev/null | head -1)
if [ ! -f "$WHEEL_FILE" ]; then
    echo "=== Building rpi-rgb-led-matrix ==="
    [ -d "$HOME/rpi-rgb-led-matrix" ] || \
        git clone https://github.com/hzeller/rpi-rgb-led-matrix.git "$HOME/rpi-rgb-led-matrix"
    cd "$HOME/rpi-rgb-led-matrix"
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

# 6. Download airline logos into the global cache (AppConfig.logo_dir =
# /var/lib/jetset/logos). Owned by the deploy user so this download can write;
# the root service only reads. A global dir means root and the deploy user
# resolve the same path — no per-home/JETSET_LOGO_DIR juggling.
echo "=== Downloading airline logos ==="
sudo mkdir -p /var/lib/jetset/logos
sudo chown "$(whoami):$(whoami)" /var/lib/jetset/logos
uv run python scripts/download_logos.py || echo "(logo download incomplete — re-run later)"

# 7. Reduce LED panel flicker. Two causes, both fixed here (idempotent; both
# take effect on the next reboot):
#   a) Onboard sound: the Adafruit HAT drives the panel's PWM timing on the
#      same hardware snd_bcm2835 uses, so leaving sound enabled is the most
#      common flicker source. Blacklist the module and turn audio off.
#   b) CPU contention: the matrix refresh thread runs on core 3; isolating it
#      (isolcpus=3) stops the scheduler from interrupting it with other work.
echo "=== Reducing LED flicker (disable sound, isolate core 3) ==="
echo "blacklist snd_bcm2835" | sudo tee /etc/modprobe.d/blacklist-rgb-matrix.conf >/dev/null

BOOT_CONFIG=/boot/firmware/config.txt
[ -f "$BOOT_CONFIG" ] || BOOT_CONFIG=/boot/config.txt
if [ -f "$BOOT_CONFIG" ]; then
    if grep -q "^dtparam=audio=on" "$BOOT_CONFIG"; then
        sudo sed -i "s/^dtparam=audio=on/dtparam=audio=off/" "$BOOT_CONFIG"
    elif ! grep -q "^dtparam=audio=off" "$BOOT_CONFIG"; then
        echo "dtparam=audio=off" | sudo tee -a "$BOOT_CONFIG" >/dev/null
    fi
fi

# cmdline.txt must stay a single line; append isolcpus to line 1 only if absent.
BOOT_CMDLINE=/boot/firmware/cmdline.txt
[ -f "$BOOT_CMDLINE" ] || BOOT_CMDLINE=/boot/cmdline.txt
if [ -f "$BOOT_CMDLINE" ] && ! grep -q "isolcpus=" "$BOOT_CMDLINE"; then
    sudo sed -i "1 s/\$/ isolcpus=3/" "$BOOT_CMDLINE"
fi

# 8. Install + enable the systemd service (runs on boot)
echo "=== Installing jetset systemd service ==="
bash bin/install-service.sh
sudo systemctl restart jetset

echo "=== Setup complete! The jetset service is enabled and running. ==="
echo "    Logs:  journalctl -u jetset -f"
echo "    (foreground debug run: \`make debug-pi\` — stop the service first)"
echo "    NOTE: reboot once to apply the sound/flicker fix: sudo reboot"
