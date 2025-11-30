
# Amazon Sales Analytics 

## Overview  
This project builds a full analytics pipeline for Amazon-like sales data:  
- Cleans and preprocesses raw transaction data  
- Loads data into a MySQL data warehouse (with `products`, `customers`, `time_dimension`, `transactions` tables)  
- Provides dashboards (via Streamlit) for revenue analysis, product performance, customer analytics, operations & logistics, and strategic forecasting  

## 🎯 Goals  
- Analyze sales, revenue, customer behavior, product performance  
- Support business decisions: inventory planning, marketing, customer segmentation, seasonal planning  
- Provide interactive dashboards for stakeholders  
- Enable reproducible and auditable analytics  

## 📁 Folder / File Structure  
Amazon_Sales_Analytics/
├── DB_schema.sql # DDL for database tables
├── Data_Loader.py # ETL script: CSV → MySQL
├── requirements.txt # Python dependencies
├── app.py # Entry point for Streamlit multi-page app
├── pages/ # Streamlit pages
│ ├── _1_HOME.py
│ ├── _2_Executive_Dashboard.py
│ ├── _3_Revenue_Analytics.py
│ ├── _4_Customer_Analytics.py
│ ├── _5_Inventory_Analytics.py
│ ├── _6_Logistics.py
│ └── _7_Advanced_Analytics.py
├── utils/ # Utility modules
│ └── db_connection.py # DB connection helper
├── notebooks/ # (Optional) data exploration notebooks
│ ├── Data_Cleaning.ipynb
│ └── data_visualization.ipynb
└── README.md # This file

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


