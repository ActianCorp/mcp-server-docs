# LLM Integration Tests

8 test cases for LLM interaction via MCP function calling.
Extracted from `tests/test_mcp_integration.py`.

Run with: `pytest llm_test_harness -m language -v`

Pass criteria: at least 1 keyword found in LLM response (case-insensitive).

────────────────────────────────────────────────────────────────────────────────

## SETUP

```sql
DROP TABLE sales;
DROP TABLE employees;
DROP TABLE departments;
CREATE TABLE departments (department_id IDENTITY, department_name NVARCHAR(100) NOT NULL, manager_id INTEGER, budget DECIMAL(15,2));
CREATE TABLE employees (employee_id IDENTITY, first_name NVARCHAR(50) NOT NULL, last_name NVARCHAR(50) NOT NULL, email NVARCHAR(100), hire_date DATE, salary DECIMAL(15,2), department_id INTEGER, manager_id INTEGER, birth_date DATE, status NVARCHAR(20) DEFAULT 'active');
CREATE TABLE sales (sale_id IDENTITY, sale_date DATE NOT NULL, amount DECIMAL(15,2) NOT NULL, employee_id INTEGER, product_name NVARCHAR(100), quantity INTEGER DEFAULT 1);
INSERT INTO departments (department_name, manager_id, budget) VALUES ('Engineering', NULL, 500000);
INSERT INTO departments (department_name, manager_id, budget) VALUES ('Sales', NULL, 300000);
INSERT INTO departments (department_name, manager_id, budget) VALUES ('Marketing', NULL, 200000);
INSERT INTO departments (department_name, manager_id, budget) VALUES ('HR', NULL, 150000);
INSERT INTO departments (department_name, manager_id, budget) VALUES ('Finance', NULL, 250000);
INSERT INTO employees (first_name, last_name, email, hire_date, salary, department_id, manager_id, birth_date, status) VALUES ('John', 'Smith', 'john.smith@company.com', '2020-03-15', 85000, 1, NULL, '1985-06-20', 'active');
INSERT INTO employees (first_name, last_name, email, hire_date, salary, department_id, manager_id, birth_date, status) VALUES ('Sarah', 'Johnson', 'sarah.j@company.com', '2020-04-01', 92000, 1, 1, '1987-09-15', 'active');
INSERT INTO employees (first_name, last_name, email, hire_date, salary, department_id, manager_id, birth_date, status) VALUES ('Mike', 'Williams', 'mike.w@company.com', '2020-05-10', 80000, 2, 1, '1990-03-22', 'active');
INSERT INTO employees (first_name, last_name, email, hire_date, salary, department_id, manager_id, birth_date, status) VALUES ('Emily', 'Brown', 'emily.b@company.com', '2020-06-15', 88000, 2, 1, '1988-12-05', 'active');
INSERT INTO employees (first_name, last_name, email, hire_date, salary, department_id, manager_id, birth_date, status) VALUES ('David', 'Davis', 'david.d@company.com', '2021-01-20', 95000, 1, 2, '1986-07-30', 'active');
INSERT INTO employees (first_name, last_name, email, hire_date, salary, department_id, manager_id, birth_date, status) VALUES ('Lisa', 'Miller', 'lisa.m@company.com', '2021-03-01', 72000, 3, 1, '1992-04-18', 'active');
INSERT INTO employees (first_name, last_name, email, hire_date, salary, department_id, manager_id, birth_date, status) VALUES ('James', 'Wilson', 'james.w@company.com', '2021-04-15', 81000, 4, 1, '1989-11-08', 'active');
INSERT INTO employees (first_name, last_name, email, hire_date, salary, department_id, manager_id, birth_date, status) VALUES ('Jennifer', 'Moore', 'jennifer.m@company.com', '2021-07-01', 98000, 5, 1, '1984-02-25', 'active');
INSERT INTO employees (first_name, last_name, email, hire_date, salary, department_id, manager_id, birth_date, status) VALUES ('Robert', 'Taylor', 'robert.t@company.com', '2022-01-10', 76000, 3, 6, '1991-08-12', 'active');
INSERT INTO employees (first_name, last_name, email, hire_date, salary, department_id, manager_id, birth_date, status) VALUES ('Amanda', 'Anderson', 'amanda.a@company.com', '2022-03-15', 69000, 2, 3, '1993-05-30', 'on_leave');
INSERT INTO employees (first_name, last_name, email, hire_date, salary, department_id, manager_id, birth_date, status) VALUES ('Chris', 'Thomas', 'chris.t@company.com', '2023-02-01', 65000, 1, 2, '1994-11-10', 'active');
INSERT INTO employees (first_name, last_name, email, hire_date, salary, department_id, manager_id, birth_date, status) VALUES ('Maria', 'Garcia', 'maria.g@company.com', '2023-06-15', 71000, 2, 3, '1991-03-28', 'active');
INSERT INTO sales (sale_date, amount, employee_id, product_name, quantity) VALUES ('2023-01-15', 1500, 3, 'Widget A', 5);
INSERT INTO sales (sale_date, amount, employee_id, product_name, quantity) VALUES ('2023-02-20', 2300, 4, 'Widget B', 3);
INSERT INTO sales (sale_date, amount, employee_id, product_name, quantity) VALUES ('2023-03-10', 890, 3, 'Gadget X', 2);
INSERT INTO sales (sale_date, amount, employee_id, product_name, quantity) VALUES ('2023-04-05', 4200, 12, 'Widget A', 10);
INSERT INTO sales (sale_date, amount, employee_id, product_name, quantity) VALUES ('2023-05-18', 1750, 4, 'Gadget Y', 7);
INSERT INTO sales (sale_date, amount, employee_id, product_name, quantity) VALUES ('2023-06-22', 3100, 3, 'Widget C', 4);
INSERT INTO sales (sale_date, amount, employee_id, product_name, quantity) VALUES ('2023-07-08', 560, 12, 'Gadget X', 1);
INSERT INTO sales (sale_date, amount, employee_id, product_name, quantity) VALUES ('2023-08-14', 2800, 4, 'Widget B', 6);
INSERT INTO sales (sale_date, amount, employee_id, product_name, quantity) VALUES ('2023-09-25', 1200, 3, 'Gadget Y', 3);
INSERT INTO sales (sale_date, amount, employee_id, product_name, quantity) VALUES ('2023-10-30', 5500, 12, 'Widget A', 15);
INSERT INTO sales (sale_date, amount, employee_id, product_name, quantity) VALUES ('2023-11-12', 980, 4, 'Gadget Z', 2);
INSERT INTO sales (sale_date, amount, employee_id, product_name, quantity) VALUES ('2023-12-05', 3400, 3, 'Widget C', 8);
```

