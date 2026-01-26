CREATE TABLE customers (
    customer_id INT,
    email VARCHAR(50)
);\g

CREATE TABLE orders (
    order_id INT,
    customer_id INT,
    order_date DATE,
    total_amount MONEY
);\g

INSERT INTO customers (customer_id, email)
VALUES (101, 'alice@tech.com'),
       (102, 'bob@corp.net'),
       (103, 'carol@design.io');\g

INSERT INTO orders (order_id, customer_id, order_date, total_amount)
VALUES (51, 101, '2026-10-01', 150.00),
       (52, 101, '2026-10-05', 45.99),
       (53, 102, '2026-11-02', 899.50),
       (54, 103, '2026-12-12', 25.00)\g

COMMIT;\g
