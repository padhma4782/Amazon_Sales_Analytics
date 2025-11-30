import pandas as pd
# Assuming utils.db_connection.get_connection is defined in your environment
from utils.db_connection import get_connection
import sys 

# Define the batch size for insertion
BATCH_SIZE = 5000 

def insert_in_batches(conn, sql, data, table_name):
    """Inserts a list of data rows into the specified table in batches."""
    cursor = conn.cursor()
    total_rows = len(data)
    inserted_count = 0
    
    print(f"Starting batch insertion into {table_name} (Total rows: {total_rows})...")
    
    for i in range(0, total_rows, BATCH_SIZE):
        batch = data[i:i + BATCH_SIZE]
        
        try:
            # 1. Execute the batch using executemany
            print(f"Preparing batch {i // BATCH_SIZE + 1} with {len(batch)} rows")

            cursor.executemany(sql, batch)
            
            # 2. CRITICAL: Commit the changes after a successful batch
            conn.commit() 
            
            # Note: cursor.rowcount here tells us how many rows were affected, 
            # including updates (for products) and ignores (for transactions/dims).
            # We track batch length for progress monitoring.
            inserted_count += len(batch)
            print(f"  -> Batch {i // BATCH_SIZE + 1} completed. Total processed: {inserted_count}/{total_rows}")
            
        except Exception as e:
            print(f"  -> ERROR in batch starting at row {i} for {table_name}: {e}. Rolling back batch and stopping.")
            
            # 3. Rollback the failed batch 
            conn.rollback() 
            
            cursor.close()
            return inserted_count # Return count of successfully processed rows
            
    cursor.close()
    print(f"Finished batch insertion for {table_name}.")
    return inserted_count


def populate_products_table():
    """Reads the CSV and inserts data into the products table using batching."""
    conn = None
    
    try:
        conn = get_connection()
        if conn is None or not conn.is_connected():
            print("ERROR: No database connection available for product population.")
            return

        print("\nAttempting to load and insert product data...")
        # Make sure 'amazon_india_products_catalog.csv' is in the same directory
        df = pd.read_csv("amazon_india_products_catalog.csv")
        
        # Prepare the DataFrame for insertion
        df = df.rename(columns={'rating': 'product_rating'})
        df = df[[
            'product_id', 'product_name', 'category', 'subcategory', 'brand', 'model', 
            'launch_year', 'base_price_2015', 'weight_kg', 'product_rating', 'is_prime_eligible'
        ]]
        
        # SQL uses ON DUPLICATE KEY UPDATE, suitable for Dimension tables
        sql = """
        INSERT INTO products (
            product_id, product_name, category, subcategory, brand, model, 
            launch_year, base_price_2015, weight_kg, product_rating, is_prime_eligible
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE 
            product_name=VALUES(product_name), category=VALUES(category), 
            subcategory=VALUES(subcategory), brand=VALUES(brand), model=VALUES(model);
        """
        
        # Convert DataFrame rows to a list of tuples for executemany
        data_to_insert = [tuple(row) for row in df.values]
        
        # 🟢 FIX: Use batch insertion for products for consistency and logging
        inserted_count = insert_in_batches(conn, sql, data_to_insert, 'products')
        print(f"Successfully processed {inserted_count} rows into the products table.")

    except Exception as e:
        print(f"Error during product data insertion: {e}")
        if conn and conn.is_connected():
            conn.rollback()

    finally:
        if conn and conn.is_connected():
            conn.close()
            print("Database connection closed after product population.")


