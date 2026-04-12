"""
generate_synthetic_data.py
--------------------------
Generates all 5 synthetic NatWest-aligned datasets for PurpleInsight.

Datasets generated:
    1. regional_revenue.csv       - Monthly revenue by region/product/channel
    2. customer_metrics.csv       - Customer signups, churn, complaints by segment
    3. product_performance.csv    - Product-level performance metrics week over week
    4. cost_breakdown.csv         - Department cost breakdown by category/quarter
    5. weekly_kpis.csv            - Weekly KPI summary (signups, churn, NPS, handle time)

Usage:
    python scripts/generate_synthetic_data.py

Output:
    All CSVs saved to data/raw/
"""

import os
import random
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# ── Reproducibility ────────────────────────────────────────────────────────────
SEED = 42
random.seed(SEED)
np.random.seed(SEED)

# ── Output path ────────────────────────────────────────────────────────────────
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── Shared constants ───────────────────────────────────────────────────────────
REGIONS       = ["North", "South", "East", "West", "Scotland", "Wales"]
PRODUCTS      = ["Personal Current Account", "Savings Account", "Mortgage", "Credit Card", "Business Loan"]
CHANNELS      = ["Branch", "Mobile App", "Online", "Telephone"]
SEGMENTS      = ["Retail", "Business", "Premier", "Student"]
DEPARTMENTS   = ["Technology", "Operations", "Risk & Compliance", "Marketing", "Customer Service", "Finance"]
COST_CATS     = ["Headcount", "Infrastructure", "Software Licences", "Marketing Spend", "Training", "Outsourcing"]
QUARTERS      = ["Q1-2023", "Q2-2023", "Q3-2023", "Q4-2023", "Q1-2024", "Q2-2024", "Q3-2024", "Q4-2024"]


# ══════════════════════════════════════════════════════════════════════════════
# Dataset 1 — Regional Revenue
# ══════════════════════════════════════════════════════════════════════════════

def generate_regional_revenue() -> pd.DataFrame:
    """
    Generate monthly revenue data broken down by region, product, and channel.

    Simulates realistic banking revenue patterns including:
    - Seasonal dips in Q1
    - South region drop in Feb 2024 (maps to use case 1 example in problem doc)
    - Mobile App channel growing over time

    Returns:
        pd.DataFrame: Monthly regional revenue records (2023–2024)
    """
    records = []
    start   = datetime(2023, 1, 1)

    for month_offset in range(26):  # 24 months
        date = start + timedelta(days=30 * month_offset)
        month_str = date.strftime("%Y-%m")

        for region in REGIONS:
            for product in PRODUCTS:
                for channel in CHANNELS:

                    # Base revenue per product
                    base = {
                        "Personal Current Account": 180_000,
                        "Savings Account":          120_000,
                        "Mortgage":                 350_000,
                        "Credit Card":              90_000,
                        "Business Loan":            270_000,
                    }[product]

                    # Regional multiplier
                    region_mult = {
                        "North": 1.10, "South": 1.25, "East": 0.95,
                        "West":  0.90, "Scotland": 0.85, "Wales": 0.75
                    }[region]

                    # Channel multiplier — Mobile growing over time
                    channel_mult = {
                        "Branch":     0.95,
                        "Mobile App": 0.85 + (month_offset * 0.005),  # growing
                        "Online":     1.05,
                        "Telephone":  0.70,
                    }[channel]

                    # Seasonal factor — Q1 dip
                    seasonal = 0.88 if date.month in [1, 2] else 1.0

                    # South region ad-spend drop in Feb 2024 (mirrors problem doc example)
                    special_drop = 0.78 if (region == "South" and month_str == "2024-02") else 1.0

                    # Random noise
                    noise = np.random.normal(1.0, 0.04)

                    revenue = round(base * region_mult * channel_mult * seasonal * special_drop * noise, 2)
                    revenue = max(revenue, 0)

                    records.append({
                        "month":          month_str,
                        "region":         region,
                        "product":        product,
                        "channel":        channel,
                        "revenue":        revenue,
                        "transactions":   int(revenue / random.uniform(45, 85)),
                        "avg_ticket":     round(random.uniform(45, 85), 2),
                        "ad_spend":       round(revenue * random.uniform(0.05, 0.12), 2),
                    })

    df = pd.DataFrame(records)
    print(f"  ✓ regional_revenue.csv        → {len(df):,} rows")
    return df


