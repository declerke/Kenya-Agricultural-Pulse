"""
Kenya Agricultural Pulse — Data Pipeline
Fetches World Bank WDI indicators for Kenya + EA peers 2000-2024
via the standard REST API (v2).
Run: python data_pipeline.py
"""

import requests
import pandas as pd
import os
import time

COUNTRIES = ['KE', 'UG', 'TZ', 'ET', 'NG']
COUNTRY_NAMES = {
    'KE': 'Kenya',
    'UG': 'Uganda',
    'TZ': 'Tanzania',
    'ET': 'Ethiopia',
    'NG': 'Nigeria',
}
COUNTRY_ISO3 = {
    'KEN': 'KE', 'UGA': 'UG', 'TZA': 'TZ', 'ETH': 'ET', 'NGA': 'NG',
}

INDICATORS = {
    'AG.PRD.FOOD.XD':    'Food Production Index',
    'AG.PRD.LVSK.XD':    'Livestock Production Index',
    'AG.YLD.CREL.KG':    'Cereal Yield (kg/ha)',
    'AG.LND.ARBL.ZS':    'Arable Land (% land)',
    'AG.LND.AGRI.ZS':    'Agricultural Land (% land)',
    'NV.AGR.TOTL.ZS':    'Agriculture % GDP',
    'SL.AGR.EMPL.ZS':    'Agricultural Employment %',
    'SN.ITK.DEFC.ZS':    'Undernourishment Rate (%)',
    'TM.VAL.FOOD.ZS.UN': 'Food Imports % Merch Imports',
    'TX.VAL.FOOD.ZS.UN': 'Food Exports % Merch Exports',
    'AG.CON.FERT.ZS':    'Fertilizer Consumption (kg/ha)',
    'SP.RUR.TOTL.ZS':    'Rural Population %',
    'NE.IMP.GNFS.CD':    'Imports Goods Services (USD)',
    'SP.POP.TOTL':       'Population',
}

WB_BASE = 'https://api.worldbank.org/v2/country'

# Indicators that 400 on multi-country requests — fetch one country at a time
SINGLE_COUNTRY_INDICATORS = {'AG.PRD.FOOD.XD', 'AG.PRD.LVSK.XD'}


def _fetch_records(url: str, timeout: int = 45) -> list:
    """Fetch all pages from a WB API URL and return raw records list."""
    resp = requests.get(url, timeout=timeout)
    resp.raise_for_status()
    payload = resp.json()
    if len(payload) < 2 or payload[1] is None:
        return []
    records = list(payload[1])
    total_pages = payload[0].get('pages', 1)
    if total_pages > 1:
        for page in range(2, total_pages + 1):
            r2 = requests.get(url + f"&page={page}", timeout=timeout)
            r2.raise_for_status()
            p2 = r2.json()
            if len(p2) >= 2 and p2[1]:
                records.extend(p2[1])
    return records


def fetch_indicator(code: str, label: str) -> pd.DataFrame | None:
    """Fetch one indicator for all countries, years 2000-2024."""
    try:
        all_records = []

        if code in SINGLE_COUNTRY_INDICATORS:
            # Fetch one country at a time to avoid 400 errors
            for country in COUNTRIES:
                url = (
                    f"{WB_BASE}/{country}/indicator/{code}"
                    f"?format=json&per_page=500&date=2000:2024"
                )
                recs = _fetch_records(url)
                all_records.extend(recs)
                time.sleep(0.2)
        else:
            country_str = ';'.join(COUNTRIES)
            url = (
                f"{WB_BASE}/{country_str}/indicator/{code}"
                f"?format=json&per_page=2000&date=2000:2024"
            )
            all_records = _fetch_records(url)

        if not all_records:
            print(f"  No data: {label}")
            return None

        rows = []
        for rec in all_records:
            iso3 = rec.get('countryiso3code', '')
            economy = COUNTRY_ISO3.get(iso3)
            if economy is None:
                continue
            year = int(rec['date'])
            value = rec['value']  # may be None
            rows.append({'economy': economy, 'year': year, label: value})

        if not rows:
            print(f"  Empty rows: {label}")
            return None

        df = pd.DataFrame(rows)
        non_null = df[label].notna().sum()
        print(f"  Fetched: {label:<45}  {non_null}/{len(df)} non-null")
        return df

    except Exception as e:
        print(f"  Skipped {code} ({label}): {e}")
        return None


def fetch_all():
    os.makedirs('data/processed', exist_ok=True)
    frames = []

    for code, label in INDICATORS.items():
        df = fetch_indicator(code, label)
        if df is not None:
            frames.append(df)
        time.sleep(0.3)  # be polite to the API

    if not frames:
        raise RuntimeError("No data fetched — check internet connection.")

    # Build a base of all country-year combos
    base_rows = []
    for eco in COUNTRIES:
        for yr in range(2000, 2025):
            base_rows.append({'economy': eco, 'year': yr})
    result = pd.DataFrame(base_rows)

    for f in frames:
        result = result.merge(f, on=['economy', 'year'], how='left')

    result['country'] = result['economy'].map(COUNTRY_NAMES)
    result = result.sort_values(['economy', 'year']).reset_index(drop=True)

    out_path = 'data/processed/agri.parquet'
    result.to_parquet(out_path, index=False)

    # Coverage report for Kenya
    ke = result[result['economy'] == 'KE']
    print(f"\n=== Kenya data coverage ===")
    for label in list(INDICATORS.values()):
        if label in ke.columns:
            non_null = ke[label].notna().sum()
            bar = '#' * non_null + '.' * (25 - non_null)
            print(f"  {label:<42} {non_null:>2}/25  [{bar}]")

    print(f"\nSaved {len(result)} rows total")
    print(f"Year range: {result['year'].min()}–{result['year'].max()}")
    print(f"Countries: {sorted(result['economy'].unique())}")
    return result


if __name__ == '__main__':
    print("Fetching World Bank agricultural data (2000-2024)...")
    print(f"Indicators: {len(INDICATORS)}, Countries: {COUNTRIES}\n")
    fetch_all()
    print("\nPipeline complete.")
