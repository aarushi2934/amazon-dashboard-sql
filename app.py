"""
Amazon Growth Dashboard (Streamlit + SQLite)
Author: ChatGPT x Aarushi

What’s new vs. CSV version?
- Real **SQLite database** backend (`amazon.db`), not just CSV.
- One-click **seed** with sample SKU data.
- Toggle between **DB** and **CSV upload** via sidebar.

Recommended runtime (macOS-friendly):
- Python 3.11
- numpy==1.26.4, pandas==2.2.2, streamlit==1.38.0, plotly==5.24.0
"""
from __future__ import annotations
import io
import math
import sqlite3
from datetime import datetime
from typing import Optional

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

DB_PATH_DEFAULT = "amazon.db"

# ------------------------------
# Data generation (for seeding)
# ------------------------------
def gen_sample_data(days: int = 90, skus: int = 120, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    start = pd.Timestamp.today().normalize() - pd.Timedelta(days=days)
    dates = pd.date_range(start, periods=days, freq="D")

    categories = ["Sarees", "Kurti", "Jewellery", "Home", "Beauty"]
    brands = ["Myx", "Libas", "Qazmi", "UrbanNest", "Biba"]
    fulfill = ["FBA", "3P", "1P"]

    sku_ids = [f"SKU-{i:04d}" for i in range(skus)]
    sku_meta = pd.DataFrame({
        "sku_id": sku_ids,
        "title": [f"Product {i:04d}" for i in range(skus)],
        "brand": rng.choice(brands, size=skus),
        "category": rng.choice(categories, size=skus),
        "base_price": rng.normal(799, 250, size=skus).clip(149, 2999),
        "fulfillment": rng.choice(fulfill, size=skus),
    })

    rows = []
    for d in dates:
        dow = d.weekday()
        traffic_boost = 1.0 + (0.20 if dow in (5, 6) else 0.0)
        promo = 1.0 + (0.35 if (d.day in (1, 15)) else 0.0)

        for _, r in sku_meta.iterrows():
            price = float(np.round(r.base_price * rng.uniform(0.85, 1.15), 2))
            discount = float(max(0, 1 - price / max(r.base_price, 1)))
            sessions = int(rng.poisson(30 * traffic_boost * promo))
            ctr = rng.uniform(0.05, 0.16)
            clicks = int(np.round(sessions * ctr))
            atc_rate = rng.uniform(0.15, 0.45)
            add_to_cart = int(np.round(clicks * atc_rate))
            conv_rate = rng.uniform(0.18, 0.45)
            units = int(np.round(add_to_cart * conv_rate))
            returns = int(max(0, np.round(units * rng.uniform(0.03, 0.15))))
            gmv = float(np.round(price * units, 2))
            take_rate = float(np.round(rng.uniform(0.07, 0.15), 3))

            rows.append({
                "date": d.date(),
                "sku_id": r.sku_id,
                "title": r.title,
                "brand": r.brand,
                "category": r.category,
                "price": price,
                "discount": discount,
                "sessions": sessions,
                "clicks": clicks,
                "add_to_cart": add_to_cart,
                "units_ordered": units,
                "units_returned": returns,
                "gmv": gmv,
                "fulfillment": r.fulfillment,
                "region": "IN",
                "take_rate": take_rate,
            })

    df = pd.DataFrame(rows)
    return df


def seed_sqlite(db_path: str, df: Optional[pd.DataFrame] = None):
    """Create/overwrite a SQLite DB with a sku_metrics table and insert df or generated sample data."""
    if df is None:
        df = gen_sample_data()

    # Ensure proper dtypes
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"]).dt.date

    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS sku_metrics (
                date TEXT,
                sku_id TEXT,
                title TEXT,
                brand TEXT,
                category TEXT,
                price REAL,
                discount REAL,
                sessions INTEGER,
                clicks INTEGER,
                add_to_cart INTEGER,
                units_ordered INTEGER,
                units_returned INTEGER,
                gmv REAL,
                fulfillment TEXT,
                region TEXT,
                take_rate REAL
            );
        """)
        conn.commit()
        # Clear previous data to make seeding idempotent
        cur.execute("DELETE FROM sku_metrics;")
        conn.commit()

        df.to_sql("sku_metrics", conn, if_exists="append", index=False)


# ------------------------------
# Streamlit App
# ------------------------------
st.set_page_config(page_title="Amazon Growth Dashboard — SQL", layout="wide")
st.title("📈 Amazon Growth Dashboard")

st.sidebar.header("⚙️ Data Source")
source_mode = st.sidebar.radio("Choose source", ["SQLite DB", "CSV upload"], index=0)

db_path = st.sidebar.text_input("SQLite DB path", DB_PATH_DEFAULT)
if source_mode == "SQLite DB":
    col_seed = st.sidebar.container()
    if col_seed.button("🔄 Seed / Reseed DB with sample data"):
        try:
            seed_sqlite(db_path)
            st.sidebar.success(f"Database seeded at: {db_path}")
        except Exception as e:
            st.sidebar.error(f"Seeding failed: {e}")

uploaded = None
if source_mode == "CSV upload":
    uploaded = st.sidebar.file_uploader("Upload CSV", type=["csv"])

# Load data
if source_mode == "SQLite DB":
    try:
        with sqlite3.connect(db_path) as conn:
            df = pd.read_sql("SELECT * FROM sku_metrics", conn, parse_dates=["date"])
            df["date"] = df["date"].dt.date
    except Exception as e:
        st.error(f"Could not read DB: {e}")
        st.stop()
else:
    if uploaded is not None:
        df = pd.read_csv(uploaded)
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"]).dt.date
    else:
        st.info("Upload a CSV from the sidebar to proceed.")
        st.stop()

# Derivations
if "gmv" not in df.columns and {"price", "units_ordered"}.issubset(df.columns):
    df["gmv"] = df["price"] * df["units_ordered"]

df["net_units"] = df.get("units_ordered", 0) - df.get("units_returned", 0)
df["net_gmv"] = np.where("gmv" in df.columns,
                         df["gmv"] - df["price"].fillna(0) * df.get("units_returned", 0).fillna(0),
                         df.get("price", 0) * df["net_units"])

if "take_rate" not in df.columns:
    df["take_rate"] = 0.10
df["platform_rev"] = df["net_gmv"] * df["take_rate"].fillna(0)

df["ctr"] = np.where(df.get("sessions", 0) > 0, df.get("clicks", 0) / df.get("sessions", 1), np.nan)
df["conv_rate"] = np.where(df.get("add_to_cart", 0) > 0, df.get("units_ordered", 0) / df.get("add_to_cart", 1), np.nan)

# Sidebar filters
st.sidebar.header("🔍 Filters")
min_date, max_date = df["date"].min(), df["date"].max()
sel_date = st.sidebar.date_input("Date range", value=(min_date, max_date), min_value=min_date, max_value=max_date)
if not isinstance(sel_date, (list, tuple)):
    sel_date = (min_date, max_date)

cats = sorted(df.get("category", pd.Series(dtype=str)).dropna().unique().tolist())
brands = sorted(df.get("brand", pd.Series(dtype=str)).dropna().unique().tolist())
fulfills = sorted(df.get("fulfillment", pd.Series(dtype=str)).dropna().unique().tolist())

sel_cat = st.sidebar.multiselect("Category", cats, default=cats[:2] if cats else [])
sel_brand = st.sidebar.multiselect("Brand", brands)
sel_fulfill = st.sidebar.multiselect("Fulfillment", fulfills)

min_price = float(df.get("price", pd.Series([0])).min())
max_price = float(df.get("price", pd.Series([0])).max())
price_band = st.sidebar.slider("Price band", min_value=float(int(min_price)), max_value=float(math.ceil(max_price)), value=(float(int(min_price)), float(math.ceil(max_price))))

mask = (
    (df["date"] >= sel_date[0]) & (df["date"] <= sel_date[1])
)
if sel_cat:
    mask &= df["category"].isin(sel_cat)
if sel_brand:
    mask &= df["brand"].isin(sel_brand)
if sel_fulfill:
    mask &= df["fulfillment"].isin(sel_fulfill)
mask &= df.get("price", 0).between(price_band[0], price_band[1])

fdf = df.loc[mask].copy()

# KPI header
def kpi(val, label, helptext=None, fmt="{:,.0f}"):
    st.metric(label=label, value=(fmt.format(val) if val is not None and not np.isnan(val) else "–"), help=helptext)

left, mid1, mid2, right1, right2 = st.columns(5)
sessions = float(fdf.get("sessions", pd.Series([0])).sum())
clicks = float(fdf.get("clicks", pd.Series([0])).sum())
ctr = clicks / sessions if sessions > 0 else np.nan
atc = float(fdf.get("add_to_cart", pd.Series([0])).sum())
units = float(fdf.get("units_ordered", pd.Series([0])).sum())
conv = units / atc if atc > 0 else np.nan
net_gmv = float(fdf.get("net_gmv", pd.Series([0.0])).sum())
platform_rev = float(fdf.get("platform_rev", pd.Series([0.0])).sum())
asp = (fdf.get("price", pd.Series([np.nan])).mean())

with left:
    kpi(sessions, "Sessions", "Total sessions")
with mid1:
    kpi(ctr*100 if not np.isnan(ctr) else np.nan, "CTR %", fmt="{:.2f}%")
with mid2:
    kpi(conv*100 if not np.isnan(conv) else np.nan, "Conv % (ATC→Order)", fmt="{:.2f}%")
with right1:
    kpi(net_gmv, "Net GMV", fmt="₹{:,.0f}")
with right2:
    kpi(asp, "Avg Selling Price", fmt="₹{:,.0f}")

# Trends
st.subheader("Trends")
if not fdf.empty:
    by_day = fdf.groupby("date").agg({
        "sessions": "sum",
        "clicks": "sum",
        "add_to_cart": "sum",
        "units_ordered": "sum",
        "net_gmv": "sum",
        "platform_rev": "sum",
        "price": "mean"
    }).reset_index()
    by_day["ctr"] = by_day["clicks"] / by_day["sessions"]
    by_day["conv"] = by_day["units_ordered"] / by_day["add_to_cart"].replace(0, np.nan)

    t1, t2 = st.columns(2)
    with t1:
        fig = px.line(by_day, x="date", y=["sessions", "clicks", "add_to_cart", "units_ordered"], title="Funnel Counts Over Time")
        st.plotly_chart(fig, use_container_width=True)
    with t2:
        fig2 = px.line(by_day, x="date", y=["net_gmv", "platform_rev"], title="Net GMV & Platform Revenue Over Time")
        st.plotly_chart(fig2, use_container_width=True)

    # Elasticity proxy
    st.subheader("Price vs Units (Elasticity Proxy)")
    price_units = fdf.groupby(["sku_id", "title"], as_index=False).agg({
        "price": "mean",
        "units_ordered": "sum",
        "sessions": "sum",
        "brand": "first",
        "category": "first"
    })

    fig3 = px.scatter(
        price_units,
        x="price",
        y="units_ordered",
        size="sessions",
        hover_data=["sku_id", "title", "brand", "category"]
    )
    st.plotly_chart(fig3, use_container_width=True)

    # Movers
    st.subheader("Top Movers — Units & GMV")
    movers = fdf.groupby(["sku_id", "title"]).agg({
        "units_ordered": "sum",
        "net_gmv": "sum",
        "sessions": "sum",
        "clicks": "sum"
    }).reset_index().sort_values("units_ordered", ascending=False).head(20)
    st.dataframe(movers, use_container_width=True)
else:
    st.info("No data after filters.")

# Anomalies
st.subheader("Anomalies — Daily Net GMV")
if not fdf.empty:
    series = fdf.groupby("date")["net_gmv"].sum().reset_index()
    mu, sd = series["net_gmv"].mean(), series["net_gmv"].std(ddof=0)
    series["z"] = (series["net_gmv"] - mu) / (sd if sd > 0 else 1)
    series["anomaly"] = series["z"].abs() >= 2.0
    fig4 = px.bar(series, x="date", y="net_gmv", color="anomaly", title="Days with ±2σ anomalies highlighted")
    st.plotly_chart(fig4, use_container_width=True)
    if series["anomaly"].any():
        st.warning(f"{int(series['anomaly'].sum())} anomaly day(s) in range.")

# Breakdowns
st.subheader("Breakdowns")
colA, colB = st.columns(2)
if not fdf.empty:
    by_cat = fdf.groupby("category").agg({
        "sessions": "sum", "clicks": "sum", "add_to_cart": "sum",
        "units_ordered": "sum", "net_gmv": "sum"
    }).reset_index()
    by_cat["CTR %"] = (by_cat["clicks"] / by_cat["sessions"].replace(0, np.nan)) * 100
    by_cat["Conv %"] = (by_cat["units_ordered"] / by_cat["add_to_cart"].replace(0, np.nan)) * 100
    with colA:
        st.markdown("**By Category**")
        st.dataframe(by_cat.sort_values("net_gmv", ascending=False), use_container_width=True)

    by_brand = fdf.groupby("brand").agg({
        "sessions": "sum", "clicks": "sum", "add_to_cart": "sum",
        "units_ordered": "sum", "net_gmv": "sum"
    }).reset_index()
    by_brand["CTR %"] = (by_brand["clicks"] / by_brand["sessions"].replace(0, np.nan)) * 100
    by_brand["Conv %"] = (by_brand["units_ordered"] / by_brand["add_to_cart"].replace(0, np.nan)) * 100
    with colB:
        st.markdown("**By Brand**")
        st.dataframe(by_brand.sort_values("net_gmv", ascending=False), use_container_width=True)

# Export
st.subheader("Export")
if not fdf.empty:
    snapshot = {
        "sessions": float(sessions),
        "ctr_pct": float(ctr*100) if not np.isnan(ctr) else None,
        "conv_pct": float(conv*100) if not np.isnan(conv) else None,
        "net_gmv": float(net_gmv),
        "asp": float(asp) if not math.isnan(asp) else None,
        "platform_rev": float(platform_rev),
        "date_start": str(sel_date[0]),
        "date_end": str(sel_date[1]),
        "filters": {
            "category": sel_cat,
            "brand": sel_brand,
            "fulfillment": sel_fulfill,
            "price_band": price_band,
        },
    }
    buf = io.StringIO()
    pd.DataFrame([snapshot]).to_csv(buf, index=False)
    st.download_button("⬇️ Download KPI snapshot (CSV)", data=buf.getvalue(),
                       file_name="kpi_snapshot.csv", mime="text/csv")
