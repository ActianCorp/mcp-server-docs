-- Schema for all example extensions, on one database. ZEN (";"-terminated).
--
-- After loading, grant each table to the user the MCP server connects as, one
-- statement per table (Zen's GRANT takes a single table):
--     GRANT ALL ON products TO <app_user>;
-- Repeat for orders, order_items, cart, customer_revenue, customers, sales.
--
-- Tables 1-4 back order_ops + catalog_insights + approval_required (e-commerce).
-- Tables 5-7 back revenue_extension (revenue).
--
-- The transaction and approval examples need the server in read-write mode
-- ("query_mode": "read-write").
--
-- Only ANSI types are used (INTEGER / VARCHAR / DECIMAL) with lowercase unquoted
-- identifiers.
--
-- Zen does not support CHECK constraints, so this file enforces
-- "stock_qty >= 0" with a BEFORE UPDATE trigger instead. The trigger signals a
-- custom SQLSTATE to abort the update, giving the same effect the other engines
-- get from a CHECK constraint.
--
-- IMPORTANT: the CREATE TRIGGER statement below contains its own internal ";"
-- terminators (inside the BEGIN...END body). Load this file with a tool that
-- runs each top-level statement as a unit, for example Zen Control Center's
-- SQL Data Manager ("execute SQL script"), not a client that splits purely on
-- ";". If your tool cannot do that, create the trigger as a separate, single
-- execution after loading the rest of this file with a ";"-splitting tool.

DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS cart;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS sales;
DROP TABLE IF EXISTS customers;
DROP TABLE IF EXISTS customer_revenue;

-- 1-4: e-commerce -----------------------------------------------------------
CREATE TABLE products (
    product_id INTEGER NOT NULL PRIMARY KEY,
    name       VARCHAR(50)   NOT NULL,
    unit_price DECIMAL(12,2) NOT NULL,                  -- place_order looks this up
    stock_qty  INTEGER       NOT NULL                   -- trigger below: rollback on oversell
);
CREATE TABLE orders (
    order_id    INTEGER NOT NULL PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    status      VARCHAR(20),
    total       DECIMAL(12,2)
);
CREATE TABLE order_items (
    order_id   INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    qty        INTEGER NOT NULL,
    line_total DECIMAL(12,2),
    PRIMARY KEY (order_id, product_id)
);
CREATE TABLE cart (
    customer_id INTEGER NOT NULL,
    product_id  INTEGER NOT NULL,
    qty         INTEGER NOT NULL,
    PRIMARY KEY (customer_id, product_id)
);

-- Enforces stock_qty >= 0 (Zen has no CHECK constraint, see header comment).
-- SQLSTATE '70001' is in the implementation-defined range; change it if your
-- environment already uses that code for something else.
CREATE TRIGGER stock_qty_check
BEFORE UPDATE ON products
REFERENCING NEW AS n
FOR EACH ROW
BEGIN
    IF (n.stock_qty < 0) THEN
        SIGNAL '70001';
    END IF;
END;

-- 5-7: revenue --------------------------------------------------------------
CREATE TABLE customer_revenue (
    customer_id   INTEGER NOT NULL PRIMARY KEY,
    customer_name VARCHAR(100) NOT NULL,
    region        VARCHAR(10)  NOT NULL,
    total_revenue DECIMAL(12,2) NOT NULL
);
CREATE TABLE customers (
    customer_id INTEGER NOT NULL PRIMARY KEY,
    vip         INTEGER NOT NULL
);
CREATE TABLE sales (
    customer_id INTEGER NOT NULL,
    amount      DECIMAL(12,2) NOT NULL
);

-- Seed data -----------------------------------------------------------------
INSERT INTO products VALUES (1, 'Widget', 10.00, 50);
INSERT INTO products VALUES (2, 'Gadget', 25.00, 5);
INSERT INTO cart VALUES (1001, 1, 3);
INSERT INTO customer_revenue VALUES (1, 'Alice', 'NA', 90000);
INSERT INTO customer_revenue VALUES (2, 'Bob', 'NA', 50000);
INSERT INTO customer_revenue VALUES (3, 'Carol', 'EMEA', 70000);
INSERT INTO customers VALUES (1, 0);
INSERT INTO customers VALUES (2, 0);
INSERT INTO customers VALUES (3, 0);

-- No explicit COMMIT: Zen auto-commits each statement (CREATE TRIGGER takes
-- effect immediately and can't be rolled back).
