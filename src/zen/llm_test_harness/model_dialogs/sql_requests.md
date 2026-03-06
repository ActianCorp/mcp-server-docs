# SQL Regression Tests

20 SQL test cases for direct execution against Zen database.
Extracted from `run_regression_tests.py`.

Run with: `pytest llm_test_harness -m sql -v`

────────────────────────────────────────────────────────────────────────────────

## SETUP

```sql
DROP TABLE invoices;
DROP TABLE sales;
DROP TABLE employees;
DROP TABLE departments;
CREATE TABLE departments (department_id IDENTITY, department_name NVARCHAR(100) NOT NULL, manager_id INTEGER, budget DECIMAL(15,2));
CREATE TABLE employees (employee_id IDENTITY, first_name NVARCHAR(50) NOT NULL, last_name NVARCHAR(50) NOT NULL, email NVARCHAR(100), hire_date DATE, salary DECIMAL(15,2), department_id INTEGER, manager_id INTEGER, birth_date DATE, status NVARCHAR(20) DEFAULT 'active');
CREATE TABLE sales (sale_id IDENTITY, sale_date DATE NOT NULL, amount DECIMAL(15,2) NOT NULL, employee_id INTEGER, product_name NVARCHAR(100), quantity INTEGER DEFAULT 1);
CREATE TABLE invoices (invoice_id INTEGER PRIMARY KEY, employee_id INTEGER NOT NULL REFERENCES employees(employee_id), amount DECIMAL(15,2), invoice_date DATE);
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
INSERT INTO invoices VALUES (1, 1, 1500.00, '2024-01-15');
INSERT INTO invoices VALUES (2, 2, 2300.00, '2024-02-20');
INSERT INTO invoices VALUES (3, 3, 890.00, '2024-03-10');
```

────────────────────────────────────────────────────────────────────────────────

## TEST R01
**Name:** Long-Tenure Employees
**Description:** Show employees working >2 years with ID, name, hire date
**Validate:** rows > 0, columns: employee_id, first_name, last_name, hire_date

```sql
SELECT employee_id, first_name, last_name, hire_date
FROM employees
WHERE hire_date < '2024-02-03'
ORDER BY hire_date
```

## TEST R02
**Name:** Monthly Sales Summary
**Description:** 2023 sales by month with count and revenue
**Validate:** rows > 0, columns: year, month, sales_count, total_revenue

```sql
SELECT YEAR(sale_date) AS year,
       MONTH(sale_date) AS month,
       COUNT(*) AS sales_count,
       SUM(amount) AS total_revenue
FROM sales
WHERE YEAR(sale_date) = 2023
GROUP BY YEAR(sale_date), MONTH(sale_date)
ORDER BY year, month
```

## TEST R03
**Name:** Employee Contact List
**Description:** Full name uppercase, email, email length for employees with email
**Validate:** rows > 0, columns: full_name, email, email_length

```sql
SELECT UPPER(first_name + ' ' + last_name) AS full_name,
       email,
       LENGTH(email) AS email_length
FROM employees
WHERE email IS NOT NULL
ORDER BY last_name, first_name
```

## TEST R04
**Name:** Above-Average Earners
**Description:** Employees earning more than department average
**Validate:** rows > 0, columns: employee_id, name, salary, department_name, above_average

```sql
SELECT e.employee_id,
       e.first_name + ' ' + e.last_name AS name,
       e.salary,
       d.department_name,
       e.salary - (SELECT AVG(e2.salary)
                  FROM employees e2
                  WHERE e2.department_id = e.department_id) AS above_average
FROM employees e
JOIN departments d ON e.department_id = d.department_id
WHERE e.salary > (SELECT AVG(e2.salary)
                FROM employees e2
                WHERE e2.department_id = e.department_id)
ORDER BY above_average DESC
```

## TEST R05
**Name:** Salary Peer Analysis
**Description:** Same department employees with salaries within $5000
**Validate:** rows > 0, columns: employee1, employee2, salary1, salary2, salary_difference

```sql
SELECT e1.first_name + ' ' + e1.last_name AS employee1,
       e2.first_name + ' ' + e2.last_name AS employee2,
       e1.salary AS salary1,
       e2.salary AS salary2,
       ABS(e1.salary - e2.salary) AS salary_difference
FROM employees e1
JOIN employees e2 ON e1.department_id = e2.department_id
WHERE e1.employee_id < e2.employee_id
  AND ABS(e1.salary - e2.salary) <= 5000
ORDER BY salary_difference
```

