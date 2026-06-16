#!/bin/bash
# panel-diag.sh: Run on the Pi to find working LED panel flags.
#
# Drives the rpi-rgb-led-matrix `demo` binary (a moving square across the WHOLE
# panel) through a sweep of hardware options. Watch the panel during each step
# and note which label — if any — renders a clean, full-panel square.
#
# This isolates the panel/wiring from the jetset app: if NO combo renders
# cleanly, the problem is hardware (cable, power, mapping); if one does, copy
# its flags into config.yaml's `hardware` section.
set -u

DEMO="${DEMO:-$HOME/rpi-rgb-led-matrix/examples-api-use/demo}"
if [ ! -x "$DEMO" ]; then
    echo "ERROR: demo binary not found at $DEMO"
    echo "Build it first: (cd ~/rpi-rgb-led-matrix && make -j4)"
    exit 1
fi

# Shared flags: single 64x32 panel on the Adafruit HAT (no PWM solder mod),
# moving-square demo (-D0). Each run is capped at 8s via `timeout` because this
# demo build has no -t flag.
RUN_SECONDS="${RUN_SECONDS:-8}"
COMMON=(-D0 --led-rows=32 --led-cols=64 --led-chain=1
        --led-gpio-mapping=adafruit-hat --led-no-hardware-pulse
        --led-slowdown-gpio=4)

# label : extra flags to test on top of COMMON
VARIANTS=(
    "baseline (no panel-type)         :"
    "panel-type FM6126A               :--led-panel-type=FM6126A"
    "panel-type FM6127                :--led-panel-type=FM6127"
    "row-addr-type 1                  :--led-row-addr-type=1"
    "multiplexing 1 (Stripe)          :--led-multiplexing=1"
    "slower GPIO (slowdown=2)         :--led-slowdown-gpio=2"
    "slower GPIO (slowdown=6)         :--led-slowdown-gpio=6"
)

echo "=== Panel diagnostic sweep — watch the panel, note the clean one ==="
for entry in "${VARIANTS[@]}"; do
    label="${entry%%:*}"
    extra="${entry#*:}"
    echo
    echo ">>> Testing: $label  (${RUN_SECONDS}s)"
    # `timeout` sends SIGTERM after RUN_SECONDS; the demo exits on it.
    # shellcheck disable=SC2086
    sudo timeout "$RUN_SECONDS" "$DEMO" "${COMMON[@]}" $extra
done

echo
echo "=== Done. Tell me which label showed a clean full-panel moving square. ==="
