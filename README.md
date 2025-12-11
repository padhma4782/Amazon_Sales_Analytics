
# Amazon Sales Analytics 

## Overview  
This project builds a full analytics pipeline for Amazon-like sales data:  
- Cleans and preprocesses raw transaction data  
- Loads data into a MySQL data warehouse (with `products`, `customers`, `time_dimension`, `transactions` tables)  
- Provides dashboards (via Streamlit) for revenue analysis, product performance, customer analytics, operations & logistics, and strategic forecasting  

## Goals  
- Analyze sales, revenue, customer behavior, product performance  
- Support business decisions: inventory planning, marketing, customer segmentation, seasonal planning  
- Provide interactive dashboards for stakeholders  
- Enable reproducible and auditable analytics  

## Folder / File Structure  
See files under pages/ and utils/. 

##  Setup & Installation  

1. Clone the repo  
   git clone https://github.com/your-username/Amazon_Sales_Analytics.git
   cd Amazon_Sales_Analytics
2. Create a Python virtual environment
python -m venv venv
source venv/bin/activate    # On Windows: venv\Scripts\activate
3. Install dependencies
pip install -r requirements.txt
4. Create MySQL database & tables
mysql -u root -p < DB_schema.sql
5. Run data loader script
python Data_Loader.py
6.Run the Streamlit app
streamlit run app.py


