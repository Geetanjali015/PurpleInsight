"""
validate_datasets.py
--------------------
Validates all 5 PurpleInsight datasets for:
    1. Schema correctness     — right columns, right types
    2. Data completeness      — no missing values
    3. Banking realism        — values within real-world NatWest ranges
    4. Use case alignment     — each dataset supports its intended use case
    5. Cross-dataset checks   — consistency across files

Usage:
    python scripts/validate_datasets.py

Output:
    Printed validation report with PASS / WARN / FAIL per check
"""

import os
import sys
import pandas as pd
import numpy as np

# ── Path setup ────────────────────────────────────────────────────────────────
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")

# ── Counters ──────────────────────────────────────────────────────────────────
PASS = 0
WARN = 0
FAIL = 0


def passed(msg):
    global PASS
    PASS += 1
    print(f"  ✅ PASS  {msg}")


def warned(msg):
    global WARN
    WARN += 1
    print(f"  ⚠️  WARN  {msg}")


def failed(msg):
    global FAIL
    FAIL += 1
    print(f"  ❌ FAIL  {msg}")


def section(title):
    print(f"\n{'─'*55}")
    print(f"  {title}")
    print(f"{'─'*55}")


# ══════════════════════════════════════════════════════════════════════════════
# Load all datasets
# ══════════════════════════════════════════════════════════════════════════════

def load_all():
    """Load all 5 CSVs and return as a dict. Fail fast if any are missing."""
    files = {
        "regional_revenue":    "regional_revenue.csv",
        "customer_metrics":    "customer_metrics.csv",
        "product_performance": "product_performance.csv",
        "cost_breakdown":      "cost_breakdown.csv",
        "weekly_kpis":         "weekly_kpis.csv",
    }
    dfs = {}
    section("0. FILE EXISTENCE")
    for key, fname in files.items():
        path = os.path.join(DATA_DIR, fname)
        if os.path.exists(path):
            dfs[key] = pd.read_csv(path)
            passed(f"{fname} exists ({len(dfs[key]):,} rows)")
        else:
            failed(f"{fname} NOT FOUND at {path}")
            sys.exit(1)
    return dfs


# ══════════════════════════════════════════════════════════════════════════════
# 1. Schema checks
# ══════════════════════════════════════════════════════════════════════════════

def check_schemas(dfs):
    """Verify all expected columns exist in each dataset."""
    section("1. SCHEMA CORRECTNESS")

    expected = {
        "regional_revenue":    ["month", "region", "product", "channel", "revenue", "transactions", "avg_ticket", "ad_spend"],
        "customer_metrics":    ["month", "segment", "region", "new_signups", "churned", "churn_rate_pct", "complaints", "nps_score", "avg_handle_time", "active_customers"],
        "product_performance": ["week", "week_start_date", "product", "region", "transaction_volume", "revenue", "new_customers", "return_customers", "return_rate_pct", "conversion_rate_pct", "satisfaction_score"],
        "cost_breakdown":      ["quarter", "department", "cost_category", "cost_gbp", "headcount", "budget_gbp", "variance_pct"],
        "weekly_kpis":         ["week", "week_start_date", "new_signups", "wow_signup_change_pct", "churn_rate_pct", "total_active_customers", "complaints", "complaint_resolution_rate", "avg_handle_time_secs", "nps_score", "digital_adoption_pct", "net_revenue_gbp"],
    }

    for name, cols in expected.items():
        df = dfs[name]
        missing = [c for c in cols if c not in df.columns]
        if not missing:
            passed(f"{name}: all {len(cols)} columns present")
        else:
            failed(f"{name}: missing columns → {missing}")


# ══════════════════════════════════════════════════════════════════════════════
# 2. Completeness checks
# ══════════════════════════════════════════════════════════════════════════════

def check_completeness(dfs):
    """Check for nulls and empty values."""
    section("2. DATA COMPLETENESS (No Nulls)")

    for name, df in dfs.items():
        null_counts = df.isnull().sum()
        total_nulls = null_counts.sum()
        if total_nulls == 0:
            passed(f"{name}: zero null values")
        else:
            cols_with_nulls = null_counts[null_counts > 0].to_dict()
            failed(f"{name}: {total_nulls} nulls found → {cols_with_nulls}")


