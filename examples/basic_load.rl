# ============================================================
# basic_load.rl
# RetailLang example: loading and inspecting a dataset
# ============================================================

# Load a CSV file into memory
Load sales.csv

# Load with an alias for reference
Load orders.csv as orders

# Load and immediately preview by computing a simple count
Load customers.csv and compute count of customer_id by segment

# Load a product catalog
Load products.csv and compute count of product_id by category