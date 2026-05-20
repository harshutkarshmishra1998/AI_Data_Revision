-- category, city, country, customer_id, customer_name,
-- discount, market, order_date, order_id, order_priority,
-- product_id, product_name, profit, quantity, region,
-- sales, segment, ship_date, ship_mode, shipping_cost,
-- state, sub_category, order_year, order_month,
-- order_quarter, order_day_of_week, is_weekend,
-- order_week, discount_bin, profit_margin, sales_per_unit

USE superstore.db;

-- Find customers who bought same product multiple times

    -- WITH customer_sales AS(
    --     SELECT customer_name, product_name, ROW_NUMBER() OVER(PARTITION BY customer_id, product_id) AS sno
    --     FROM orders
    -- )
    -- SELECT DISTINCT customer_name, product_name FROM customer_sales WHERE sno > 1


-- Find products bought together by same customer

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


-- Compare two orders of same customer

    -- SELECT DISTINCT o1.customer_name, o1.product_name, o1.profit, o2.product_name, o2.profit
    -- FROM orders o1
    -- INNER JOIN orders o2 
    --     ON o1.order_id = o2.order_id
    --     AND o1.product_name < o2.product_name
    -- ORDER BY o1.customer_name


-- Find customers ordering in multiple regions

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