# ══════════════════════════════════════════════════════════════════════════════
# Dataset 2 — Customer Metrics
# ══════════════════════════════════════════════════════════════════════════════

def generate_customer_metrics() -> pd.DataFrame:
    """
    Generate monthly customer-level metrics per segment and region.

    Includes signups, churn, complaints, NPS — aligned to use cases
    1 (what changed) and 4 (weekly/monthly summary).

    Returns:
        pd.DataFrame: Monthly customer metric records
    """
    records = []
    start   = datetime(2023, 1, 1)

    for month_offset in range(26):
        date      = start + timedelta(days=30 * month_offset)
        month_str = date.strftime("%Y-%m")

        for segment in SEGMENTS:
            for region in REGIONS:

                base_signups = {
                    "Retail": 1200, "Business": 300,
                    "Premier": 150, "Student": 800
                }[segment]

                # Student signups spike in September (university intake)
                signup_seasonal = 1.8 if (segment == "Student" and date.month == 9) else 1.0
                signups = int(base_signups * signup_seasonal * np.random.normal(1.0, 0.08))

                # Churn rate — Business segment higher churn mid-2023
                base_churn = 0.018
                if segment == "Business" and date.month in [6, 7, 8] and date.year == 2023:
                    base_churn = 0.032
                churn_count = int(signups * base_churn * np.random.normal(1.0, 0.1))

                # Complaints — spike when churn is high
                complaints = int(churn_count * random.uniform(0.3, 0.6))

                # NPS score (0–100)
                base_nps = {"Retail": 42, "Business": 38, "Premier": 61, "Student": 35}[segment]
                nps = min(100, max(0, int(base_nps + np.random.normal(0, 5))))

                # Avg handle time (seconds)
                avg_handle_time = int(np.random.normal(340, 30))

                records.append({
                    "month":            month_str,
                    "segment":          segment,
                    "region":           region,
                    "new_signups":      max(signups, 0),
                    "churned":          max(churn_count, 0),
                    "churn_rate_pct":   round(base_churn * 100, 3),
                    "complaints":       max(complaints, 0),
                    "nps_score":        nps,
                    "avg_handle_time":  avg_handle_time,
                    "active_customers": max(signups - churn_count, 0),
                })

    df = pd.DataFrame(records)
    print(f"  ✓ customer_metrics.csv        → {len(df):,} rows")
    return df


# ══════════════════════════════════════════════════════════════════════════════
# Dataset 3 — Product Performance (Week over Week)
# ══════════════════════════════════════════════════════════════════════════════

