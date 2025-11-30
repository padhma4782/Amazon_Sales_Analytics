import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from utils.db_connection import get_connection


@st.cache_data
def load_data():
    conn = get_connection()

    query = """
        SELECT 
            t.transaction_id,
            t.customer_id,
            t.product_id,
            t.corrected_price,
            t.customer_rating,
            td.date_key,
            td.month,
            td.year,
            p.product_name,
            p.category,
            p.subcategory,
            p.brand,
            p.product_rating
        FROM transactions t
        JOIN time_dimension td ON t.date_key = td.date_key
        JOIN products p ON t.product_id = p.product_id
    """

    df = pd.read_sql(query, conn)
    conn.close()
    return df


def app():
    st.set_page_config(page_title="Product Performance Dashboard",
                       layout="wide")

    st.title("📊 Product Performance Dashboard")

    df = load_data()

    # Sidebar Filters
    category = st.sidebar.selectbox("Filter by Category:", 
                                    ["All"] + sorted(df["category"].dropna().unique().tolist()))

    if category != "All":
        df = df[df["category"] == category]

    st.sidebar.write(f"**Total Records: {len(df)}**")

  
    # PRODUCT RANKING BY REVENUE
    
    st.subheader("🏆 Top Products by Revenue")

    revenue_df = (
        df.groupby(["product_id", "product_name"])
        ["corrected_price"]
        .sum()
        .sort_values(ascending=False)
        .reset_index()
    )

    st.dataframe(revenue_df.head(10))

    # Plot Top 10 Revenue Products
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.bar(revenue_df.head(10)["product_name"], revenue_df.head(10)["corrected_price"])
    ax.set_title("Top 10 Revenue Products")
    plt.xticks(rotation=45, ha="right")
    st.pyplot(fig)

   
    # 2️ CATEGORY-WISE ANALYSIS
 
    st.subheader("📂 Category-wise Revenue Analysis")

    cat_df = df.groupby("subcategory")["corrected_price"].sum().reset_index()

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(cat_df["subcategory"], cat_df["corrected_price"])
    ax.set_title("Revenue by Category")
    plt.xticks(rotation=45)
    st.pyplot(fig)

  
    #  PRODUCT DEMAND PATTERNS (Sales Count)
   
    st.subheader("📈 Product Demand Patterns")

    demand_df = (
        df.groupby(["product_id", "product_name"])
        ["transaction_id"]
        .count()
        .sort_values(ascending=False)
        .reset_index()
        .rename(columns={"transaction_id": "sales_count"})
    )

    st.dataframe(demand_df.head(10))

    
    #  SEASONAL TRENDS (Monthly & Quarterly)
    
    st.subheader(" Seasonal Trends (Monthly Sales)")

    seasonal_df = (
        df.groupby(["year", "month"])
        ["corrected_price"]
        .sum()
        .reset_index()
    )

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(seasonal_df["month"], seasonal_df["corrected_price"])
    ax.set_title("Monthly Revenue Trend")
    ax.set_xlabel("Month")
    ax.set_ylabel("Revenue")
    st.pyplot(fig)

    
    # INVENTORY TURNOVER (Proxy: Sales Count / Product)
   
    st.subheader("🔄 Inventory Turnover (Sales Frequency)")

    inv_df = demand_df.copy()
    inv_df["turnover_score"] = inv_df["sales_count"] / inv_df["sales_count"].max()

    st.dataframe(inv_df[["product_name", "turnover_score"]].head(10))

    
    # DEMAND FORECASTING (Simple Moving Average)
   
    st.subheader("📉 Demand Forecasting (3-Month Moving Average)")

    forecast_df = seasonal_df.copy()
    forecast_df["forecast"] = forecast_df["corrected_price"].rolling(window=3).mean()

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(forecast_df["corrected_price"], label="Actual")
    ax.plot(forecast_df["forecast"], label="Forecast (3-month MA)")
    ax.legend()
    st.pyplot(fig)

    
    # 7 PRODUCT RATING CORRELATION WITH SALES
    
    st.subheader("⭐ Product Rating vs Sales Correlation")

    rating_df = df.groupby(["product_id", "product_name"]).agg(
        avg_rating=("customer_rating", "mean"),
        total_sales=("transaction_id", "count")
    ).reset_index()

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.scatter(rating_df["avg_rating"], rating_df["total_sales"])
    ax.set_xlabel("Average Rating")
    ax.set_ylabel("Sales Count")
    ax.set_title("Rating vs Sales")
    st.pyplot(fig)

    # correlation value
    corr = rating_df["avg_rating"].corr(rating_df["total_sales"])
    st.info(f"📌 Correlation between rating and sales: **{round(corr, 3)}**")

