#!/bin/bash
# content-sweep.sh: Run on the Pi to find the row_address_type x multiplexing
# combo that renders text cleanly on this 1/16-scan panel.
#
# Per hzeller issue #1640, 1/16-scan panels often need row_address_type=3 (and
# sometimes a multiplexing mapper). Draws the app's 4-row card in blue-free
# colors. Watch for the combo where all four rows are readable, in order, with
# no scrambling inside each row.
#
# Ctrl-C once to skip to the next combo.
set -u

HOLD="${HOLD:-12}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# "row_addr_type multiplexing" — most-likely combos first (row_addr_type=3 alone
# fixed a similar panel in issue #1640), then pair it with the column mappers.
COMBOS=(
    "3 0"
    "2 0"
    "4 0"
    "3 1"
    "3 17"
    "2 17"
    "4 17"
)

for combo in "${COMBOS[@]}"; do
    read -r addr mux <<<"$combo"
    echo
    echo ">>> row_address_type=$addr multiplexing=$mux  (${HOLD}s)"
    sudo -E env PATH="$PATH" uv run python "$SCRIPT_DIR/panel-content.py" "$addr" "$mux" "$HOLD"
done

echo
echo "=== Done. Which (row_address_type, multiplexing) showed 4 clean readable rows? ==="