def populate_data_from_cleaned_csv():
    """
    Loads data from cleaned.csv and populates customers, time_dimension, 
    and transactions tables.
    """
    conn = None
    
    try:
        conn = get_connection()
        if conn is None or not conn.is_connected():
            print("ERROR: No database connection available for cleaned data population.")
            return

        file_path = 'cleaned.csv' 
        
        print(f"\nLoading data from {file_path}...")
        df = pd.read_csv(file_path, low_memory=False)

        # 1. Parse date correctly
        #df['order_date'] = pd.to_datetime(df['order_date'], dayfirst=True, errors='coerce')
        df['order_date'] = pd.to_datetime(df['order_date'], format='%Y-%m-%d', errors='coerce')


        # 2. Drop bad dates
        df = df.dropna(subset=['order_date'])
        
        # --- Data Cleaning and Preparation ---
        #df['order_date'] = pd.to_datetime(df['order_date'], errors='coerce')
        #df = df.dropna(subset=['order_date']).copy()
        
        # --- A. time_dimension Data Preparation ---
        time_df = df[['order_date', 'festival_name']].drop_duplicates().copy()
        time_df['date_key'] = time_df['order_date'].dt.date
        time_df['day_of_week'] = time_df['order_date'].dt.dayofweek + 1 
        time_df['day_name'] = time_df['order_date'].dt.day_name()
        time_df['day_of_month'] = time_df['order_date'].dt.day
        time_df['month'] = time_df['order_date'].dt.month
        time_df['month_name'] = time_df['order_date'].dt.month_name()
        time_df['year'] = time_df['order_date'].dt.year
        time_df['quarter'] = time_df['order_date'].dt.quarter
        time_df['is_weekend'] = time_df['order_date'].dt.weekday >= 5
        time_df = time_df[['date_key', 'day_of_week', 'day_name', 'day_of_month', 'month', 
                           'month_name', 'quarter', 'year', 'is_weekend', 'festival_name']]
        
        # --- B. customers Data Preparation ---
        customers_df = df[['customer_id']].drop_duplicates().copy()
        customers_df['customer_segment'] = df['customer_spending_tier']
        customers_df['city'] = df['customer_city'] 
        customers_df['state'] = df['customer_state']
        customers_df['tier'] = df['customer_tier']
        customers_df['age_range'] = df['customer_age_group']  
        customers_df['is_prime_member'] = df['is_prime_member']
        # --- C. transactions Data Preparation ---


        # 3. Prepare transactions fact table
        # --- C. transactions Data Preparation ---

        transactions_df = df[['transaction_id', 'order_date', 'customer_id', 'product_id','original_price_inr', 'discount_percent','payment_method','delivery_days', 'corrected_price','return_status', 'customer_rating']].copy()

        transactions_df['date_key'] = transactions_df['order_date'].dt.date
        



        # 1. Parse dates (MANDATORY)
        transactions_df['order_date'] = pd.to_datetime(
            transactions_df['order_date'],
            format='%Y-%m-%d',
            errors='coerce'
        )

        # 2. Convert to Python date object
        transactions_df['date_key'] = transactions_df['order_date'].dt.date

        # 3. Drop rows with invalid dates
        transactions_df = transactions_df.dropna(subset=['date_key'])

        # 4. Remove order_date
        transactions_df.drop(columns=['order_date'], inplace=True)

        # FORCE clean all date formats from CSV
        transactions_df['date_key'] = pd.to_datetime(transactions_df['date_key'], errors='coerce')

        # Convert to python date (NOT string)
        transactions_df['date_key'] = transactions_df['date_key'].dt.date

        # Replace NaT or bad dates with NULL for MySQL
        transactions_df['date_key'] = transactions_df['date_key'].where(transactions_df['date_key'].notna(), None)

        print("Final date_key dtype:", transactions_df['date_key'].apply(type).unique())

        
        # 🟢 FIX: reorder columns to match SQL
        transactions_df = transactions_df[
            [
                'transaction_id',
                'date_key',
                'customer_id',
                'product_id',
                'original_price_inr',
                'discount_percent',
                'payment_method',
                'delivery_days',
                'corrected_price',
                'return_status',
                'customer_rating'
            ]
        ]



        # Debug print
        print("Sample transactions:\n", transactions_df.head(10))
        print("Type check:", type(transactions_df['date_key'].iloc[0]))
        print("Dtypes:\n", transactions_df.dtypes)
        print(transactions_df['date_key'].apply(type).unique())
        bad_rows = transactions_df[transactions_df['date_key'].astype(str) == '0000-00-00']
        print("Python bad rows:", len(bad_rows))
        print(bad_rows.head())


        
        # --- SQL Insertion Logic ---
        
        # 1. Insert into time_dimension (INSERT IGNORE based on date_key PK)
        time_sql = """
        INSERT IGNORE INTO time_dimension (
            date_key, day_of_week, day_name, day_of_month, month, 
            month_name, quarter, year, is_weekend, festival_name
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
        """
        time_data = [tuple(row) for row in time_df.values]
        #insert_in_batches(conn, time_sql, time_data, 'time_dimension')
        
        # 2. Insert into customers (INSERT IGNORE based on customer_id PK)
        customers_sql = """
        INSERT IGNORE INTO customers (
            customer_id, customer_segment,  city, state,tier, age_range, is_prime_member
        ) VALUES (%s, %s, %s,%s, %s, %s, %s);
        """
        customers_data = [tuple(row) for row in customers_df.values]
        #insert_in_batches(conn, customers_sql, customers_data, 'customers')
        
        # 3. Insert into transactions (Fact Table)
        transactions_sql = """
        INSERT   INTO transactions (
            transaction_id, date_key, customer_id, product_id, 
            original_price_inr, discount_percent, payment_method,delivery_days,corrected_price, 
            return_status, customer_rating
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s,%s,%s)
        ON DUPLICATE KEY UPDATE transaction_id = transaction_id;
        """
        transactions_data = [tuple(row) for row in transactions_df.values]
        insert_in_batches(conn, transactions_sql, transactions_data, 'transactions')
        
        print(f"Processed {len(transactions_data)} transactions in total.")
        
    except Exception as e:
        print(f"An error occurred during data processing or insertion: {e}")
        if conn and conn.is_connected():
            conn.rollback()
        
    finally:
        if conn and conn.is_connected():
            conn.close() 
            print("Database connection closed.")


if __name__ == "__main__":
    #populate_products_table()
    populate_data_from_cleaned_csv()