## TEST R06
**Name:** Department Size Filter
**Description:** Departments with >2 employees showing count, avg salary, total payroll
**Validate:** rows > 0, columns: department_name, employee_count, avg_salary, total_payroll

```sql
SELECT d.department_name,
       COUNT(e.employee_id) AS employee_count,
       AVG(e.salary) AS avg_salary,
       SUM(e.salary) AS total_payroll
FROM departments d
LEFT JOIN employees e ON d.department_id = e.department_id
GROUP BY d.department_name
HAVING COUNT(e.employee_id) > 2
ORDER BY employee_count DESC
```

## TEST R07
**Name:** Department Performance Overview
**Description:** All departments with employees, sales revenue, revenue per employee
**Validate:** rows > 0, columns: department_name, employee_count, total_revenue, revenue_per_employee

```sql
SELECT d.department_name,
       COUNT(DISTINCT e.employee_id) AS employee_count,
       ISNULL(SUM(s.amount), 0) AS total_revenue,
       CASE WHEN COUNT(DISTINCT e.employee_id) > 0
            THEN ISNULL(SUM(s.amount), 0) / COUNT(DISTINCT e.employee_id)
            ELSE 0
       END AS revenue_per_employee
FROM departments d
LEFT JOIN employees e ON d.department_id = e.department_id
LEFT JOIN sales s ON e.employee_id = s.employee_id
GROUP BY d.department_name
ORDER BY total_revenue DESC
```

## TEST R08
**Name:** Salary Classification
**Description:** Classify employees into Senior/Mid-level/Junior brackets
**Validate:** rows > 0, columns: employee_id, name, salary, salary_bracket

```sql
SELECT employee_id,
       first_name + ' ' + last_name AS name,
       salary,
       CASE
           WHEN salary >= 90000 THEN 'Senior'
           WHEN salary >= 75000 THEN 'Mid-level'
           ELSE 'Junior'
       END AS salary_bracket
FROM employees
ORDER BY salary DESC
```

## TEST R09
**Name:** Product Sales Performance
**Description:** Sales by product with count, revenue, avg, min, max
**Validate:** rows > 0, columns: product_name, sales_count, total_revenue, avg_sale, min_sale, max_sale

```sql
SELECT product_name,
       COUNT(*) AS sales_count,
       SUM(amount) AS total_revenue,
       AVG(amount) AS avg_sale,
       MIN(amount) AS min_sale,
       MAX(amount) AS max_sale
FROM sales
GROUP BY product_name
ORDER BY total_revenue DESC
```

## TEST R10
**Name:** Employee Order by Salary (ROW_NUMBER workaround)
**Description:** Employees within dept sorted by salary with ranking using correlated subquery
**Validate:** rows > 0, columns: name, department_name, salary, dept_rank

```sql
SELECT e1.first_name + ' ' + e1.last_name AS name,
       d.department_name,
       e1.salary,
       (SELECT COUNT(*) + 1 FROM employees e2
        WHERE e2.department_id = e1.department_id
        AND e2.salary > e1.salary) AS dept_rank
FROM employees e1
JOIN departments d ON e1.department_id = d.department_id
ORDER BY d.department_name, dept_rank
```

## TEST R11
**Name:** Manager's Team Overview
**Description:** All employees with their manager's name
**Validate:** rows > 0, columns: employee_id, employee_name, manager_name

```sql
SELECT e.employee_id,
       e.first_name + ' ' + e.last_name AS employee_name,
       m.first_name + ' ' + m.last_name AS manager_name
FROM employees e
LEFT JOIN employees m ON e.manager_id = m.employee_id
ORDER BY manager_name, employee_name
```

## TEST R12
**Name:** Recent Hires
**Description:** Employees hired in last 3 years
**Validate:** rows > 0, columns: employee_id, employee_name, hire_date, department_id

```sql
SELECT employee_id,
       first_name + ' ' + last_name AS employee_name,
       hire_date,
       department_id
FROM employees
WHERE hire_date >= '2023-02-03'
ORDER BY hire_date DESC
```

