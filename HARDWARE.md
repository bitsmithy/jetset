# Jetset — Hardware Build Plan

> A DIY live flight tracking LED display.

## Bill of Materials

| # | Item | Price | Link | Notes |
|---|------|-------|------|-------|
| 1 | **Raspberry Pi 3 A+** | **$25.00** | [Adafruit](https://www.adafruit.com/product/4027) | Quad-core 1.4GHz, WiFi built-in, GPIO pre-soldered |
| 2 | **RGB Matrix HAT + RTC** | **$24.95** | [Adafruit](https://www.adafruit.com/product/2345) | Level shifter + real-time clock; plugs directly onto Pi's GPIO |
| 3 | **5V 4A Power Supply** (UL listed) | **$14.95** | [Adafruit](https://www.adafruit.com/product/1466) | Powers the LED panel via the HAT's barrel jack |
| 4 | **P2.5 64×32 HUB75 LED Panel** | ~$22 | [Amazon](https://www.amazon.com/dp/B0BRBGHFKQ) | 64×32 resolution, 2.5mm pitch, 160mm × 80mm |
| 5 | **32GB microSD Card** (Class 10) | ~$8 | [Amazon](https://www.amazon.com/s?k=32gb+microsd+card+class+10) | For Raspberry Pi OS + code |
| 6 | **Micro USB Cable** | ~$4 | [Adafruit](https://www.adafruit.com/product/898) | Powers the Pi 3 A+ (any micro USB cable works) |
| | **Total** | **~$99** | | |

## Connection Diagram

```
                         ┌──────────────────────────┐
                         │      P2.5 LED Panel      │
                         │   64×32 HUB75 (P2.5)     │
                         │  160mm × 80mm            │
                         └──────────┬───────────────┘
                                    │ 16-pin IDC ribbon cable
                         ┌──────────┴───────────────┐
                         │   RGB Matrix HAT + RTC   │
                         │   (Adafruit 2345)        │
                         │                          │
                         │  ┌────────────────────┐  │
                         │  │ 5V / GND screw     │  │
                         │  │ terminal (panel     │  │
                         │  │ power input)        │  │
                         │  └────────────────────┘  │
                         │           │              │
                         │      ╔════╧════╗         │
                         │      ║ DC jack ║         │
                         │      ╚════════╝         │
                         └──────────┬───────────────┘
                                    │ 40-pin GPIO header
                         ┌──────────┴───────────────┐
                         │   Raspberry Pi 3 A+      │
                         │                          │
                         │  micro USB (power)        │
                         └──────────┬───────────────┘
                                    │ micro USB cable
                         ┌──────────┴───────────────┐
                         │  Phone charger or         │
                         │  5V 2.5A USB power supply │
                         └──────────────────────────┘
```

## Why Pi 3 A+?

| Factor | Pi Zero 2 W | Pi 3 A+ |
|--------|------------|---------|
| **Availability** | ❌ Sold out everywhere | ✅ In stock (Adafruit) |
| **Price** | ~$17 (if you can find one) | **$25** |
| **GPIO header** | ❌ Not soldered | ✅ Pre-soldered |
| **CPU** | Quad-core 1GHz | Quad-core **1.4GHz** |
| **Soldering needed?** | Yes (GPIO header) | **No** |

## Assembly Steps

1. Flash Raspberry Pi OS Lite to microSD, pre-configure WiFi + SSH
2. Attach RGB Matrix HAT to Pi's GPIO header (press firmly)
3. Connect panel via IDC ribbon cable to HAT
4. Plug 5V 4A supply into HAT's barrel jack (powers panel)
5. Plug micro USB into Pi from phone charger (powers Pi)
6. SSH in, install software, run

## Panel notes & troubleshooting

Hard-won lessons from bring-up:

- **A healthy, properly-powered panel needs no tuning.** The app sets only the
  `adafruit-hat` mapping and runs on rpi-rgb-led-matrix defaults (gpio_slowdown,
  multiplexing, row_address_type, rgb_sequence, pwm_bits). Early bring-up *seemed*
  to need gpio_slowdown 5 and an RBG sequence, but that was the power-starvation
  artefact below — once the panel was powered through its own header, defaults
  rendered cleanly. If a future panel ever misbehaves, those knobs live in
  rpi-rgb-led-matrix; re-add the ones you need in `src/jetset/__main__.py`.
- **Use INDOOR, standard 1/16-scan panels.** They map 1:1 on the defaults.
  **Avoid OUTDOOR / multiplexed panels** — their scrambled internal wiring needs
  a custom multiplex-mapper compiled into rpi-rgb-led-matrix (hzeller #1640).
- **Power the panel through its OWN power header (VH4 / 4-pin), not the ribbon.**
  The 16-pin HUB75 ribbon carries DATA + ground only — *not* the LEDs' 5V. Fed
  only through the ribbon, the panel starves on parasitic ground current and the
  symptom mimics a dead panel: red (lowest forward voltage) limps on, green
  weak, blue dead, white collapses to red. We chased this as a "faulty panel"
  across two panels + a new ribbon — it was always the VH4 power header not
  being wired to 5V. Wire it and every channel works. Capacity isn't the issue
  (the panel is ≤12W / 2.5A); a missing/starved power-header connection is.
- **Bring-up tooling:** `scripts/panel-colors.py` (solid red/green/blue/white
  fills to confirm the three channels) and `scripts/probe-text.py` (the real
  4-row text layout) drive a panel directly via rgbmatrix, independent of the
  app. Run colors first, then text. (The many one-off probes/sweeps used to
  characterize the original faulty panel were removed once diagnosed — see git
  history if you need them again.)

### Verifying a new panel

When swapping in a replacement panel (reuse the same HAT + ribbon cable):

1. **Power:** wire the panel's own power header (VH4 / 4-pin) to 5V — the ribbon
   does NOT carry LED power. A red-only / blue-dead / white→red panel is almost
   always starved here, not faulty.
2. `make deploy`
3. **Channels:** `sudo -E env PATH=$PATH uv run python scripts/panel-colors.py`
   - red→red, green→green, **blue→blue**, white→white. A *dead/dim* channel ⇒
     power (step 1) or the HAT/cable. A *swapped* channel ⇒ the panel's subpixel
     order differs; re-add `led_rgb_sequence` in `backend.build_matrix` to fix it.
4. **Geometry + combination colors:** `... scripts/probe-text.py white`
   - four stable rows, and white renders white (no collapse-to-red / garbling).
5. **Live app:** `make run-pi` — confirm flight cards render in full colour.