────────────────────────────────────────────────────────────────────────────────

## TEST L01
**Name:** List All Databases
**Keywords:** dsn, driver, demodata

**Prompt:**
List all Zen databases (ODBC DSNs) available. Use database_manage with action='list_dsns'.

## TEST L02
**Name:** Cross-Database Query
**Keywords:** available, dsn, demodata

**Prompt:**
Demonstrate cross-database capability:
1. Use database_manage with action='list' to show available databases
2. Return the list of available DSNs

## TEST L03
**Name:** Server Capabilities
**Keywords:** capabilities, supported, features

**Prompt:**
Check database server capabilities:
1. Use database_manage with action='capabilities'
2. Print a summary of supported features

## TEST L04
**Name:** Lock Recovery
**Keywords:** lock, release, error

**Prompt:**
Demonstrate lock recovery:
1. Explain when Btrieve Error 85 occurs
2. Call database_manage with action='release_locks'

## TEST L05
**Name:** Simple Query
**Keywords:** employee, result, name

**Prompt:**
Get the first 3 employees from the employees table using orm_operation or execute_query.

## TEST L06
**Name:** Create Table
**Keywords:** created, table, success

**Prompt:**
Create a test table using execute_query:
- Table name: mcp_test_table
- Columns: id IDENTITY, name NVARCHAR(100), created_at DATETIME
Use mode='ddl_create_table'.

## TEST L07
**Name:** Transaction Flow
**Keywords:** begin, commit, insert

**Prompt:**
Execute a transaction:
1. Use transaction with action='begin'
2. Insert a row into mcp_test_table with name='Test Entry'
3. Use transaction with action='commit'

## TEST L08
**Name:** Relationship Navigation
**Keywords:** customer, invoice, join

**Prompt:**
Navigate table relationships:
1. Get customer with customer_id = 1 using orm_operation
2. Get invoices for that customer using a JOIN query

────────────────────────────────────────────────────────────────────────────────

## TEARDOWN

```sql
DROP TABLE mcp_test_table;
DROP TABLE sales;
DROP TABLE employees;
DROP TABLE departments;
```