# ══════════════════════════════════════════════════════════════════════════════
# 3. Banking realism checks
# ══════════════════════════════════════════════════════════════════════════════

def check_realism(dfs):
    """
    Validate values are within realistic NatWest / UK banking ranges.
    Sources: UK Finance annual report, Bank of England statistics (public).
    """
    section("3. BANKING REALISM CHECKS")

    # ── Regional Revenue ──────────────────────────────────────────────────────
    rr = dfs["regional_revenue"]

    # Revenue per row should be between £10k and £800k (branch/channel slice)
    rev_min, rev_max = rr["revenue"].min(), rr["revenue"].max()
    if 10_000 <= rev_min and rev_max <= 800_000:
        passed(f"regional_revenue: revenue range £{rev_min:,.0f} – £{rev_max:,.0f} ✓ realistic")
    else:
        warned(f"regional_revenue: revenue range £{rev_min:,.0f} – £{rev_max:,.0f} — check outliers")

    # All regions present
    expected_regions = {"North", "South", "East", "West", "Scotland", "Wales"}
    actual_regions   = set(rr["region"].unique())
    if expected_regions == actual_regions:
        passed(f"regional_revenue: all 6 UK regions present")
    else:
        failed(f"regional_revenue: missing regions → {expected_regions - actual_regions}")

    # South region Feb 2024 drop (mirrors problem doc example)
    south_jan = rr[(rr["region"] == "South") & (rr["month"] == "2024-01")]["revenue"].sum()
    south_feb = rr[(rr["region"] == "South") & (rr["month"] == "2024-02")]["revenue"].sum()
    if south_jan > 0:
        drop_pct = ((south_jan - south_feb) / south_jan) * 100
        if 15 <= drop_pct <= 35:
            passed(f"regional_revenue: South region Feb 2024 drop = {drop_pct:.1f}% ✓ matches problem doc example")
        else:
            warned(f"regional_revenue: South Feb 2024 drop = {drop_pct:.1f}% (expected ~22%)")

    # ── Customer Metrics ──────────────────────────────────────────────────────
    cm = dfs["customer_metrics"]

    # Churn rate should be 0.5%–5% for retail banking (industry standard)
    churn_min = cm["churn_rate_pct"].min()
    churn_max = cm["churn_rate_pct"].max()
    if 0.5 <= churn_min and churn_max <= 5.0:
        passed(f"customer_metrics: churn rate {churn_min:.2f}%–{churn_max:.2f}% ✓ realistic (UK banking: 1–3%)")
    else:
        warned(f"customer_metrics: churn rate {churn_min:.2f}%–{churn_max:.2f}% — outside typical UK range")

    # NPS 0–100
    nps_min = cm["nps_score"].min()
    nps_max = cm["nps_score"].max()
    if 0 <= nps_min and nps_max <= 100:
        passed(f"customer_metrics: NPS scores {nps_min}–{nps_max} ✓ valid range")
    else:
        failed(f"customer_metrics: NPS out of 0–100 range → min={nps_min}, max={nps_max}")

    # Student signups spike in September
    student_sep = cm[(cm["segment"] == "Student") & (cm["month"].str.endswith("-09"))]["new_signups"].mean()
    student_avg = cm[cm["segment"] == "Student"]["new_signups"].mean()
    if student_sep > student_avg * 1.3:
        passed(f"customer_metrics: Student September spike confirmed ({student_sep:.0f} vs avg {student_avg:.0f}) ✓ realistic")
    else:
        warned(f"customer_metrics: Student September spike weak — {student_sep:.0f} vs avg {student_avg:.0f}")

    # ── Product Performance ───────────────────────────────────────────────────
    pp = dfs["product_performance"]

    # Return rate 10%–90%
    rr_min = pp["return_rate_pct"].min()
    rr_max = pp["return_rate_pct"].max()
    if 10 <= rr_min and rr_max <= 90:
        passed(f"product_performance: return rate {rr_min:.1f}%–{rr_max:.1f}% ✓ realistic")
    else:
        warned(f"product_performance: return rate {rr_min:.1f}%–{rr_max:.1f}% — check range")

    # Satisfaction 1–5
    sat_min = pp["satisfaction_score"].min()
    sat_max = pp["satisfaction_score"].max()
    if 1.0 <= sat_min and sat_max <= 5.0:
        passed(f"product_performance: satisfaction scores {sat_min:.2f}–{sat_max:.2f} ✓ valid 1–5 scale")
    else:
        failed(f"product_performance: satisfaction out of 1–5 range")

    # Personal Current Account should have highest return rate
    pca_rate = pp[pp["product"] == "Personal Current Account"]["return_rate_pct"].mean()
    other_rate = pp[pp["product"] != "Personal Current Account"]["return_rate_pct"].mean()
    if pca_rate > other_rate:
        passed(f"product_performance: Personal Current Account highest return rate ({pca_rate:.1f}% vs {other_rate:.1f}%) ✓ matches doc example")
    else:
        warned(f"product_performance: Personal Current Account return rate not highest ({pca_rate:.1f}% vs {other_rate:.1f}%)")

    # ── Cost Breakdown ────────────────────────────────────────────────────────
    cb = dfs["cost_breakdown"]

    # Costs should be positive
    neg_costs = (cb["cost_gbp"] < 0).sum()
    if neg_costs == 0:
        passed(f"cost_breakdown: all costs positive ✓")
    else:
        failed(f"cost_breakdown: {neg_costs} negative cost values found")

    # Technology should be highest cost dept (realistic for a bank)
    dept_costs = cb.groupby("department")["cost_gbp"].sum()
    top_dept   = dept_costs.idxmax()
    if top_dept == "Technology":
        passed(f"cost_breakdown: Technology is highest cost dept ({dept_costs[top_dept]:,.0f} GBP) ✓ realistic for NatWest")
    else:
        warned(f"cost_breakdown: top cost dept is {top_dept} — expected Technology")

    # ── Weekly KPIs ───────────────────────────────────────────────────────────
    wk = dfs["weekly_kpis"]

    # Handle time 200–500 seconds (realistic call centre range)
    ht_min = wk["avg_handle_time_secs"].min()
    ht_max = wk["avg_handle_time_secs"].max()
    if 200 <= ht_min and ht_max <= 500:
        passed(f"weekly_kpis: avg handle time {ht_min}–{ht_max}s ✓ realistic (UK bank call centre: ~340s)")
    else:
        warned(f"weekly_kpis: avg handle time {ht_min}–{ht_max}s — outside typical 200–500s range")

    # Digital adoption should grow over time
    first_8  = wk.head(8)["digital_adoption_pct"].mean()
    last_8   = wk.tail(8)["digital_adoption_pct"].mean()
    if last_8 > first_8:
        passed(f"weekly_kpis: digital adoption growing {first_8:.1f}% → {last_8:.1f}% ✓ realistic trend")
    else:
        warned(f"weekly_kpis: digital adoption not growing ({first_8:.1f}% → {last_8:.1f}%)")

    # Net revenue range (weekly, whole bank) — £4M–£6M realistic slice
    rev_min = wk["net_revenue_gbp"].min()
    rev_max = wk["net_revenue_gbp"].max()
    if 3_000_000 <= rev_min and rev_max <= 7_000_000:
        passed(f"weekly_kpis: weekly net revenue £{rev_min/1e6:.1f}M–£{rev_max/1e6:.1f}M ✓ realistic")
    else:
        warned(f"weekly_kpis: weekly net revenue £{rev_min/1e6:.1f}M–£{rev_max/1e6:.1f}M — check range")


