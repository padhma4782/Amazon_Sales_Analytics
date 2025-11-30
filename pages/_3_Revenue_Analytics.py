import streamlit as st
import pandas as pd
import mysql.connector
import plotly.express as px
from utils.db_connection import get_connection

# ---------------------------
# Query Functions
# ---------------------------
@st.cache_data
def load_geographic_revenue():
    conn = get_connection()
    query = """
        SELECT 
            c.state,
            c.customer_segment AS segment,
            SUM(t.corrected_price) AS revenue,
            COUNT(t.transaction_id) AS total_transactions,
            COUNT(DISTINCT t.customer_id) AS unique_customers
        FROM transactions t
        JOIN customers c ON t.customer_id = c.customer_id
        GROUP BY c.state, c.customer_segment
        ORDER BY revenue DESC;
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def app():
    # ---------------------------
    # Dashboard
    # ---------------------------
    st.title("📊 Geographic Revenue Analysis (State + Segment)")

    df = load_geographic_revenue()

    st.subheader("Raw Data")
    st.dataframe(df)

    # ---------------------------
    # KPI Summary (Total Revenue, Total Customers, Total Transactions)
    # ---------------------------
    total_rev = df["revenue"].sum()
    total_customers = df["unique_customers"].sum()
    total_txn = df["total_transactions"].sum()

    col1, col2, col3 = st.columns(3)

    col1.metric("Total Revenue", f"₹{total_rev:,.0f}")
    col2.metric("Total Customers", f"{total_customers:,}")
    col3.metric("Total Transactions", f"{total_txn:,}")

    # ---------------------------
    # FILTERS
    # ---------------------------
    st.subheader("Filters")
    states = st.multiselect("Filter by State", df["state"].unique())
    segments = st.multiselect("Filter by Customer Segment", df["segment"].unique())

    filtered = df.copy()
    if states:
        filtered = filtered[filtered["state"].isin(states)]
    if segments:
        filtered = filtered[filtered["segment"].isin(segments)]

    # ---------------------------
    # BAR CHART — Revenue by State
    # ---------------------------
    st.subheader("Revenue by State")
    fig1 = px.bar(
        filtered.groupby("state")["revenue"].sum().reset_index(),
        x="state",
        y="revenue",
        text_auto=".2s",
        labels={"revenue": "Revenue"},
    )
    st.plotly_chart(fig1, use_container_width=True)

    # ---------------------------
    # PIE CHART — Segment Contribution
    # ---------------------------
    st.subheader("Segment Contribution")
    fig2 = px.pie(
        filtered.groupby("segment")["revenue"].sum().reset_index(),
        names="segment",
        values="revenue",
        title="Revenue Share by Customer Segment"
    )
    st.plotly_chart(fig2, use_container_width=True)

    # ---------------------------
    # TABLE — Detailed Drilldown
    # ---------------------------
    st.subheader("State + Segment Drilldown")
    st.dataframe(filtered.sort_values("revenue", ascending=False))
