import streamlit as st
import pandas as pd
from datetime import date
from millify import millify # You need to run: pip install millify
# Import the connection function from the main file.
# This assumes 'streamlit_app' is the main file defining get_db_connection.
from utils.db_connection import get_connection 

st.set_page_config(layout="wide")

def fetch_data(conn, query, params=None):
    """Helper function to fetch data from MySQL and return a DataFrame."""
    try:
        # Uses pandas to execute the SQL query and fetch results directly
        return pd.read_sql(query, conn, params=params)
    except Exception as e:
        st.error(f"Error executing query: {e}")
        return pd.DataFrame()

def get_executive_summary(conn):
    """
    Fetches core KPIs (Revenue, Customers, AOV) and YoY growth data by querying 
    the dimension and fact tables.
    """
    # Define the current year and previous year for comparison
    current_year = date.today().year
    previous_year = current_year - 1
    
    # 1. Query to get Revenue, Customer Count, Orders, and AOV for current and previous year
    summary_query = f"""
    SELECT
        t.year,
        SUM(txn.corrected_price) AS TotalRevenue,
        COUNT(DISTINCT txn.customer_id) AS ActiveCustomers,
        COUNT(DISTINCT txn.transaction_id) AS TotalOrders,
        SUM(txn.corrected_price) / COUNT(DISTINCT txn.transaction_id) AS AOV
    FROM transactions txn
    JOIN time_dimension t ON txn.date_key = t.date_key
    WHERE t.year IN ({current_year}, {previous_year})
    GROUP BY t.year
    ORDER BY t.year DESC;
    """
    
    # 2. Query to get Top Performing Categories (Lifetime Revenue)
    # Note: Assumes a 'products' table exists with a 'category' column
    top_categories_query = """
    SELECT
        p.subcategory AS category,
        SUM(t.corrected_price) AS Revenue
    FROM transactions t
    JOIN products p ON t.product_id = p.product_id
    GROUP BY p.subcategory
    ORDER BY Revenue DESC
    LIMIT 5;
    """
    
    summary_df = fetch_data(conn, summary_query)
    categories_df = fetch_data(conn, top_categories_query)
    
    if summary_df.empty:
        return None, None
        
    # Python logic to calculate YoY Growth
    cp_data = summary_df[summary_df['year'] == current_year].iloc[0] if current_year in summary_df['year'].values else None
    pp_data = summary_df[summary_df['year'] == previous_year].iloc[0] if previous_year in summary_df['year'].values else None
    
    kpis = {}
    if cp_data is not None:
        kpis['Total Revenue'] = cp_data['TotalRevenue']
        kpis['Active Customers'] = cp_data['ActiveCustomers']
        kpis['Total Orders'] = cp_data['TotalOrders']
        kpis['AOV'] = cp_data['AOV']
        
        # Calculate Growth Rate
        if pp_data is not None and pp_data['TotalRevenue'] and pp_data['ActiveCustomers'] and pp_data['AOV']:
            kpis['Revenue Growth'] = ((cp_data['TotalRevenue'] - pp_data['TotalRevenue']) / pp_data['TotalRevenue']) 
            kpis['Customer Growth'] = ((cp_data['ActiveCustomers'] - pp_data['ActiveCustomers']) / pp_data['ActiveCustomers'])
            kpis['AOV Growth'] = ((cp_data['AOV'] - pp_data['AOV']) / pp_data['AOV'])
        else:
            # Set to 0 if previous period data is missing
            kpis['Revenue Growth'] = 0
            kpis['Customer Growth'] = 0
            kpis['AOV Growth'] = 0
            
    return kpis, categories_df

def display_executive_summary():
    """Renders the Streamlit UI for the Executive Summary."""
    conn = get_connection()
    if conn is None:
        st.warning("Database connection is not available. Please check the main application file for configuration errors.")
        return
        
    st.header("📊 Executive Summary Dashboard (Q1)")
    st.markdown("##### Key Business Metrics with Year-over-Year Comparison")
    
    kpis, categories_df = get_executive_summary(conn)

    if not kpis or categories_df.empty:
        st.info("No data found for the Executive Summary. Ensure your MySQL tables are populated, especially 'transactions'.")
        return

    # Create four columns for the KPI metrics
    col1, col2, col3, col4 = st.columns(4)

    # Helper function to display KPI with growth indicator
    def display_kpi(col, label, value, growth_rate, unit="₹"):
        with col:
            st.metric(
                label=label,
                # Format large numbers using millify (e.g., 1.5M)
                value=f"{unit}{millify(value, precision=2)}",
                # Display growth rate as a percentage delta
                delta=f"{growth_rate:.2%}" if growth_rate is not None else "N/A"
            )

    # --- KPI Row ---
    display_kpi(col1, "Total Revenue (YTD)", kpis['Total Revenue'], kpis['Revenue Growth'])
    display_kpi(col2, "Active Customers (YTD)", kpis['Active Customers'], kpis['Customer Growth'], unit="")
    display_kpi(col3, "Avg Order Value (AOV)", kpis['AOV'], kpis['AOV Growth'])
    
    with col4:
        st.metric(
            label="Total Orders",
            value=millify(kpis['Total Orders'], precision=0),
            delta="Total Orders YTD"
        )
        
    st.markdown("---")
    
    # --- Top Categories Visualization ---
    st.markdown("#### Top 5 Performing Categories (Revenue Trend)")
    st.bar_chart(categories_df.set_index('category')['Revenue'])

# Execute the display function when the page is loaded
def app():
    display_executive_summary()