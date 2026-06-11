# Jetset — Domain Glossary

## Core Concepts

- **Display**: The LED matrix panel hardware (64×32 P2.5 HUB75) that shows flight information.
- **Home**: The user's configured location (lat/lon) — the center of their tracking area.
- **Range**: The radius around Home in which aircraft are tracked. Default 50 miles (configurable).
- **Flight**: A specific aircraft journey identified by flight number, operating between origin and destination airports.
- **Aircraft**: The physical plane — identified by registration (tail number) and type (e.g., B737, A320).
- **Tracking**: The act of monitoring flights within Range and displaying their current state on the Display.

## Flight Data Displayed

Per-flight card visible on the matrix:
- **Airline** ICAO code (e.g., "UAL", "AAL", "SWA")
- **Flight Number** (e.g., "2337")
- **Route** (origin → destination airport codes, e.g., "SFO → LAX")
- **Aircraft Type** (e.g., "B738")
- **Metrics**: Altitude (ft), Speed (knots), Track (°), Vertical Rate (ft/min)
- **Airline Logo** (optional): Small icon downsampled from airline-logos database

## Track vs Heading

- **Track**: The aircraft's actual path over the ground, measured in compass degrees. Affected by wind — differs from heading when there's a crosswind.
- **Heading**: The direction the aircraft's nose is pointing. Not directly available from OpenSky — only Track is returned.

## Flight Data Fields

- **altitude**: Current altitude in feet.
- **speed**: Current ground speed in knots.
- **track**: Ground track in degrees (see Track vs Heading above).
- **vertical_rate**: Rate of climb or descent in feet per minute. Positive = climbing, negative = descending.
- **callsign**: The flight identifier broadcast by the aircraft (e.g., "UAL2337").

## Display Layout (64 columns × 32 rows)

```
┌──────────────────────────────┐
│ UAL 2337           [logo]   │  ← row 0-7: airline + flight number
│ SFO → LAX                    │  ← row 8-14: route
│ B738                         │  ← row 15-21: aircraft type
│ ALT 35K  SPD 450             │  ← row 22-31: metrics
└──────────────────────────────┘
```

## Display Behavior

- **Mode: Single-Flight Cycle**: One flight at a time with full detail. Rotates through active flights every few seconds.
- **Tracked Flight** (stretch): A single flight the user has selected to follow specifically — skips the rotation and sticks to that flight.
- **Empty State**: When no flights are currently in Range, the display continues showing the last known flights that were in range (a historical buffer).
- **History Buffer**: The display cycles through the last N flights that were seen in Range, even after they've left Range. Size of N is configurable (default 5).
- **Refresh**: Flight data is fetched from the API periodically (TBD, likely 30-60s).
- **Cycle Interval**: Each flight card is shown for 5-7 seconds before advancing to the next.
