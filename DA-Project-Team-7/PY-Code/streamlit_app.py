# ============================================================
# Retail Capstone — Streamlit in Snowflake Dashboard (Clean Edition)
# Exactly the 5 required charts, presented with premium visual polish.
# Paste this entire file into your Streamlit app's editor in Snowsight.
# ============================================================

import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
from snowflake.snowpark.context import get_active_session

# ------------------------------------------------------------
# 1. PAGE SETUP + GLOBAL STYLE
# ------------------------------------------------------------
st.set_page_config(page_title="Retail Analytics Dashboard", page_icon="🛒", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.block-container { padding-top: 1.5rem; padding-bottom: 2rem; }

.hero {
    background: linear-gradient(120deg, #0f172a 0%, #1e293b 55%, #0ea5e9 180%);
    border-radius: 18px; padding: 34px 40px; margin-bottom: 26px; border: 1px solid #1e293b;
}
.hero h1 { color: #f8fafc; font-size: 32px; font-weight: 800; margin: 0; }
.hero p  { color: #cbd5e1; font-size: 14px; margin-top: 8px; }

.kpi-card {
    background: linear-gradient(160deg, #1e293b 0%, #0f172a 100%);
    border-radius: 16px; padding: 22px 24px; border: 1px solid #273449;
    transition: border-color 0.2s ease;
}
.kpi-card:hover { border-color: #38bdf8; }
.kpi-icon { font-size: 20px; margin-bottom: 6px; }
.kpi-label { color: #94a3b8; font-size: 12px; text-transform: uppercase; letter-spacing: 0.08em; font-weight: 600; }
.kpi-value { color: #f8fafc; font-size: 26px; font-weight: 800; margin-top: 4px; }

.section-header { color: #f8fafc; font-size: 22px; font-weight: 700; margin: 30px 0 4px 0; }
.section-sub { color: #94a3b8; font-size: 13px; margin-bottom: 18px; }
</style>
""", unsafe_allow_html=True)


def format_inr(n: float) -> str:
    if n >= 1e7:
        return f"₹{n/1e7:,.1f} Cr"
    if n >= 1e5:
        return f"₹{n/1e5:,.1f} L"
    return f"₹{n:,.0f}"


# ------------------------------------------------------------
# 2. HERO HEADER
# ------------------------------------------------------------
st.markdown("""
<div class="hero">
    <h1>🛒 Global Retail E-Commerce — Analytics Dashboard</h1>
    <p>Built on the RETAIL_CAPSTONE Star Schema · Snowflake Data Warehouse</p>
</div>
""", unsafe_allow_html=True)

# ------------------------------------------------------------
# 3. CONNECT + LOAD DATA
# ------------------------------------------------------------
session = get_active_session()
session.sql("USE DATABASE RETAIL_CAPSTONE").collect()

@st.cache_data(ttl=600)
def load_data():
    fact_sales   = session.table("DW.FACT_SALES").to_pandas()
    dim_customer = session.table("DW.DIM_CUSTOMER").filter('"IS_CURRENT" = TRUE').to_pandas()
    dim_product  = session.table("DW.DIM_PRODUCT").to_pandas()
    dim_date     = session.table("DW.DIM_DATE").to_pandas()
    dim_location = session.table("DW.DIM_LOCATION").to_pandas()
    return fact_sales, dim_customer, dim_product, dim_date, dim_location

fact_sales, dim_customer, dim_product, dim_date, dim_location = load_data()

df = (fact_sales
      .merge(dim_date, on="DATE_SK", how="left")
      .merge(dim_product, on="PRODUCT_SK", how="left")
      .merge(dim_location, on="LOCATION_SK", how="left")
      .merge(dim_customer, on="CUSTOMER_SK", how="left", suffixes=("", "_CUST")))

# ------------------------------------------------------------
# 4. SIDEBAR FILTERS
# ------------------------------------------------------------
with st.sidebar:
    st.markdown("### 🔍 Filters")
    categories = ["All"] + sorted(df["CATEGORY"].dropna().unique().tolist())
    selected_category = st.selectbox("Category", categories)
    years = ["All"] + sorted(df["YEAR"].dropna().unique().astype(int).tolist())
    selected_year = st.selectbox("Year", years)

filtered = df.copy()
if selected_category != "All":
    filtered = filtered[filtered["CATEGORY"] == selected_category]
if selected_year != "All":
    filtered = filtered[filtered["YEAR"] == selected_year]

# ------------------------------------------------------------
# 5. KPI CARDS
# ------------------------------------------------------------
total_revenue    = filtered["LINE_AMOUNT"].sum()
total_orders     = filtered["ORDER_ID"].nunique()
avg_order_value  = total_revenue / total_orders if total_orders else 0
unique_customers = filtered["CUSTOMER_CODE"].nunique()

kpis = [
    ("💰", "Total Revenue", format_inr(total_revenue)),
    ("📦", "Total Orders", f"{total_orders:,}"),
    ("🧾", "Avg Order Value", format_inr(avg_order_value)),
    ("👥", "Unique Customers", f"{unique_customers:,}"),
]
cols = st.columns(4)
for col, (icon, label, value) in zip(cols, kpis):
    with col:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-icon">{icon}</div>
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
        </div>
        """, unsafe_allow_html=True)

# ------------------------------------------------------------
# 6. SHARED CHART THEME
# ------------------------------------------------------------
ACCENT = "#38bdf8"
PALETTE = ["#38bdf8", "#a78bfa", "#fb7185", "#34d399", "#fbbf24", "#f472b6", "#818cf8", "#2dd4bf"]

def style_chart(chart, title, subtitle=None):
    if subtitle:
        t = alt.TitleParams(text=title, subtitle=subtitle, color="#f8fafc", subtitleColor="#94a3b8",
                             fontSize=15, fontWeight="bold", anchor="start")
    else:
        t = alt.TitleParams(text=title, color="#f8fafc", fontSize=15, fontWeight="bold", anchor="start")
    return (
        chart.properties(title=t, height=320, background="#0f172a")
        .configure_view(strokeWidth=0)
        .configure_axis(labelColor="#cbd5e1", titleColor="#94a3b8", gridColor="#1e293b", domainColor="#334155")
        .configure_legend(labelColor="#cbd5e1", titleColor="#94a3b8")
    )

st.markdown('<div class="section-header">📊 Business Insights</div>', unsafe_allow_html=True)
st.markdown('<div class="section-sub">The 5 core analyses requested for this capstone</div>', unsafe_allow_html=True)

# ------------------------------------------------------------
# 7. THE 5 REQUIRED CHARTS — 2 rows x 3, with the 5th chart centered
# ------------------------------------------------------------
row1 = st.columns(2)
row2 = st.columns(2)

# --- Chart 1 (Line): Monthly Revenue Trend ---
monthly_rev = filtered.groupby(["YEAR", "MONTH"])["LINE_AMOUNT"].sum().reset_index()
monthly_rev["label"] = monthly_rev["YEAR"].astype(str) + "-" + monthly_rev["MONTH"].astype(str).str.zfill(2)
chart1 = alt.Chart(monthly_rev).mark_area(
    line={"color": ACCENT, "strokeWidth": 2.5},
    color=alt.Gradient(gradient="linear",
                        stops=[alt.GradientStop(color="#0f172a", offset=0), alt.GradientStop(color="#38bdf8", offset=1)],
                        x1=1, x2=1, y1=1, y2=0)
).encode(
    x=alt.X("label:N", title="Month", sort=None),
    y=alt.Y("LINE_AMOUNT:Q", title="Revenue"),
    tooltip=["label", alt.Tooltip("LINE_AMOUNT:Q", format=",.0f")]
)
with row1[0]:
    st.altair_chart(style_chart(chart1, "Monthly Revenue Trend"), use_container_width=True)

# --- Chart 2 (Bar): Category-wise Revenue ---
category_rev = filtered.groupby("CATEGORY", as_index=False)["LINE_AMOUNT"].sum().sort_values("LINE_AMOUNT", ascending=False)
chart2 = alt.Chart(category_rev).mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6).encode(
    x=alt.X("CATEGORY:N", title=None, sort="-y"),
    y=alt.Y("LINE_AMOUNT:Q", title="Revenue"),
    color=alt.Color("CATEGORY:N", scale=alt.Scale(range=PALETTE), legend=None),
    tooltip=["CATEGORY", alt.Tooltip("LINE_AMOUNT:Q", format=",.0f")]
)
with row1[1]:
    st.altair_chart(style_chart(chart2, "Revenue by Category"), use_container_width=True)

# --- Chart 3 (Histogram): Distribution of Line Amounts ---
counts, bin_edges = np.histogram(filtered["LINE_AMOUNT"].dropna(), bins=30)
hist_df = pd.DataFrame({"bin_start": bin_edges[:-1], "bin_end": bin_edges[1:], "count": counts})
hist_df["bin_label"] = hist_df["bin_start"].round(0).astype(int).astype(str) + "–" + hist_df["bin_end"].round(0).astype(int).astype(str)
chart3 = alt.Chart(hist_df).mark_bar(color=ACCENT, cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(
    x=alt.X("bin_label:N", title="Order Line Amount Range", sort=None, axis=alt.Axis(labelAngle=-45, labelFontSize=9)),
    y=alt.Y("count:Q", title="Count"),
    tooltip=["bin_label", "count"]
)
with row2[0]:
    st.altair_chart(style_chart(chart3, "Distribution of Order Line Amounts"), use_container_width=True)

# --- Chart 4 (Pie): Customer Segments by Spend ---
cust_spend = filtered.groupby("CUSTOMER_CODE")["LINE_AMOUNT"].sum()
segments = pd.qcut(cust_spend, q=3, labels=["Low", "Medium", "High"])
segment_counts = segments.value_counts().reset_index()
segment_counts.columns = ["Segment", "Count"]
chart4 = alt.Chart(segment_counts).mark_arc(innerRadius=70, outerRadius=115, cornerRadius=5, padAngle=0.02).encode(
    theta="Count:Q",
    color=alt.Color("Segment:N", scale=alt.Scale(domain=["Low", "Medium", "High"], range=[PALETTE[2], PALETTE[4], PALETTE[3]])),
    tooltip=["Segment", "Count"]
)
with row2[1]:
    st.altair_chart(style_chart(chart4, "Customer Segments by Spend"), use_container_width=True)

# --- Chart 5 (Horizontal Bar): Top 10 Cities by Revenue — full width, centerpiece ---
top_cities = filtered.groupby("CITY", as_index=False)["LINE_AMOUNT"].sum().sort_values("LINE_AMOUNT", ascending=False).head(10)
chart5 = alt.Chart(top_cities).mark_bar(color=ACCENT, cornerRadiusTopRight=6, cornerRadiusBottomRight=6).encode(
    y=alt.Y("CITY:N", title=None, sort="-x"),
    x=alt.X("LINE_AMOUNT:Q", title="Revenue"),
    tooltip=["CITY", alt.Tooltip("LINE_AMOUNT:Q", format=",.0f")]
)
st.altair_chart(style_chart(chart5, "Top 10 Cities by Revenue"), use_container_width=True)

st.markdown("---")
st.caption("Data pipeline: RAW → STAGING (cleaned) → DW (Star Schema with SCD2) — see accompanying SQL scripts for full ETL logic.")