## TEST R13
**Name:** Sales by Employee
**Description:** Sales performance per employee with count and revenue
**Validate:** rows > 0, columns: employee_name, sales_count, total_revenue

```sql
SELECT e.first_name + ' ' + e.last_name AS employee_name,
       COUNT(s.sale_id) AS sales_count,
       SUM(s.amount) AS total_revenue
FROM employees e
JOIN sales s ON e.employee_id = s.employee_id
GROUP BY e.first_name, e.last_name
ORDER BY total_revenue DESC
```

## TEST R14
**Name:** Active vs Inactive Comparison
**Description:** Compare employee groups by status
**Validate:** rows > 0, columns: status, employee_count, avg_salary, highest_salary

```sql
SELECT status,
       COUNT(*) AS employee_count,
       AVG(salary) AS avg_salary,
       MAX(salary) AS highest_salary
FROM employees
GROUP BY status
HAVING COUNT(*) > 0
ORDER BY status
```

## TEST R15
**Name:** Department Budget Analysis
**Description:** Departments where budget > payroll
**Validate:** rows > 0, columns: department_name, budget, total_payroll, budget_surplus

```sql
SELECT d.department_name,
       d.budget,
       SUM(e.salary) AS total_payroll,
       d.budget - SUM(e.salary) AS budget_surplus
FROM departments d
LEFT JOIN employees e ON d.department_id = e.department_id
GROUP BY d.department_name, d.budget
HAVING d.budget > SUM(e.salary)
ORDER BY budget_surplus DESC
```

## TEST R16
**Name:** Sales with Employee Details
**Description:** Sales with employee info, first 10
**Validate:** rows > 0, columns: sale_id, employee_id, first_name, last_name, amount

```sql
SELECT TOP 10 s.sale_id,
       e.employee_id,
       e.first_name,
       e.last_name,
       s.amount
FROM sales s
JOIN employees e ON s.employee_id = e.employee_id
ORDER BY s.sale_id
```

## TEST R17
**Name:** Department Employee Roster
**Description:** Engineering dept roster with dept name and employees
**Validate:** rows > 0, columns: department_name, first_name, last_name

```sql
SELECT d.department_name,
       e.first_name,
       e.last_name
FROM departments d
LEFT JOIN employees e ON d.department_id = e.department_id
WHERE d.department_name = 'Engineering'
ORDER BY e.last_name
```

## TEST R18
**Name:** Sales Performance by Department
**Description:** Sales with employee and department, first 10
**Validate:** rows > 0, columns: sale_id, employee_name, department_name, amount

```sql
SELECT TOP 10 s.sale_id,
       e.first_name + ' ' + e.last_name AS employee_name,
       d.department_name,
       s.amount
FROM sales s
JOIN employees e ON s.employee_id = e.employee_id
JOIN departments d ON e.department_id = d.department_id
ORDER BY s.sale_id
```

## TEST R19
**Name:** Employee Salary Distribution
**Description:** Count employees in each salary range
**Validate:** rows > 0, columns: salary_range, employee_count

```sql
SELECT
    CASE
        WHEN salary < 70000 THEN 'Under 70K'
        WHEN salary < 80000 THEN '70K-80K'
        WHEN salary < 90000 THEN '80K-90K'
        ELSE 'Over 90K'
    END AS salary_range,
    COUNT(*) AS employee_count
FROM employees
GROUP BY
    CASE
        WHEN salary < 70000 THEN 'Under 70K'
        WHEN salary < 80000 THEN '70K-80K'
        WHEN salary < 90000 THEN '80K-90K'
        ELSE 'Over 90K'
    END
ORDER BY salary_range
```

## TEST R20
**Name:** Cross-Department Sales Analysis
**Description:** Sales with full context, top 5 by amount
**Validate:** rows > 0, columns: sale_id, first_name, last_name, department_name, amount, product_name

```sql
SELECT TOP 5 s.sale_id,
       e.first_name,
       e.last_name,
       d.department_name,
       s.amount,
       s.product_name
FROM sales s
JOIN employees e ON s.employee_id = e.employee_id
JOIN departments d ON e.department_id = d.department_id
ORDER BY s.amount DESC
```

────────────────────────────────────────────────────────────────────────────────

## TEARDOWN

```sql
DROP TABLE invoices;
DROP TABLE sales;
DROP TABLE employees;
DROP TABLE departments;
```
