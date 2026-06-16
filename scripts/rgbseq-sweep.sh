#!/bin/bash
# rgbseq-sweep.sh: Run on the Pi to find the panel's subpixel order.
#
# Solid color fills came out misordered/blank. This sweeps all six
# led_rgb_sequence permutations, showing solid RED/GREEN/BLUE for each. Watch
# for the sequence where red->red, green->green, blue->blue. If BLUE never
# lights under any sequence, the blue channel is a hardware fault (cable/panel).
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

for seq in RGB RBG GRB GBR BRG BGR; do
    echo
    echo ">>> led_rgb_sequence=$seq"
    sudo -E env PATH="$PATH" uv run python "$SCRIPT_DIR/panel-rgbseq.py" "$seq"
done

echo
echo "=== Done. Which sequence (if any) showed red=red, green=green, blue=blue? ==="
echo "=== If blue NEVER appeared, the blue channel is a hardware fault. ==="