def generate_product_performance() -> pd.DataFrame:
    """
    Generate weekly product performance metrics.

    Designed to support use case 2 (compare) and use case 3 (breakdown).
    Product A (Personal Current Account) outperforms in return customer rate,
    matching the example output in the problem document.

    Returns:
        pd.DataFrame: Weekly product performance records
    """
    records = []
    start   = datetime(2023, 1, 2)  # Monday

    for week in range(104):  # 2 years of weeks
        week_start = start + timedelta(weeks=week)
        week_str   = week_start.strftime("%Y-W%W")

        for product in PRODUCTS:
            for region in REGIONS:

                base_volume = {
                    "Personal Current Account": 5000,
                    "Savings Account":          3000,
                    "Mortgage":                 800,
                    "Credit Card":              4500,
                    "Business Loan":            600,
                }[product]

                # Personal Current Account — growing return customer rate (doc example)
                return_rate = 0.62 if product == "Personal Current Account" else random.uniform(0.30, 0.55)
                return_rate += week * 0.0003  # gradual growth

                volume          = int(base_volume * np.random.normal(1.0, 0.06))
                revenue         = round(volume * random.uniform(40, 90), 2)
                new_customers   = int(volume * random.uniform(0.15, 0.35))
                return_customers= int(volume * min(return_rate, 0.85))
                conversion_rate = round(random.uniform(0.12, 0.38), 4)
                satisfaction    = round(np.random.normal(4.1, 0.3), 2)
                satisfaction    = max(1.0, min(5.0, satisfaction))

                records.append({
                    "week":                week_str,
                    "week_start_date":     week_start.strftime("%Y-%m-%d"),
                    "product":             product,
                    "region":              region,
                    "transaction_volume":  max(volume, 0),
                    "revenue":             max(revenue, 0),
                    "new_customers":       max(new_customers, 0),
                    "return_customers":    max(return_customers, 0),
                    "return_rate_pct":     round(min(return_rate, 0.85) * 100, 2),
                    "conversion_rate_pct": round(conversion_rate * 100, 2),
                    "satisfaction_score":  satisfaction,
                })

    df = pd.DataFrame(records)
    print(f"  ✓ product_performance.csv     → {len(df):,} rows")
    return df


# ══════════════════════════════════════════════════════════════════════════════
# Dataset 4 — Cost Breakdown by Department
# ══════════════════════════════════════════════════════════════════════════════

def generate_cost_breakdown() -> pd.DataFrame:
    """
    Generate quarterly cost breakdown data by department and cost category.

    Supports use case 3 (decomposition): "Show the breakdown of costs by department."
    Technology and Operations are the biggest cost contributors.

    Returns:
        pd.DataFrame: Quarterly departmental cost records
    """
    records = []

    base_costs = {
        "Technology":        2_800_000,
        "Operations":        2_100_000,
        "Risk & Compliance": 1_500_000,
        "Marketing":         900_000,
        "Customer Service":  1_200_000,
        "Finance":           750_000,
    }

    cost_cat_split = {
        "Headcount":          0.45,
        "Infrastructure":     0.18,
        "Software Licences":  0.12,
        "Marketing Spend":    0.10,
        "Training":           0.07,
        "Outsourcing":        0.08,
    }

    for quarter in QUARTERS:
        year = int(quarter.split("-")[0][1:]) + 2022  # Q1-2023 → 2023
        q_num = int(quarter[1])

        for dept in DEPARTMENTS:
            base = base_costs[dept]

            # Cost inflation over time
            inflation = 1 + (QUARTERS.index(quarter) * 0.015)

            # Marketing spends more in Q4
            seasonal = 1.20 if (dept == "Marketing" and q_num == 4) else 1.0

            total_cost = base * inflation * seasonal * np.random.normal(1.0, 0.03)

            for cat in COST_CATS:
                # Marketing dept skews heavily to Marketing Spend
                if dept == "Marketing" and cat == "Marketing Spend":
                    split = 0.40
                elif dept == "Technology" and cat == "Infrastructure":
                    split = 0.28
                else:
                    split = cost_cat_split[cat]

                cost = round(total_cost * split * np.random.normal(1.0, 0.05), 2)
                headcount = int(np.random.normal(
                    {"Technology": 120, "Operations": 200, "Risk & Compliance": 80,
                     "Marketing": 60, "Customer Service": 250, "Finance": 70}[dept],
                    10
                ))

                records.append({
                    "quarter":       quarter,
                    "department":    dept,
                    "cost_category": cat,
                    "cost_gbp":      max(cost, 0),
                    "headcount":     max(headcount, 0),
                    "budget_gbp":    round(cost * random.uniform(0.95, 1.10), 2),
                    "variance_pct":  round(np.random.normal(0, 5), 2),
                })

    df = pd.DataFrame(records)
    print(f"  ✓ cost_breakdown.csv          → {len(df):,} rows")
    return df