# ══════════════════════════════════════════════════════════════════════════════
# 4. Use case alignment
# ══════════════════════════════════════════════════════════════════════════════

def check_use_case_alignment(dfs):
    """Confirm each dataset can answer its intended use case queries."""
    section("4. USE CASE ALIGNMENT")

    # Use case 1 — "Why did revenue drop last month?"
    rr = dfs["regional_revenue"]
    months = rr["month"].nunique()
    if months >= 24:
        passed(f"Use Case 1 (Change Analysis): {months} months of revenue data ✓ trend analysis ready")
    else:
        warned(f"Use Case 1: only {months} months — need 24+ for meaningful trend")

    # Use case 2 — "This week vs last week / Region A vs B"
    pp = dfs["product_performance"]
    weeks = pp["week"].nunique()
    regions = pp["region"].nunique()
    if weeks >= 52 and regions >= 4:
        passed(f"Use Case 2 (Compare): {weeks} weeks × {regions} regions ✓ comparison ready")
    else:
        warned(f"Use Case 2: {weeks} weeks, {regions} regions — more data recommended")

    # Use case 3 — "Show breakdown of costs by department"
    cb = dfs["cost_breakdown"]
    depts = cb["department"].nunique()
    cats  = cb["cost_category"].nunique()
    if depts >= 5 and cats >= 5:
        passed(f"Use Case 3 (Breakdown): {depts} departments × {cats} cost categories ✓ decomposition ready")
    else:
        warned(f"Use Case 3: {depts} depts, {cats} categories — need 5+ each")

    # Use case 4 — "Give me a weekly summary"
    wk = dfs["weekly_kpis"]
    kpi_cols = ["new_signups", "churn_rate_pct", "avg_handle_time_secs", "nps_score"]
    all_present = all(c in wk.columns for c in kpi_cols)
    if all_present and len(wk) >= 52:
        passed(f"Use Case 4 (Summarize): {len(wk)} weeks of KPIs ✓ summary ready")
    else:
        warned(f"Use Case 4: missing KPI columns or insufficient weeks")


