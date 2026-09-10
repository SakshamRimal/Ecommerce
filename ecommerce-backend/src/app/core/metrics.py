from prometheus_client import Counter, Histogram

orders_created_total = Counter(
    "orders_created_total",
    "Total number of orders created",
)
orders_failed_total = Counter(
    "orders_failed_total",
    "Total number of orders creation failed",
    ["reason"],
)

order_value_dollars = Histogram(
    "order_value_dollars",
    "Distribution of order values in dollars",
)
