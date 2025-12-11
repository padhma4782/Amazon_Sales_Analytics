import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from utils.db_connection import get_connection
from millify import millify

st.set_page_config(page_title="Advanced Analytics", layout="wide")


@st.cache_data
def load_data():
    conn = get_connection()

    query = """
        SELECT
            t.transaction_id,
            t.corrected_price,
            t.customer_rating,
            t.payment_method,
            t.delivery_days,
            t.return_status,
            td.date_key,
            td.year,
            td.month,
            td.quarter,
            td.day_of_week,
            c.is_prime_member,
            p.category,
            p.product_name
        FROM transactions t
        JOIN time_dimension td ON t.date_key = td.date_key
        JOIN customers c ON t.customer_id = c.customer_id
        JOIN products p ON t.product_id = p.product_id;
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df


def app():

    st.title("Advanced Analytics Dashboard")

    df = load_data()

    # 1 Key Sales Metrics

    st.header("Key Sales Metrics")
    total_revenue = df['corrected_price'].sum()
    readable_rev = millify(total_revenue, precision=2)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Revenue", f"₹{readable_rev}")
    col2.metric("Avg Delivery Days", round(df["delivery_days"].mean(), 2))
    col3.metric("Return Rate (%)", round((df["return_status"] == "Returned").mean() * 100, 2))
    col4.metric("Avg Customer Rating", round(df["customer_rating"].mean(), 2))


    seasonal = df.groupby(["year", "month"])["corrected_price"].sum().reset_index()
    seasonal["period"] = seasonal["year"].astype(str) + "-" + seasonal["month"].astype(str)

   
    # 3 Delivery Performance Analysis
  
    st.subheader("Delivery Performance Analysis")

    col1, col2 = st.columns(2)

    with col1:
        st.write("### Delivery Time Distribution")
        fig, ax = plt.subplots(figsize=(5, 4))
        ax.hist(df["delivery_days"].dropna())
        st.pyplot(fig)

    with col2:
        st.write("### Delivery Issues (Returns)")
        issue_df = df["return_status"].value_counts()
        st.bar_chart(issue_df)

   
    #  PAYMENT METHOD PERFORMANCE
    
    st.subheader("Payment Method Preferences")

    pay_df = df["payment_method"].value_counts()
    st.bar_chart(pay_df)


    # Customer Satisfaction & Recommendation Effectiveness
    
    st.subheader("Customer Satisfaction & Recommendation Effectiveness")

    rating_rev = df.groupby("customer_rating")["corrected_price"].mean()

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(rating_rev.index, rating_rev.values)
    ax.set_title("Rating vs Avg Spending")
    st.pyplot(fig)

 
    # Automated Alerts

    st.subheader("Automated Alerts")

    alerts = []

    if df["delivery_days"].mean() > 7:
        alerts.append("⚠ Average delivery time has increased above 7 days.")

    if (df["return_status"] == "Returned").mean() > 0.10:
        alerts.append("⚠ Return rate is above 10%.")

    if df["customer_rating"].mean() < 3.5:
        alerts.append("⚠ Drop in customer satisfaction score.")

    if len(alerts) == 0:
        st.success(" No alerts! Performance looks healthy.")
    else:
        for a in alerts:
            st.error(a)

    # Strategic Recommendations

    st.subheader("Strategic Recommendations")

    st.write("""
    - Increase warehouse capacity in high-delay regions  
    - Add faster delivery options for premium customers  
    - Promote high-rated products in marketing campaigns  
    - Monitor high-return categories for quality issues  
    - Use seasonal forecasting to plan inventory ahead  
    """)


# Run in Streamlit
if __name__ == "__main__":
    app()
