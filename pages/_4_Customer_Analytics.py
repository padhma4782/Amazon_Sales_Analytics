import streamlit as st
import pandas as pd
from utils.db_connection import get_connection
import plotly.express as px


@st.cache_data
def load_data():
    conn = get_connection()

    customers = pd.read_sql("SELECT * FROM customers", conn)
    transactions = pd.read_sql("""
        SELECT t.*, c.state, c.customer_segment, c.is_prime_member
        FROM transactions t
        JOIN customers c ON t.customer_id = c.customer_id
    """, conn)

    conn.close()
    return customers, transactions



# Marketing Recommendation Logic

def generate_recommendation(row):
    if row["is_prime_member"] == 1:
        if row["avg_spend"] > 50000:
            return "Promote high-value Prime bundles, premium gadgets, loyalty upgrades."
        else:
            return "Push Prime-exclusive deals, cashback, and personalized coupons."
    else:
        if row["avg_spend"] > 30000:
            return "Suggest Prime membership with savings calculator & free delivery benefits."
        else:
            return "Offer low-cost trial Prime membership & budget product bundles."

def app():

    # Streamlit UI

    st.set_page_config(page_title="Customer Analytics Dashboard", layout="wide")
    st.title("🧑‍💼 Customer Analytics Dashboard")

    customers, transactions = load_data()

    # Sidebar Interactive Customer Profile
  
    st.sidebar.header("🔍 Search Customer")

    selected_customer = st.sidebar.selectbox(
        "Select Customer ID", 
        customers["customer_id"].unique()
    )

    cust_df = customers[customers["customer_id"] == selected_customer]
    cust_txn = transactions[transactions["customer_id"] == selected_customer]

    st.sidebar.subheader("Customer Profile Summary")
    st.sidebar.write(cust_df)

    # Personalized statistics
    if not cust_txn.empty:
        total_spend = cust_txn["corrected_price"].sum()
        avg_spend = cust_txn["corrected_price"].mean()
        orders = len(cust_txn)

        st.sidebar.metric("Total Spend", f"₹{total_spend:,.0f}")
        st.sidebar.metric("Avg Order Value", f"₹{avg_spend:,.0f}")
        st.sidebar.metric("Orders Count", orders)
    else:
        st.sidebar.warning("No transaction data found.")

   
    # Main Dashboard Layout
  
    tab1, tab2, tab3 = st.tabs(["Prime vs Non-Prime Behavior", 
                                "Membership Value Analysis", 
                                "Customer Marketing Recommendations"])

   
    # Tab 1 — PRIME VS NON-PRIME BEHAVIOR
  
    with tab1:
        st.header("👑 Prime vs Non-Prime Behavior Overview")

        prime_grp = transactions.groupby("is_prime_member").agg({
            "corrected_price": "mean",
            "transaction_id": "count"
        }).rename(columns={"transaction_id": "order_count"})

        prime_grp["type"] = prime_grp.index.map({1: "Prime Members", 0: "Non-Prime Members"})

        fig = px.bar(
            prime_grp, 
            x="type",
            y="corrected_price",
            color="type",
            title="Average Spend Comparison",
            labels={"corrected_price": "Avg Spend (₹)"}
        )
        st.plotly_chart(fig, use_container_width=True)

        fig2 = px.pie(
            prime_grp, 
            names="type",
            values="order_count",
            title="Order Share: Prime vs Non-Prime"
        )
        st.plotly_chart(fig2, use_container_width=True)



    # Tab 2 — MEMBERSHIP VALUE ANALYSIS

    with tab2:
        st.header("📊 Membership Value Analysis")

        # Avg spend by customer segment
        seg_data = transactions.groupby(["customer_segment", "is_prime_member"])["corrected_price"].mean().reset_index()

        seg_data["Member_Type"] = seg_data["is_prime_member"].map({1: "Prime", 0: "Non-Prime"})

        fig3 = px.bar(
            seg_data,
            x="customer_segment",
            y="corrected_price",
            color="Member_Type",
            barmode="group",
            title="Avg Spend by Segment (Prime vs Non-Prime)"
        )
        st.plotly_chart(fig3, use_container_width=True)

        # State-wise revenue
        state_rev = transactions.groupby("state")["corrected_price"].sum().reset_index()

        fig4 = px.choropleth(
            state_rev,
            locationmode="country names",
            locations="state",
            color="corrected_price",
            title="State-wise Revenue Contribution",
            labels={"corrected_price": "Revenue (₹)"}
        )
        st.plotly_chart(fig4, use_container_width=True)




    # Tab 3 — CUSTOMER TARGETED MARKETING RECOMMENDATIONS

    with tab3:
        st.header("🎯 Customer Targeted Marketing Recommendations")

        # Prepare profile table
        profile = transactions.groupby("customer_id").agg(
            total_spend=("corrected_price", "sum"),
            avg_spend=("corrected_price", "mean"),
            orders=("transaction_id", "count"),
            is_prime_member=("is_prime_member", "max")
        ).reset_index()

        profile["recommendation"] = profile.apply(generate_recommendation, axis=1)

        # Show for selected customer
        selected = profile[profile["customer_id"] == selected_customer]

        if not selected.empty:
            st.subheader("📌 Recommendation for Selected Customer")
            st.success(selected["recommendation"].values[0])

        # Full table
        st.subheader("📋 Full Customer Marketing Recommendation Table")
        st.dataframe(profile)



