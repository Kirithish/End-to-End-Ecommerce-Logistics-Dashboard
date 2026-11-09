"""EDA and statistical tests for the last-mile delivery project.

Usage:  python eda_analysis.py [path_to_enriched_csv]
Needs:  pandas, numpy, scipy   (pip install pandas numpy scipy)
Input:  amazon_delivery_enriched.csv (made by build_enriched.py)
Output: printed report, also saved to eda_results.txt
"""
import sys
import numpy as np
import pandas as pd
from scipy import stats

PATH = sys.argv[1] if len(sys.argv) > 1 else "amazon_delivery_enriched.csv"
LATE_MIN = 160
OUT = []


def say(text=""):
    print(text)
    OUT.append(str(text))


def section(title):
    say("\n" + "=" * 70)
    say(title)
    say("=" * 70)


def group_table(df, col, order=None, min_n=100):
    g = (df.groupby(col, observed=True)
           .agg(deliveries=("late_flag", "size"), avg_minutes=("delivery_time", "mean"),
                late_rate=("late_flag", "mean")).round(3))
    g = g[g.deliveries >= min_n]
    if order:
        g = g.reindex([o for o in order if o in g.index])
    return g


def mann_whitney(a, b, label_a, label_b):
    """Mann-Whitney U test with rank-biserial effect size and median gap."""
    u, p = stats.mannwhitneyu(a, b, alternative="two-sided")
    r = 2 * u / (len(a) * len(b)) - 1  # rank-biserial: >0 means a tends to be larger
    say(f"  {label_a} (n={len(a)}, median {np.median(a):.0f} min) vs "
        f"{label_b} (n={len(b)}, median {np.median(b):.0f} min)")
    say(f"    U={u:,.0f}  p={p:.2e}  rank-biserial r={r:+.2f}  "
        f"median gap={np.median(a) - np.median(b):+.0f} min")


def ols(y, X, names):
    """Plain OLS with standard errors (numpy only)."""
    X1 = np.column_stack([np.ones(len(X)), X])
    beta, *_ = np.linalg.lstsq(X1, y, rcond=None)
    resid = y - X1 @ beta
    dof = len(y) - X1.shape[1]
    sigma2 = resid @ resid / dof
    se = np.sqrt(np.diag(sigma2 * np.linalg.inv(X1.T @ X1)))
    r2 = 1 - resid @ resid / ((y - y.mean()) @ (y - y.mean()))
    out = pd.DataFrame({"coef": beta, "std_err": se, "t": beta / se}, index=["intercept"] + names).round(3)
    return out, r2


df = pd.read_csv(PATH)
df["late_flag"] = df["late_flag"].astype(bool)
df["order_date"] = pd.to_datetime(df["order_date"])
df["date_parity"] = np.where(df["order_date"].dt.day % 2 == 0, "even date", "odd date")

# ---------------------------------------------------------------------
section("1. OVERVIEW")
say(f"Deliveries: {len(df):,}   Days: {df.order_date.nunique()}   "
    f"Range: {df.order_date.min().date()} to {df.order_date.max().date()}")
say(f"Average delivery time: {df.delivery_time.mean():.1f} min   Median: {df.delivery_time.median():.0f} min")
say(f"Late (> {LATE_MIN} min): {df.late_flag.sum():,}  ({df.late_flag.mean():.1%})   "
    f"On-time: {1 - df.late_flag.mean():.2%}")
say(f"Valid coordinates: {df.coords_valid.sum():,} ({df.coords_valid.mean():.1%})")

# ---------------------------------------------------------------------
section("2. LATE RATE AND AVERAGE MINUTES BY CONDITION")
tables = [("traffic", ["Low", "Medium", "High", "Jam"]),
          ("time_of_day", ["Morning", "Afternoon", "Evening", "Late night"]),
          ("distance_band", ["0-3 km", "3-6 km", "6-10 km", "10-15 km", "15+ km"]),
          ("agent_rating_band", ["Below 4.5", "4.5-4.8", "4.8-5.0"]),
          ("agent_age_band", ["18-25", "26-30", "31-35", "36+"]),
          ("weather", None), ("vehicle", None), ("area", None),
          ("is_weekend", None), ("date_parity", None)]
for col, order in tables:
    say(f"\n-- by {col}")
    say(group_table(df, col, order).to_string())

say("\n-- by city (cities with at least 100 deliveries, Unknown excluded)")
city = group_table(df[df.city_est.notna()], "city_est").sort_values("late_rate", ascending=False)
say(city.to_string())

