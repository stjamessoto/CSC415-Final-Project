# ============================================================
# bar_chart_demo.rl
# RetailLang example: chart generation across multiple
# chart types, dimensions, and filtered subsets
# ============================================================

# --- Bar charts ---

# Total revenue by region as a bar chart
Load sales.csv and compute total revenue by region and generate a bar chart

# Total profit by product as a bar chart
Load sales.csv and compute total profit by product and generate a bar chart

# Units sold by category as a bar chart
Load sales.csv and compute total units by category and generate a bar chart

# Average order value by channel
Load orders.csv and compute average total by channel and generate a bar chart

# Customer count by loyalty tier
Load customers.csv and compute count of customer_id by loyalty_tier
and generate a bar chart

# Customer count by segment
Load customers.csv and compute count of customer_id by segment
and generate a bar chart

# --- Filtered bar charts ---

# West region revenue by product
Load sales.csv, filter by region = West, compute total revenue by product,
and generate a bar chart

# East region revenue by product
Load sales.csv, filter by region = East, compute total revenue by product,
and generate a bar chart

# Completed orders only: revenue by region
Load orders.csv, filter by status = Completed, compute total total by region,
and generate a bar chart

# Online channel only: revenue by region
Load orders.csv, filter by channel = Online, compute total subtotal by region,
and generate a bar chart

# High-profit products only
Load sales.csv, filter by profit > 200, compute total revenue by product,
and generate a bar chart

# --- Line charts ---

# Revenue trend: line chart by region
Load sales.csv and compute total revenue by region and generate a line chart

# Profit trend by product: line chart
Load sales.csv and compute total profit by product and generate a line chart

# Average order value trend by channel
Load orders.csv and compute average total by channel and generate a line chart

# --- Pie charts ---

# Revenue share by region: pie chart
Load sales.csv and compute total revenue by region and generate a pie chart

# Profit share by category: pie chart
Load sales.csv and compute total profit by category and generate a pie chart

# Customer distribution by segment: pie chart
Load customers.csv and compute count of customer_id by segment
and generate a pie chart

# Order share by channel: pie chart
Load orders.csv and compute count of order_id by channel and generate a pie chart

# --- Titled charts ---

# Revenue by region with a custom title
Load sales.csv and compute total revenue by region
and generate a bar chart titled "2024 Revenue by Region"

# Profit by product with a custom title
Load sales.csv and compute total profit by product
and generate a bar chart titled "Product Profitability 2024"

# Corporate customer spend with a custom title
Load customers.csv, filter by segment = Corporate,
compute total total_spent by region,
and generate a bar chart titled "Corporate Spend by Region"