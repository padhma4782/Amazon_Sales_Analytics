import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from utils.db_connection import get_connection


@st.cache_data(show_spinner=True, ttl=1800)
def load_ops_data():
    conn = get_connection()

    query = """
        SELECT 
            t.transaction_id,
            t.customer_id,
            t.product_id,
            t.corrected_price,
            t.delivery_days,
            t.payment_method,
            t.return_status,
            t.customer_rating,
            td.date_key,
            td.month,
            td.year,
            c.state
        FROM transactions t
        LEFT JOIN time_dimension td ON t.date_key = td.date_key
        LEFT JOIN customers c ON t.customer_id = c.customer_id;
    """

    df = pd.read_sql(query, conn)
    conn.close()
    return df


def app():
    st.title("Operations & Logistics Analytics Dashboard")

    df = load_ops_data()

    st.sidebar.header("Filters")
    year_filter = st.sidebar.selectbox(
        "Select Year", ["All"] + sorted(df["year"].dropna().unique().tolist())
    )
    state_filter = st.sidebar.selectbox(
        "Select State", ["All"] + sorted(df["state"].dropna().unique().tolist())
    )

    # Apply Filters
    if year_filter != "All":
        df = df[df["year"] == year_filter]

    if state_filter != "All":
        df = df[df["state"] == state_filter]

    st.sidebar.write(f"Total Records: **{len(df)}**")

   
    #  1 -Delivery Performance Analysis
    
    st.subheader("Delivery Performance")

    col1, = st.columns(1)

    with col1:
        avg_days = df["delivery_days"].mean()
        st.metric("Avg Delivery Days", round(avg_days, 2))

    # Delivery Bar Chart
    del_count = df["return_status"].value_counts()

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar(del_count.index, del_count.values)
    ax.set_title("Delivery Status Distribution")
    st.pyplot(fig)
    

    st.subheader("Return Rate Analysis")

    total_orders = len(df)
    returned_orders = df[df["return_status"] == "Returned"].shape[0]
    return_rate = (returned_orders / total_orders) * 100 if total_orders > 0 else 0

    st.metric("Return Rate (%)", f"{return_rate:.2f}%")
    st.markdown("---")

 
    #  2 — Payment Method Preferences

    st.subheader("Payment Method Preferences")

    pay_df = df["payment_method"].value_counts().reset_index()
    pay_df.columns = ["payment_method", "count"]

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.pie(pay_df["count"], labels=pay_df["payment_method"], autopct="%1.1f%%")
    ax.set_title("Payment Method Share")
    st.pyplot(fig)

    st.markdown("---")

    

 
    # 3 — Customer Satisfaction Score

    st.subheader("Customer Satisfaction Score")

    avg_rating = df["customer_rating"].mean()
    st.metric("Average Rating", round(avg_rating, 2))

    # Rating Distribution
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.hist(df["customer_rating"].dropna(), bins=5)
    ax.set_title("Rating Distribution")
    ax.set_xlabel("Rating")
    ax.set_ylabel("Count")
    st.pyplot(fig)

    st.markdown("---")

