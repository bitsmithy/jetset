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
