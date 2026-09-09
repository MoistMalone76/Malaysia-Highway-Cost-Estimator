# Highway Cost Estimator

A single-page calculator for Peninsular Malaysia expressway trips. Pick an entry and exit toll plaza, choose a vehicle, and see toll, fuel, and EV charging costs update live.

Built from a Malaysian highway cost estimator spreadsheet — the distance, toll, and energy formulas are reproduced exactly in the page's JavaScript.

## Features

- 91 toll plazas across the North, Central, South, and East regions
- 27 vehicle models covering petrol, diesel, hybrid, and electric
- Toll cost calculated from plaza-to-plaza distance at a flat rate (RM0.1088/km)
- Fuel cost for petrol/diesel/hybrid vehicles, or home/public AC/public DC charging cost for EVs
- Everything recalculates instantly as you change a dropdown — no submit button, no build step, no dependencies beyond a Google Fonts import

## Usage

Open `index.html` in any browser. That's it — it's a static, self-contained page.

To publish with GitHub Pages:

1. Push this repo to GitHub
2. Go to **Settings → Pages**
3. Under **Source**, select the branch (usually `main`) and root folder
4. Save — your site will be live at `https://<your-username>.github.io/<repo-name>/`

## How the numbers are calculated

- **Distance:** if entry and exit plazas are in the same region, distance is the difference between their distances from KL; if they're in different regions, it's the sum of both distances plus a 15 km connector.
- **Toll:** distance × RM0.1088/km.
- **Fuel/energy cost:** (distance ÷ 100) × vehicle consumption × price per unit (RM/L or RM/kWh).
- **EV charging split:** if an EV is charged at home, the cost is shown as "Home charging"; if charged at a public AC or DC station, it's shown separately as "Public charging."

Energy prices reflect Malaysia benchmark rates at the time of writing (~RM0.50/kWh home, ~RM1.10/kWh public AC, ~RM1.50/kWh public DC) and will drift from actual operator/TNB tariffs over time.

## Disclaimer

Toll and energy costs are estimates only, based on modelled rates and straight-line plaza distances. Actual concessionaire tolls and charging tariffs vary by vehicle class, operator, site, and time.
