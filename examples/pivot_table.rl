# ============================================================
# pivot_table.rl
# RetailLang example: pivot table generation across
# multiple dimensions and filtered subsets
# ============================================================

# --- Basic pivot tables ---

# Revenue pivot: products as rows, regions as columns
Load sales.csv and create a pivot table by product and region

# Profit pivot: regions as rows, products as columns
Load sales.csv and create a pivot table by region and product

# Units pivot: product vs region
Load sales.csv and create a pivot table by product and category

# --- Pivot with explicit roles ---

# Revenue pivot with full role specification
Load sales.csv and build a pivot table with
region as rows, product as columns, revenue as values

# Profit pivot with full role specification
Load sales.csv and build a pivot table with
product as rows, region as columns, profit as values

# Units sold pivot with full role specification
Load sales.csv and build a pivot table with
category as rows, region as columns, units as values

# Cost pivot with full role specification
Load sales.csv and build a pivot table with
product as rows, region as columns, cost as values

# --- Customer pivot tables ---

# Total spend by segment and loyalty tier
Load customers.csv and build a pivot table with
segment as rows, loyalty_tier as columns, total_spent as values

# Order count by segment and region
Load customers.csv and build a pivot table with
segment as rows, region as columns, total_orders as values

# Average order value by segment and loyalty tier
Load customers.csv and build a pivot table with
loyalty_tier as rows, segment as columns, avg_order_value as values

# --- Order pivot tables ---

# Order totals by region and channel
Load orders.csv and build a pivot table with
region as rows, channel as columns, total as values

# Discount analysis by region and channel
Load orders.csv and build a pivot table with
region as rows, channel as columns, discount as values

# Tax breakdown by region and channel
Load orders.csv and build a pivot table with
region as rows, channel as columns, tax as values

# --- Product pivot tables ---

# Unit price by category and brand
Load products.csv and build a pivot table with
category as rows, brand as columns, unit_price as values

# Margin by category and subcategory
Load products.csv and build a pivot table with
category as rows, subcategory as columns, margin_pct as values

# Stock levels by category and brand
Load products.csv and build a pivot table with
category as rows, brand as columns, stock as values

# --- Filtered pivot tables ---

# West region only: revenue by product and category
Load sales.csv, filter by region = West,
and create a pivot table by product and category

# Electronics only: revenue by product and region
Load sales.csv, filter by category = Electronics,
and build a pivot table with product as rows, region as columns, revenue as values

# Completed orders only: totals by region and channel
Load orders.csv, filter by status = Completed,
and build a pivot table with region as rows, channel as columns, total as values

# Corporate customers only: spend by region and loyalty tier
Load customers.csv, filter by segment = Corporate,
and build a pivot table with region as rows, loyalty_tier as columns, total_spent as values

# High-margin products only
Load products.csv, filter by margin_pct > 35,
and create a pivot table by category and subcategory

# --- Pivot followed by chart ---

# Pivot then visualise: revenue by product and region, then chart
Load sales.csv, create a pivot table by product and region,
and generate a bar chart titled "Product Revenue by Region"

# Filtered pivot then chart
Load orders.csv, filter by channel = Online,
build a pivot table with region as rows, status as columns, total as values,
and generate a bar chart titled "Online Orders by Region and Status"