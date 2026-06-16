#!/bin/bash
# mux-sweep.sh: Run on the Pi to find the panel's multiplexing type.
#
# Solid fills render fine but sparse content (text/lines) garbles — a
# pixel-mapping mismatch. This sweeps every multiplexing type (0-17), drawing a
# border + text each time. Watch for the value that yields a CLEAN rectangle
# border and READABLE "AbCd12", then put it in config.yaml as hardware.multiplexing.
#
# Ctrl-C once to skip to the next value; Ctrl-C twice quickly to abort.
set -u

HOLD="${HOLD:-6}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

for mux in $(seq 0 17); do
    echo
    echo ">>> Testing multiplexing=$mux  (${HOLD}s) — clean border + readable text?"
    sudo -E env PATH="$PATH" uv run python "$SCRIPT_DIR/panel-mux.py" "$mux" "$HOLD"
done

echo
echo "=== Done. Tell me which multiplexing value rendered a clean border + readable text. ==="
