import streamlit as st
import warnings
warnings.filterwarnings("ignore", category=UserWarning)


st.set_page_config(page_title='Amazon Sales', layout='wide')
st.sidebar.title('Navigation')
page = st.sidebar.selectbox('Go to', ['Home', 'Executive Dashboard','Revenue Analytics', 'Customer Analytics','Inventory Analytics','Logistics','Advanced Analytics' ])

if page == 'Home':
    from pages._1_HOME  import app as home_app
    home_app()
elif page == 'Executive Dashboard':
    from pages._2_Executive_Dashboard import app as Executive_app
    Executive_app()
elif page == 'Revenue Analytics':
    from pages._3_Revenue_Analytics import app as Revenue_app
    Revenue_app()
elif page == 'Inventory Analytics':
    from pages._5_Inventory_Analytics import app as Inventory_app
    Inventory_app()
elif page == 'Customer Analytics':
    from pages._4_Customer_Analytics import app as Customer_app
    Customer_app()
elif page == 'Logistics':
    from pages._6_Logistics import app as Logistics_app
    Logistics_app()
elif page == 'Advanced Analytics':
    from pages._7_Advanced_Analytics import app as Advanced_Analytics_app
    Advanced_Analytics_app()

