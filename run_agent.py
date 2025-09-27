# inventory_agent_ai.py

import os
import json
import pandas as pd
import numpy as np
from dotenv import load_dotenv
from google import genai

# =========================
# 1. Load Environment & Gemini AI
# =========================
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("❌ GEMINI_API_KEY not found in environment variables")

client = genai.Client(api_key=GEMINI_API_KEY)

# =========================
# 2. Load Inventory & Config
# =========================
STOCK_FILE = "Stock.csv"
SALES_FILE = "Sales.csv"
CONFIG_FILE = "meta.json"

stock_df = pd.read_csv(STOCK_FILE)
sales_df = pd.read_csv(SALES_FILE)

with open(CONFIG_FILE, "r") as f:
    config = json.load(f)

lead_times = config["lead_time_days"]
batch_size = config["manufacturing_batch_size"]

# =========================
# 3. Helper Functions
# =========================
def get_current_stock(product_id: str, city: str = None):
    df = stock_df[stock_df["product_id"] == product_id]
    if city:
        df = df[df["city_name"].str.lower() == city.lower()]
    return df[["product_id", "product_name", "city_name", "stock"]]

def get_total_sales(product_id: str, city: str = None):
    df = sales_df[sales_df["product_id"] == product_id]
    if city:
        df = df[df["city_name"].str.lower() == city.lower()]
    return int(df["units_sold"].sum())

def get_average_daily_sales(product_id: str, city: str = None):
    sales_df["date"] = pd.to_datetime(sales_df["date"], errors="coerce")
    df = sales_df[sales_df["product_id"] == product_id]
    if city:
        df = df[df["city_name"].str.lower() == city.lower()]
    if df.empty:
        return 0
    daily_sales = df.groupby(df["date"].dt.date)["units_sold"].sum()
    return float(daily_sales.mean())

def get_monthly_sales(product_id: str, city: str = None):
    sales_df["date"] = pd.to_datetime(sales_df["date"], errors="coerce")
    df = sales_df[sales_df["product_id"] == product_id]
    if city:
        df = df[df["city_name"].str.lower() == city.lower()]
    monthly_sales = df.groupby(df["date"].dt.to_period("M"))["units_sold"].sum().reset_index()
    monthly_sales["date"] = monthly_sales["date"].astype(str)
    monthly_sales["units_sold"] = monthly_sales["units_sold"].astype(int)
    return monthly_sales

def check_reorder(product_id: str, city: str = None):
    df_stock = stock_df[stock_df["product_id"] == product_id]
    if city:
        df_stock = df_stock[df_stock["city_name"].str.lower() == city.lower()]
    current_stock = int(df_stock["stock"].sum())

    avg_daily_sales = get_average_daily_sales(product_id, city)
    lead_time_key = product_id.replace("SKU", "SKU-")
    lead_time = lead_times.get(lead_time_key, 5)
    reorder_point = avg_daily_sales * lead_time

    reorder_needed = current_stock <= reorder_point
    recommended_units = max(batch_size.get(product_id, 10), int(reorder_point - current_stock)) if reorder_needed else 0

    message = f"Reorder needed: {reorder_needed}. Current stock = {current_stock}, Reorder Point = {reorder_point:.2f}"

    return {
        "reorder_needed": reorder_needed,
        "recommended_order_units": recommended_units,
        "message": message
    }

def convert_numpy(obj):
    if isinstance(obj, (np.integer, np.int64)):
        return int(obj)
    if isinstance(obj, (np.floating, np.float64)):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    return obj

# =========================
# 4. Main Run
# =========================
if __name__ == "__main__":
    product_id = input("Enter Product ID (e.g., SKU5, SKU10): ").strip()

    # Overall inventory metrics
    overall_stock = int(stock_df[stock_df["product_id"] == product_id]["stock"].sum())
    overall_sales = get_total_sales(product_id)
    overall_avg_daily = get_average_daily_sales(product_id)

    print(f"\n📊 Overall Inventory Summary for {product_id} (All Cities):")
    print(f"Current Stock       : {overall_stock}")
    print(f"Total Units Sold    : {overall_sales}")
    print(f"Average Daily Sales : {overall_avg_daily:.2f}\n")

    # City selection
    city_list = stock_df["city_name"].unique()
    print("Select a city for detailed report:")
    for idx, c in enumerate(city_list, start=1):
        print(f"{idx}. {c}")

    while True:
        try:
            choice = int(input("Enter city number: "))
            if 1 <= choice <= len(city_list):
                city = city_list[choice - 1]
                break
            else:
                print("❌ Invalid choice. Try again.")
        except ValueError:
            print("❌ Please enter a valid number.")

    # City-specific metrics
    current_stock = get_current_stock(product_id, city).to_dict(orient="records")
    total_sales = get_total_sales(product_id, city)
    avg_daily_sales = get_average_daily_sales(product_id, city)
    monthly_sales = get_monthly_sales(product_id, city).to_dict(orient="records")
    reorder_info = check_reorder(product_id, city)

    results = {
        "current_stock": current_stock,
        "total_sales": {product_id: total_sales},
        "average_daily_sales": {product_id: avg_daily_sales},
        "monthly_sales": {product_id: monthly_sales},
        "reorder_check": {product_id: reorder_info}
    }

    # Save JSON report
    output_file = f"inventory_report_{product_id}_{city}.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=4, default=convert_numpy)

    print(f"\n✅ City-specific inventory report saved to {output_file}")

    # =========================
    # 5. Generate AI Recommendation
    # =========================
    sample_inventory_prompt = f"""
    You are an inventory assistant.
    Given the following product details, provide a short recommendation in JSON format:

    Product: {product_id}
    City: {city}
    Current Stock: {current_stock[0]['stock']} units
    Average Daily Sales: {avg_daily_sales:.2f} units/day
    Lead Time: {lead_times.get(product_id.replace("SKU","SKU-"),5)} days

    Return JSON like this:
    {{
        "product_id": "{product_id}",
        "city": "{city}",
        "reorder_needed": true/false,
        "recommended_order_units": number,
        "message": "message"
    }}
    """

    response = client.models.generate_content(model="gemini-2.5-flash", contents=sample_inventory_prompt)

    try:
        parsed = json.loads(response.text)
        readable_response = json.dumps(parsed, indent=4)
    except json.JSONDecodeError:
        readable_response = response.text.strip()

    print("\n💡 AI Recommendation:\n")
    print(readable_response)
