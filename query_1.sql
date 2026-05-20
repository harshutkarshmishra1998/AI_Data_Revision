USE superstore.db;

-- SELECT * FROM orders

SELECT country, AVG(sales) 
FROM orders 
GROUP BY country