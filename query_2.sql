-- category, city, country, customer_id, customer_name,
-- discount, market, order_date, order_id, order_priority,
-- product_id, product_name, profit, quantity, region,
-- sales, segment, ship_date, ship_mode, shipping_cost,
-- state, sub_category, order_year, order_month,
-- order_quarter, order_day_of_week, is_weekend,
-- order_week, discount_bin, profit_margin, sales_per_unit

USE superstore.db;

CREATE FUNCTION getNthHighestProfit (@N INT)
RETURNS INT
AS
BEGIN
    RETURN (
        SELECT profit
        FROM orders
        ORDER BY profit DESC
        OFFSET (@N - 1) ROWS
        FETCH NEXT 1 ROWS ONLY
    );
END;

SELECT superstore.getNthHighestProfit(10);