# ---------------------------------------------------------------------
section("3. MANN-WHITNEY TESTS (delivery time in minutes)")
say("Rank-biserial r is the effect size: about 0.1 small, 0.3 medium, 0.5 large.\n")
t = df.dropna(subset=["traffic"])
mann_whitney(t.loc[t.traffic == "Jam", "delivery_time"], t.loc[t.traffic == "Low", "delivery_time"], "Jam traffic", "Low traffic")
mann_whitney(t.loc[t.traffic == "High", "delivery_time"], t.loc[t.traffic == "Medium", "delivery_time"], "High traffic", "Medium traffic")
mann_whitney(df.loc[df.time_of_day == "Evening", "delivery_time"], df.loc[df.time_of_day == "Morning", "delivery_time"], "Evening", "Morning")
r = df.dropna(subset=["agent_rating"])
mann_whitney(r.loc[r.agent_rating < 4.5, "delivery_time"], r.loc[r.agent_rating >= 4.5, "delivery_time"], "Agents rated < 4.5", "Agents rated >= 4.5")
d = df.dropna(subset=["distance_km"])
mann_whitney(d.loc[d.distance_km >= 10, "delivery_time"], d.loc[d.distance_km < 6, "delivery_time"], "Trips >= 10 km", "Trips < 6 km")
a = df.dropna(subset=["agent_age"])
mann_whitney(a.loc[a.agent_age >= 31, "delivery_time"], a.loc[a.agent_age <= 30, "delivery_time"], "Agents aged 31+", "Agents aged <= 30")
say("\nChecks that should show NO meaningful effect:")
mann_whitney(df.loc[df.is_weekend, "delivery_time"], df.loc[~df.is_weekend, "delivery_time"], "Weekend", "Weekday")
cg = [g.delivery_time.values for _, g in df[df.city_est.notna()].groupby("city_est") if len(g) >= 100]
h, p = stats.kruskal(*cg)
eta = (h - len(cg) + 1) / (sum(len(x) for x in cg) - len(cg))
say(f"  Kruskal-Wallis across {len(cg)} cities: H={h:.1f}  p={p:.3g}  epsilon-squared={eta:.4f} (near 0 = negligible)")

# ---------------------------------------------------------------------
section("4. DO THE MAIN EFFECTS SURVIVE THE ODD/EVEN DATE PATTERN?")
say("Average delivery minutes within each date group:\n")
for col, order in [("traffic", ["Low", "Medium", "High", "Jam"]), ("time_of_day", ["Morning", "Afternoon", "Evening", "Late night"]),
                   ("distance_band", ["0-3 km", "3-6 km", "6-10 km", "10-15 km", "15+ km"])]:
    pv = df.pivot_table(index=col, columns="date_parity", values="delivery_time", aggfunc="mean", observed=True).round(0)
    say(pv.reindex([o for o in order if o in pv.index]).to_string() + "\n")
lr = df.pivot_table(index="date_parity", values="late_flag", aggfunc="mean").round(3)
say("Late rate by date group:\n" + lr.to_string())

# ---------------------------------------------------------------------
section("5. REGRESSION: delivery minutes ~ conditions (rows with valid distance and rating)")
m = df.dropna(subset=["traffic", "distance_km", "agent_rating", "agent_age", "order_hour"]).copy()
m = m[m.coords_valid]
X = pd.DataFrame({
    "traffic_Medium": (m.traffic == "Medium").astype(float),
    "traffic_High": (m.traffic == "High").astype(float),
    "traffic_Jam": (m.traffic == "Jam").astype(float),
    "distance_km": m.distance_km,
    "evening_order": (m.time_of_day == "Evening").astype(float),
    "agent_rating": m.agent_rating,
    "agent_age": m.agent_age,
    "even_date": (m.date_parity == "even date").astype(float),
})
res, r2 = ols(m.delivery_time.values.astype(float), X.values, list(X.columns))
say(f"n = {len(m):,}   R-squared = {r2:.3f}\n")
say(res.to_string())
say("\nReading it: each coefficient is the change in delivery minutes holding the other variables fixed.")
say("traffic_* are compared with Low traffic; evening_order is compared with all other times of day.")

# ---------------------------------------------------------------------
section("6. WHERE THE LATE ORDERS COME FROM")
late = df[df.late_flag]
say("Share of late orders by traffic vs share of all orders:\n")
share = pd.DataFrame({"share_of_late": late.traffic.value_counts(normalize=True),
                      "share_of_all": df.traffic.value_counts(normalize=True)}).round(3)
say(share.reindex(["Low", "Medium", "High", "Jam"]).to_string())
combo = df[(df.traffic == "Jam") & (df.time_of_day == "Evening")]
say(f"\nJam traffic in the evening: {len(combo):,} deliveries ({len(combo) / len(df):.1%} of all), "
    f"late rate {combo.late_flag.mean():.1%}, share of all late orders {combo.late_flag.sum() / df.late_flag.sum():.1%}")

# ---------------------------------------------------------------------
section("7. ILLUSTRATIVE COST OF LATE DELIVERIES (assumed rates, not measured)")
tot = df.asm_total_cost_inr.sum()
lc = df.asm_cost_of_late_minutes_inr.sum()
jam = df.loc[df.traffic == "Jam", "asm_cost_of_late_minutes_inr"].sum()
say(f"Total illustrative cost: {tot:,.0f} INR   Cost of late minutes: {lc:,.0f} INR ({lc / tot:.1%} of total)")
say(f"Jam traffic late cost: {jam:,.0f} INR ({jam / lc:.1%} of late cost)")
say(f"A 20% cut in jam late cost would save about {0.2 * jam:,.0f} INR over {df.order_date.nunique()} days "
    f"(about {0.2 * jam / df.order_date.nunique():,.0f} INR per day of data).")

with open("eda_results.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(OUT))
print("\nSaved to eda_results.txt")