# ══════════════════════════════════════════════════════════════════════════════
# 5. Cross-dataset consistency
# ══════════════════════════════════════════════════════════════════════════════

def check_cross_dataset(dfs):
    """Check consistency across datasets."""
    section("5. CROSS-DATASET CONSISTENCY")

    # Same regions in regional_revenue and customer_metrics
    rr_regions = set(dfs["regional_revenue"]["region"].unique())
    cm_regions = set(dfs["customer_metrics"]["region"].unique())
    if rr_regions == cm_regions:
        passed(f"Regions consistent across regional_revenue and customer_metrics ✓")
    else:
        warned(f"Region mismatch: revenue={rr_regions}, customers={cm_regions}")

    # Same products in regional_revenue and product_performance
    rr_products = set(dfs["regional_revenue"]["product"].unique())
    pp_products = set(dfs["product_performance"]["product"].unique())
    if rr_products == pp_products:
        passed(f"Products consistent across regional_revenue and product_performance ✓")
    else:
        warned(f"Product mismatch: revenue={rr_products}, performance={pp_products}")

    # Date ranges overlap — revenue and customer metrics both cover 2023–2024
    rr_months = sorted(dfs["regional_revenue"]["month"].unique())
    cm_months = sorted(dfs["customer_metrics"]["month"].unique())
    if rr_months[0] == cm_months[0] and rr_months[-1] == cm_months[-1]:
        passed(f"Date ranges aligned: {rr_months[0]} → {rr_months[-1]} ✓")
    else:
        warned(f"Date range mismatch: revenue {rr_months[0]}–{rr_months[-1]}, customers {cm_months[0]}–{cm_months[-1]}")


# ══════════════════════════════════════════════════════════════════════════════
# Final summary
# ══════════════════════════════════════════════════════════════════════════════

def print_summary():
    """Print final validation report."""
    total = PASS + WARN + FAIL
    print(f"\n{'═'*55}")
    print(f"  VALIDATION SUMMARY")
    print(f"{'═'*55}")
    print(f"  Total checks : {total}")
    print(f"  PASS      : {PASS}")
    print(f"   WARN      : {WARN}")
    print(f"  FAIL      : {FAIL}")
    print(f"{'═'*55}")

    if FAIL == 0 and WARN == 0:
        print("  ALL CHECKS PASSED — data is production ready")
    elif FAIL == 0:
        print("  PASSED WITH WARNINGS — review warnings above")
    else:
        print("   FAILURES FOUND — re-run generate_synthetic_data.py")
    print()


# ══════════════════════════════════════════════════════════════════════════════
# Main
# ══════════════════════════════════════════════════════════════════════════════

def main():
    """Run all validation checks on PurpleInsight datasets."""
    print("\nPurpleInsight — Dataset Validator")
    print("=" * 55)

    dfs = load_all()
    check_schemas(dfs)
    check_completeness(dfs)
    check_realism(dfs)
    check_use_case_alignment(dfs)
    check_cross_dataset(dfs)
    print_summary()


if __name__ == "__main__":
    main()