# ══════════════════════════════════════════════════════════════════════════════
# Dataset 5 — Weekly KPIs
# ══════════════════════════════════════════════════════════════════════════════

def generate_weekly_kpis() -> pd.DataFrame:
    """
    Generate weekly KPI summary table across all business metrics.

    Directly maps to use case 4 (summarize) output example from the problem doc:
    'Signups grew by 5%, churn remained stable, avg handle time improved by 12 seconds.'

    Returns:
        pd.DataFrame: Weekly KPI records for 2 years
    """
    records = []
    start   = datetime(2023, 1, 2)

    prev_signups     = 8500
    prev_churn_rate  = 1.8
    prev_handle_time = 342
    prev_nps         = 41

    for week in range(104):
        week_start = start + timedelta(weeks=week)
        week_str   = week_start.strftime("%Y-W%W")

        # Signups — gradual growth with noise
        signups = int(prev_signups * np.random.normal(1.005, 0.03))

        # Churn — stable with occasional spikes
        churn_rate = round(max(0.5, prev_churn_rate + np.random.normal(0, 0.08)), 3)

        # Handle time — slow improvement (efficiency gains)
        handle_time = int(max(200, prev_handle_time + np.random.normal(-0.5, 4)))

        # NPS — slow upward trend
        nps = min(100, max(0, int(prev_nps + np.random.normal(0.1, 2))))

        # Derived
        wow_signup_chg  = round(((signups - prev_signups) / prev_signups) * 100, 2)
        total_customers = int(signups * random.uniform(18, 22))  # approx active base
        complaints      = int(signups * random.uniform(0.004, 0.009))
        resolution_rate = round(random.uniform(0.82, 0.97), 4)
        digital_adoption= round(min(0.95, 0.55 + week * 0.002), 4)

        records.append({
            "week":                  week_str,
            "week_start_date":       week_start.strftime("%Y-%m-%d"),
            "new_signups":           max(signups, 0),
            "wow_signup_change_pct": wow_signup_chg,
            "churn_rate_pct":        churn_rate,
            "total_active_customers":total_customers,
            "complaints":            complaints,
            "complaint_resolution_rate": round(resolution_rate * 100, 2),
            "avg_handle_time_secs":  handle_time,
            "nps_score":             nps,
            "digital_adoption_pct":  round(digital_adoption * 100, 2),
            "net_revenue_gbp":       round(random.uniform(4_200_000, 5_800_000), 2),
        })

        prev_signups     = signups
        prev_churn_rate  = churn_rate
        prev_handle_time = handle_time
        prev_nps         = nps

    df = pd.DataFrame(records)
    print(f"  ✓ weekly_kpis.csv             → {len(df):,} rows")
    return df


# ══════════════════════════════════════════════════════════════════════════════
# Main runner
# ══════════════════════════════════════════════════════════════════════════════

def main():
    """Generate all 5 datasets and save to data/raw/."""
    print("\n PurpleInsight — Synthetic Data Generator")
    print("=" * 50)

    generators = {
        "regional_revenue.csv":    generate_regional_revenue,
        "customer_metrics.csv":    generate_customer_metrics,
        "product_performance.csv": generate_product_performance,
        "cost_breakdown.csv":      generate_cost_breakdown,
        "weekly_kpis.csv":         generate_weekly_kpis,
    }

    for filename, generator_fn in generators.items():
        df = generator_fn()
        filepath = os.path.join(OUTPUT_DIR, filename)
        df.to_csv(filepath, index=False)

    print("=" * 50)
    print(f" All datasets saved to: {os.path.abspath(OUTPUT_DIR)}")
    print("\nDataset summary:")
    for filename in generators:
        filepath = os.path.join(OUTPUT_DIR, filename)
        df = pd.read_csv(filepath)
        print(f"  {filename:<35} {len(df):>7,} rows  ×  {len(df.columns):>2} cols")
    print()


if __name__ == "__main__":
    main()