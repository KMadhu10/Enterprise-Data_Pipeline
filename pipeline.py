import os
import pandas as pd
import psycopg2
from psycopg2 import extras
from datetime import datetime
from dotenv import load_dotenv

# Load database credentials from the .env file
load_dotenv()

def get_db_connection():
    """Establishes a safe connection to the local PostgreSQL database."""
    try:
        return psycopg2.connect(
            host="localhost",
            database="fde_retail_db",
            user="postgres",
            password="admin123",  # Your verified database password
            port="5432"
        )
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return None


def generate_messy_client_data():
    """Simulates a chaotic raw dataset an FDE would receive from a client."""
    print("📦 Simulating raw, messy client data ingestion...")
    raw_data = {
        "order_id": ["ORD101", "ORD102", "ORD103", "ORD104", "ORD105"],
        "customer_id": ["CUST01", None, "CUST02", "CUST03", "CUST01"], 
        "customer_name": ["Alice Smith", "Unknown", "Bob Jones", "Charlie Brown", "Alice Smith"],
        "email": ["alice@email.com", "missing", "bob@email.com", "charlie@email.com", "alice@email.com"],
        "product_id": ["PROD_A", "PROD_B", "PROD_A", "PROD_C", "PROD_B"],
        "product_name": ["Wireless Mouse", "Mechanical Keyboard", "Wireless Mouse", "4K Monitor", "Mechanical Keyboard"],
        "category": ["Electronics", "Electronics", "Electronics", "Electronics", "Electronics"],
        "price": [25.00, 85.00, -10.00, 350.00, 85.00],        
        "quantity": [2, 1, 1, 1, 2],
        "order_date": ["2026-09-10", "2026/09/11", "2026-09-12", None, "2026-09-14"], 
        "shipping_status": ["Shipped", "Pending", "Pending", "Processing", "Shipped"]
    }
    return pd.DataFrame(raw_data)

def clean_and_process_data(df):
    """FDE Cleaning Logic using Pandas to enforce database constraints."""
    print("🧹 Cleaning and transforming data...")
    
    # 1. Drop rows where critical identification fields (like customer_id) are missing
    df = df.dropna(subset=["customer_id"])
    
    # 2. Fix pricing anomalies: filter out impossible negative prices
    df = df[df["price"] >= 0]
    
    # 3. Handle dates: fill missing dates with current time, and standardize strings to ISO format
    df["order_date"] = df["order_date"].fillna(datetime.now().strftime("%Y-%m-%d"))
    df["order_date"] = pd.to_datetime(df["order_date"].str.replace("/", "-")).dt.strftime("%Y-%m-%d %H:%M:%S")
    
    # 4. Feature Engineering: Calculate total transaction amount structurally
    df["total_amount"] = df["quantity"] * df["price"]
    
    print(f"✅ Data cleaned successfully. {len(df)} resilient rows remaining.")
    return df

def stream_to_postgres(df):
    """Streams the structured components directly into PostgreSQL using upsert syntax."""
    conn = get_db_connection()
    if not conn:
        return
    
    cursor = conn.cursor()
    try:
        customers = df[["customer_id", "customer_name", "email"]].drop_duplicates().values.tolist()
        products = df[["product_id", "product_name", "category", "price"]].drop_duplicates().values.tolist()
        orders = df[["order_id", "customer_id", "product_id", "quantity", "total_amount", "order_date", "shipping_status"]].values.tolist()
        
        print("🚀 Upserting data into 'customers' table...")
        extras.execute_values(cursor, """
            INSERT INTO customers (customer_id, customer_name, email) VALUES %s
            ON CONFLICT (customer_id) DO UPDATE SET customer_name = EXCLUDED.customer_name, email = EXCLUDED.email;
        """, customers)
        
        print("🚀 Upserting data into 'products' table...")
        extras.execute_values(cursor, """
            INSERT INTO products (product_id, product_name, category, price) VALUES %s
            ON CONFLICT (product_id) DO UPDATE SET price = EXCLUDED.price;
        """, products)
        
        print("🚀 Inserting transaction logs into 'orders' table...")
        extras.execute_values(cursor, """
            INSERT INTO orders (order_id, customer_id, product_id, quantity, total_amount, order_date, shipping_status) VALUES %s
            ON CONFLICT (order_id) DO NOTHING;
        """, orders)
        
        conn.commit()
        print("🌟 All pipelines executed perfectly! Data safely committed to PostgreSQL.")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Transaction rolled back due to error: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    raw_df = generate_messy_client_data()
    clean_df = clean_and_process_data(raw_df)
    stream_to_postgres(clean_df)
