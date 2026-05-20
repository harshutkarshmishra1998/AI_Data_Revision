-- category, city, country, customer_id, customer_name,
-- discount, market, order_date, order_id, order_priority,
-- product_id, product_name, profit, quantity, region,
-- sales, segment, ship_date, ship_mode, shipping_cost,
-- state, sub_category, order_year, order_month,
-- order_quarter, order_day_of_week, is_weekend,
-- order_week, discount_bin, profit_margin, sales_per_unit

USE superstore.db;

-- 1. Find customers who bought same product multiple times
    -- WITH customer_sales AS(
    --     SELECT customer_name, product_name, ROW_NUMBER() OVER(PARTITION BY customer_id, product_id) AS sno
    --     FROM orders
    -- )
    -- SELECT DISTINCT customer_name, product_name FROM customer_sales WHERE sno > 1


-- 2. Find products bought together by same customer
    -- WITH products AS (
    -- SELECT DISTINCT o1.customer_name, o1.product_name
    -- FROM orders o1
    -- INNER JOIN orders o2 
    --     ON o1.order_id = o2.order_id
    -- ORDER BY o1.customer_name
    -- )
    -- SELECT customer_name, GROUP_CONCAT(product_name, ', ')
    -- FROM products
    -- GROUP BY customer_name


-- 3. Compare two orders of same customer
    -- SELECT DISTINCT o1.customer_name, o1.product_name, o1.profit, o2.product_name, o2.profit
    -- FROM orders o1
    -- INNER JOIN orders o2 
    --     ON o1.order_id = o2.order_id
    --     AND o1.product_name < o2.product_name
    -- ORDER BY o1.customer_name


-- 4. Find customers ordering in multiple regions
    -- Method #1
    -- SELECT customer_name, COUNT(city) AS city_count
    -- FROM orders
    -- GROUP BY customer_name
    -- HAVING city_count > 1

    -- Method #2
    -- WITH RankedRegions AS (
    -- SELECT customer_name, DENSE_RANK() OVER (PARTITION BY customer_id ORDER BY region) AS region_rank
    -- FROM orders)
    -- SELECT DISTINCT customer_name
    -- FROM RankedRegions
    -- WHERE region_rank > 1;


-- 5. Top N products per category
    -- WITH topn AS (
    --     SELECT category, product_name, DENSE_RANK() OVER (PARTITION BY category ORDER BY profit) AS ranked
    --     FROM orders
    -- )

    -- SELECT category, product_name
    -- FROM topn
    -- WHERE ranked <= 5


-- 6. Running totals
    -- SELECT product_name, profit, SUM(profit) OVER(ORDER BY profit DESC) AS running_total
    -- FROM orders


-- 7. Rolling 3-month average sales
WITH bucket AS (
    SELECT order_year, order_month, SUM(sales) AS total_monthly_sales
    FROM orders
    GROUP BY order_month, order_year
    ORDER BY order_year, order_month
)

SELECT order_year, order_month, AVG(total_monthly_sales) OVER(ORDER BY order_year, order_month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) AS rolling_avg
FROM bucket


-- Monthly revenue trend
-- Latest order per customer
-- Customers with no profit orders
-- Day-over-day growth
-- Month-over-month growth
-- Customer retention basics
-- Find repeat customers
-- Most profitable city per region
-- Lowest performing sub-category
-- Find seasonal sales trends
-- Identify high discount but low profit products
-- Calculate contribution % of category sales
-- Find top customer in every market
-- Find product with longest name
-- Find customers who bought same product multiple times
-- Find products bought together by same customer
-- Find pairs of customers from same city
-- Find customers with more than 5 orders
-- Find cities whose average profit is negative
-- Find products contributing top 10% revenue
-- Running sales by month
-- Running profit by category
-- Cumulative quantity sold
-- Compare current month sales with previous month
-- Find sales difference between consecutive orders