#!/bin/bash
# hold-sweep.sh: Run on the Pi to see if any GPIO-timing setting lets a STATIC
# image hold steady instead of degrading.
#
# The box+X renders correctly then corrupts under sustained refresh. This sweeps
# gpio_slowdown (and a hardware-pulsing variant) holding the static box+X each
# time. Watch for a setting where the image stays STABLE for the full hold.
set -u

HOLD="${HOLD:-12}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# "gpio_slowdown disable_pulsing"
COMBOS=(
    "2 1"
    "3 1"
    "5 1"
    "6 1"
    "4 0"
)

for combo in "${COMBOS[@]}"; do
    read -r slowdown pulsing <<<"$combo"
    echo
    echo ">>> gpio_slowdown=$slowdown disable_hardware_pulsing=$pulsing  (${HOLD}s)"
    sudo -E env PATH="$PATH" uv run python "$SCRIPT_DIR/probe-hold.py" "$slowdown" "$pulsing" "$HOLD"
done

echo
echo "=== Done. Did any setting hold the box+X stable for the full duration? ==="
