-- Copyright (C) 2026 Actian Corp.
-- All Rights Reserved.

-- Schema for all example extensions, on one database. INGRES.
--
-- Run with:
--     sql <db> < schema.ingres.sql
--
-- Then grant each table to the user the MCP server connects as, one
-- statement per table:
--     GRANT ALL ON products TO <app_user>;
--     \g
-- Repeat for orders, order_items, cart, customer_revenue, customers, sales.
--
-- Tables 1-4 back order_ops + catalog_insights + approval_required (e-commerce).
-- Tables 5-7 back revenue_extension (revenue).
--
-- The transaction and approval examples need the server in read-write mode
-- ("query_mode": "read-write").

DROP TABLE IF EXISTS order_items;
\g
DROP TABLE IF EXISTS cart;
\g
DROP TABLE IF EXISTS orders;
\g
DROP TABLE IF EXISTS products;
\g
DROP TABLE IF EXISTS sales;
\g
DROP TABLE IF EXISTS customers;
\g
DROP TABLE IF EXISTS customer_revenue;
\g

-- 1-4: e-commerce -----------------------------------------------------------
CREATE TABLE products (
    product_id INTEGER NOT NULL PRIMARY KEY,
    name       VARCHAR(50)   NOT NULL,
    unit_price DECIMAL(12,2) NOT NULL,                  -- place_order looks this up
    stock_qty  INTEGER       NOT NULL CHECK (stock_qty >= 0)  -- rollback on oversell
);
\g
CREATE TABLE orders (
    order_id    INTEGER NOT NULL PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    status      VARCHAR(20),
    total       DECIMAL(12,2)
);
\g
CREATE TABLE order_items (
    order_id   INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    qty        INTEGER NOT NULL,
    line_total DECIMAL(12,2),
    PRIMARY KEY (order_id, product_id)
);
\g
CREATE TABLE cart (
    customer_id INTEGER NOT NULL,
    product_id  INTEGER NOT NULL,
    qty         INTEGER NOT NULL,
    PRIMARY KEY (customer_id, product_id)
);
\g

-- 5-7: revenue --------------------------------------------------------------
CREATE TABLE customer_revenue (
    customer_id   INTEGER NOT NULL PRIMARY KEY,
    customer_name VARCHAR(100) NOT NULL,
    region        VARCHAR(10)  NOT NULL,
    total_revenue DECIMAL(12,2) NOT NULL
);
\g
CREATE TABLE customers (
    customer_id INTEGER NOT NULL PRIMARY KEY,
    vip         INTEGER NOT NULL
);
\g
CREATE TABLE sales (
    customer_id INTEGER NOT NULL,
    amount      DECIMAL(12,2) NOT NULL
);
\g

-- Seed data -----------------------------------------------------------------
INSERT INTO products VALUES (1, 'Widget', 10.00, 50);
\g
INSERT INTO products VALUES (2, 'Gadget', 25.00, 5);
\g
INSERT INTO cart VALUES (1001, 1, 3);
\g
INSERT INTO customer_revenue VALUES (1, 'Alice', 'NA', 90000);
\g
INSERT INTO customer_revenue VALUES (2, 'Bob', 'NA', 50000);
\g
INSERT INTO customer_revenue VALUES (3, 'Carol', 'EMEA', 70000);
\g
INSERT INTO customers VALUES (1, 0);
\g
INSERT INTO customers VALUES (2, 0);
\g
INSERT INTO customers VALUES (3, 0);
\g
COMMIT;
\g
