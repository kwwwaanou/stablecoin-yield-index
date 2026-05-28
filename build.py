#!/usr/bin/env python3
"""Fetch DeFiLlama yield data and generate the yield dashboard HTML."""

import json
import urllib.request
import os
import time

POOLS = {
    "fxSAVE (fx Protocol)": "705cbd88-5428-4973-adc9-d8ca7b4aa1a4",
    "Fluid USD Lite": "488f06db-5a36-450e-9ba9-b4321be39c7c",
    "limUSD (Liminal)": "e0ab5e92-79be-4e00-aa28-a2447db45282",
    "feUSD HYPE (Felix)": "2bae7cf8-d278-4b27-9959-7f5f92c6f14b",
    "feUSD BTC (Felix)": "d2a0cae6-7a65-4c1c-9995-327ddbcfb37f",
    "AAVE USDC": "aa70268e-4b52-42bf-a116-608b370f9501",
    "Fluid USDC": "4438dabc-7f0c-430b-8136-2722711ae663",
}

CUTOFF_DATE = "2025-04-28"
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "yield_dashboard.html")


def fetch_chart(pool_id):
    url = f"https://yields.llama.fi/chart/{pool_id}"
    for attempt in range(3):
        try:
            with urllib.request.urlopen(url, timeout=30) as resp:
                data = json.loads(resp.read())
            return [
                [d["timestamp"][:10], d["apy"], d["tvlUsd"]]
                for d in data.get("data", [])
                if d.get("apy", 0) > 0
            ]
        except Exception as e:
            if attempt < 2:
                time.sleep(2)
            else:
                raise e
    return []


def main():
    print("Fetching yield data from DeFiLlama...")
    all_data = {}
    for name, pool_id in POOLS.items():
        print(f"  {name}...", end=" ", flush=True)
        series = fetch_chart(pool_id)
        # Trim old data to keep file size reasonable
        if name in ("AAVE USDC", "Fluid USDC", "fxSAVE (fx Protocol)"):
            series = [p for p in series if p[0] >= CUTOFF_DATE]
        all_data[name] = series
        last = series[-1] if series else [None, 0, 0]
        print(f"{len(series)} pts | APY={last[1]:.2f}% | TVL=${last[2]:,.0f}")

    with open(OUTPUT_FILE) as f:
        template = f.read()

    # Replace the embedded data
    data_line_start = 'var ALL_DATA = '
    data_line_end = ';\n\nvar POOLS = ['
    start_idx = template.index(data_line_start)
    end_idx = template.index(data_line_end, start_idx)

    new_data = f"var ALL_DATA = {json.dumps(all_data)}"
    new_html = template[:start_idx] + new_data + template[end_idx:]

    # Inject refresh timestamp
    from datetime import datetime, timezone
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    new_html = new_html.replace("REFRESH_TIMESTAMP", ts)

    with open(OUTPUT_FILE, "w") as f:
        f.write(new_html)

    total_pts = sum(len(v) for v in all_data.values())
    print(f"\nDone! Written {len(new_html):,} bytes, {total_pts} total data points.")


if __name__ == "__main__":
    main()
