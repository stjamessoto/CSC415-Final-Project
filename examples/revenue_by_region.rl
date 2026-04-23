# ============================================================
# revenue_by_region.rl
# RetailLang example: revenue aggregation and analysis
# by region, product, and time dimension
# ============================================================

# --- Basic revenue by region ---

# Total revenue across all regions
Load sales.csv and compute total revenue by region

# Average revenue per region
Load sales.csv and compute average revenue by region

# Total revenue by region sorted highest first
Load sales.csv and compute total revenue by region and sort by revenue descending

# --- Revenue by product ---

# Total revenue per product
Load sales.csv and compute total revenue by product

# Total revenue by product sorted highest first
Load sales.csv and compute total revenue by product and sort by revenue descending

# Top products in the West region only
Load sales.csv, filter by region = West, compute total revenue by product,
and sort by revenue descending

# --- Revenue by category ---

# Revenue breakdown by category
Load sales.csv and compute total revenue by category

# Profit breakdown by category
Load sales.csv and compute total profit by category

# --- Filtered revenue ---

# Revenue for completed orders in the East region
Load orders.csv, filter by region = East, and compute total total by channel

# Revenue from online channel only
Load orders.csv, filter by channel = Online, and compute total subtotal by region

# Revenue from high-value orders only
Load orders.csv, filter by total > 1000, and compute total total by region

# Corporate customer revenue
Load customers.csv, filter by segment = Corporate,
and compute total total_spent by region

# --- Combined region and product ---

# Total profit by region and product
Load sales.csv and compute total profit by region

# Units sold by region
Load sales.csv and compute total units by region

# Cost analysis by region
Load sales.csv and compute total cost by region