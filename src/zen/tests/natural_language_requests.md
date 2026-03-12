# Natural Language Test Requests

Self-contained test file for LLM integration testing via MCP tools.

## File Structure

This file has three sections, processed by the test runner:

1. **SETUP** — SQL statements executed directly (no LLM) before tests.
   Creates tables and loads test data. Edit freely: add tables, rows,
   columns. Each SQL statement must be on its own line.
   Runner calls `execute_query` for each line programmatically.

2. **TEST sections** — English prompts sent to LLM via OpenRouter.
   LLM decides which MCP tools to call and what SQL to generate.
   Optional directives: `**Keywords:**`, `**Validate:**`

3. **TEARDOWN** — SQL statements executed directly (no LLM) after tests.
   Drops tables created in SETUP. Keep in sync with SETUP.

To add test data: edit the SETUP sql block (add CREATE/INSERT statements)
and the TEARDOWN sql block (add matching DROP statements).

Current schema: departments, employees, sales, projects, project_assignments.

────────────────────────────────────────────────────────────────────────────────

## SETUP

```sql
DROP TABLE project_assignments;
DROP TABLE projects;
CREATE TABLE projects (project_id IDENTITY, project_name NVARCHAR(100) NOT NULL, start_date DATE, end_date DATE, budget DECIMAL(15,2), status NVARCHAR(20) DEFAULT 'active');
CREATE TABLE project_assignments (assignment_id IDENTITY, project_id INTEGER, employee_id INTEGER, assigned_date DATE, hours_allocated DECIMAL(8,2), role NVARCHAR(50));
INSERT INTO projects (project_name, start_date, end_date, budget, status) VALUES ('Project Alpha', '2023-01-01', '2023-12-31', 100000, 'completed');
INSERT INTO projects (project_name, start_date, end_date, budget, status) VALUES ('Project Beta', '2023-06-01', '2024-06-30', 200000, 'active');
INSERT INTO projects (project_name, start_date, end_date, budget, status) VALUES ('Project Gamma', '2024-01-01', '2024-12-31', 150000, 'active');
INSERT INTO projects (project_name, start_date, end_date, budget, status) VALUES ('Project Delta', '2024-03-01', NULL, 80000, 'planning');
INSERT INTO project_assignments (project_id, employee_id, assigned_date, hours_allocated, role) VALUES (1, 1, '2023-01-15', 200, 'Lead');
INSERT INTO project_assignments (project_id, employee_id, assigned_date, hours_allocated, role) VALUES (1, 2, '2023-02-01', 160, 'Developer');
INSERT INTO project_assignments (project_id, employee_id, assigned_date, hours_allocated, role) VALUES (1, 5, '2023-03-01', 120, 'Developer');
INSERT INTO project_assignments (project_id, employee_id, assigned_date, hours_allocated, role) VALUES (2, 3, '2023-06-15', 180, 'Lead');
INSERT INTO project_assignments (project_id, employee_id, assigned_date, hours_allocated, role) VALUES (2, 4, '2023-07-01', 140, 'Analyst');
INSERT INTO project_assignments (project_id, employee_id, assigned_date, hours_allocated, role) VALUES (2, 11, '2023-08-01', 100, 'Developer');
INSERT INTO project_assignments (project_id, employee_id, assigned_date, hours_allocated, role) VALUES (3, 2, '2024-01-10', 200, 'Lead');
INSERT INTO project_assignments (project_id, employee_id, assigned_date, hours_allocated, role) VALUES (3, 5, '2024-01-15', 160, 'Developer');
INSERT INTO project_assignments (project_id, employee_id, assigned_date, hours_allocated, role) VALUES (3, 9, '2024-02-01', 120, 'Tester');
INSERT INTO project_assignments (project_id, employee_id, assigned_date, hours_allocated, role) VALUES (4, 6, '2024-03-15', 80, 'Analyst');
```

────────────────────────────────────────────────────────────────────────────────

## TEARDOWN

```sql
DROP TABLE project_assignments;
DROP TABLE projects;
```

────────────────────────────────────────────────────────────────────────────────

## TEST 1: Long-Tenure Employees

Show me employees who have been working at the company for more than 2 years.
I need to see their ID, name, and when they were hired.

**Keywords:** employee, hire, name

────────────────────────────────────────────────────────────────────────────────

## TEST 2: Monthly Sales Summary

> I want to see how our sales performed in 2023, broken down by month.
> For each month, show me the number of sales and the total revenue.

**Keywords:** sales, month, revenue

────────────────────────────────────────────────────────────────────────────────

## TEST 3: Employee Contact List

> Give me a contact list of all employees. For each person, show their full name in uppercase,
> their email address, and how long the email address is. Only include people who have an email.

**Keywords:** employee, email, name

────────────────────────────────────────────────────────────────────────────────

## TEST 4: Above-Average Earners

> I want to identify high earners in each department. Show me employees who earn more than
> the average salary in their own department. Tell me how much more they're making compared
> to their department's average.

**Keywords:** salary, department, average

────────────────────────────────────────────────────────────────────────────────

## TEST 5: Salary Peer Analysis

> Find employees who work in the same department and have similar salaries - let's say within
> $5,000 of each other. Show me both employees' names, their salaries, and the exact difference.
> I don't want to see the same pair twice.

**Keywords:** salary, employee, department

────────────────────────────────────────────────────────────────────────────────

## TEST 6: Department Size Filter

> Show me departments that have more than 2 employees. For each qualifying department,
> tell me the department name, how many employees, average salary, and total payroll.

**Keywords:** department, employee, salary

**Validate:** rows > 0

────────────────────────────────────────────────────────────────────────────────

## TEST 7: Department Performance Overview

> Give me a complete overview of all departments. For each department, show:
> - Department name and location
> - How many employees work there
> - Total sales revenue generated by employees in that department
> - Revenue per employee
> Make sure to include departments even if they haven't made any sales yet.

**Keywords:** department, sales, revenue, employee

────────────────────────────────────────────────────────────────────────────────

## TEST 8: Salary Classification

> Classify our employees into salary brackets. Anyone making $90,000 or more is 'Senior',
> anyone between $75,000 and $89,999 is 'Mid-level', and anyone below $75,000 is 'Junior'.
> Show me each employee's ID, name, salary, and their salary bracket.

**Keywords:** employee, salary, bracket

────────────────────────────────────────────────────────────────────────────────

## TEST 9: Product Category Performance

> Analyze our sales by product category. For each category, tell me:
> - How many sales we made
> - Total revenue
> - Average sale amount
> - Smallest and largest sale amounts
> Sort the results by total revenue, highest first.

**Keywords:** sales, category, revenue

────────────────────────────────────────────────────────────────────────────────

## TEST 10: Employee Order by Salary

> List all employees within each department, sorted by their salary from highest to lowest.
> For each employee, show their name, department, salary, and their position number within
> their department (1 for highest paid, 2 for second highest, etc.).

**Keywords:** employee, salary, department, rank

────────────────────────────────────────────────────────────────────────────────

## TEST 11: Manager's Team Overview

> Show me all employees and their direct manager's name. Include employees who don't have
> a manager. Sort by manager name, then employee name.

**Keywords:** employee, manager

────────────────────────────────────────────────────────────────────────────────

## TEST 12: Recent Project Assignments

> Find all project assignments that happened in the last 3 years. For each assignment,
> show the project name, employee name, when they were assigned, and their role.

**Keywords:** project, assignment, employee, role

────────────────────────────────────────────────────────────────────────────────

## TEST 13: Sales by Employee

> Show me sales performance for each employee who has made at least one sale.
> Tell me their name, total number of sales, and total revenue. Order by total revenue descending.

**Keywords:** sales, employee, revenue

────────────────────────────────────────────────────────────────────────────────

## TEST 14: Active vs Inactive Comparison

> Compare active and non-active employees. For each status group, show me:
> - How many employees
> - Average salary
> - Highest salary
> Only show status groups that have at least one employee.

**Keywords:** employee, status, salary

────────────────────────────────────────────────────────────────────────────────

## TEST 15: Department Budget Analysis

> Which departments have a budget greater than their total employee payroll?
> Show the department name, budget, total payroll, and the difference.
> Only show departments where budget exceeds payroll.

**Keywords:** department, budget, payroll

────────────────────────────────────────────────────────────────────────────────

## TEST 16: Sales with Employee Details

> I want to see all sales transactions along with the employee who made each sale.
> For each sale, show me the sale ID, employee ID, employee's first and last name,
> and the sale amount. Sort by sale ID. Limit to first 10 results.

**Keywords:** sales, employee, amount

**Validate:** rows > 0

────────────────────────────────────────────────────────────────────────────────

## TEST 17: Department Employee Roster

> Give me a roster of all employees in the Engineering department.
> Show the department name and each employee's first and last name.
> Include the department even if it has no employees. Sort by employee last name.

**Keywords:** department, employee, engineering

────────────────────────────────────────────────────────────────────────────────

## TEST 18: Sales Performance by Department

> I need a report showing sales broken down by department.
> For each sale, show the sale ID, employee's name, their department name,
> and the sale amount. Sort by sale ID. Limit to first 10 results.

**Keywords:** sales, department, employee

────────────────────────────────────────────────────────────────────────────────

## TEST 19: Employee Project Workload

> Show me all employees and their current project assignments.
> For each assignment, display the employee's full name, project name,
> their role on the project, and hours allocated. Include only assignments
> from the last 3 years. Sort by employee last name.

**Keywords:** employee, project, assignment, hours

────────────────────────────────────────────────────────────────────────────────

## TEST 20: Cross-Department Sales Analysis

> Give me a detailed view of sales with full employee and department context.
> For each sale, show: sale ID, employee first and last name, department name,
> department location, sale amount, and product category. Sort by sale amount
> descending. Limit to top 5 highest sales.

**Keywords:** sales, employee, department, category

────────────────────────────────────────────────────────────────────────────────

## TEST 21: Dynamic Multi-Filter Search

Find employees matching these criteria:
- Department ID = 1
- Salary >= 50000
- Sorted by last name
- Limit 50 results

**Keywords:** employee, department, salary, filter

────────────────────────────────────────────────────────────────────────────────

## TEST 22: Pagination with Custom Sorting

Show employees page 1 (first 5 rows), sorted by salary descending.

**Keywords:** employee, salary, pagination

────────────────────────────────────────────────────────────────────────────────

## TEST 23: Complex Boolean Filter

Find employees who are either:
- High earners in Department 1 (salary > 90000 AND department_id = 1)
OR
- Long-tenure employees (hired before 2020-04-01)

**Keywords:** employee, salary, department, hire

────────────────────────────────────────────────────────────────────────────────

## TEST 24: Bulk Insert

Insert 3 new employees from the following data:
- Employee 1: TestBulk1 User1, test1@company.com, hired 2024-04-01, salary 65000, dept 2, manager 3, born 1994-06-15, active
- Employee 2: TestBulk2 User2, test2@company.com, hired 2024-04-02, salary 68000, dept 3, manager 6, born 1993-08-20, active
- Employee 3: TestBulk3 User3, test3@company.com, hired 2024-04-03, salary 70000, dept 1, manager 2, born 1992-11-30, active

Do not specify employee_id (should auto-generate).

**Keywords:** insert, employee, bulk

────────────────────────────────────────────────────────────────────────────────

## TEST 25: Conditional Update

Update employee with ID 5 to have salary of 95000.00.

**Keywords:** update, employee, salary

────────────────────────────────────────────────────────────────────────────────

## TEST 26: Dynamic Grouping Dimensions

Sales report grouped by employee and product category, showing:
- Employee ID
- Product category
- Total sales (sum of amount as decimal)
- Number of sales (count)

Sorted by employee ID ascending.

**Keywords:** sales, employee, category, group

────────────────────────────────────────────────────────────────────────────────

## TEST 27: Multi-Level Relationship Traversal

Find all sales with employee information, showing:
- Sale ID
- Employee ID
- Employee first name
- Employee last name
- Sale amount

Join sales table with employees table, sorted by sale ID.

**Keywords:** sales, employee, join

────────────────────────────────────────────────────────────────────────────────

## TEST 28: Sales Transaction Details

I need to see detailed information about our sales transactions.
For each sale, show me the sale ID, employee ID, the employee's first and last name,
and the amount of the sale. Sort the results by sale ID and show me just the first 5.

**Keywords:** sales, employee, transaction

────────────────────────────────────────────────────────────────────────────────

## TEST 29: Engineering Department Team

Give me a list of everyone who works in the Engineering department (department ID 1).
For each person, show me the department name and the employee's first and last name.
Sort the list alphabetically by last name.

**Keywords:** department, employee, engineering

────────────────────────────────────────────────────────────────────────────────

## TEST 30: Sales with Full Context

I want a comprehensive view of our sales. For each sale, show me:
- The sale ID
- The salesperson's first and last name
- Which department they work in
- The sale amount

Sort by sale ID and show me the first 5 transactions.

**Keywords:** sales, employee, department

────────────────────────────────────────────────────────────────────────────────

## TEST 31: High-Value Sales Report

Show me all sales over $20,000 with complete details. For each qualifying sale:
- Sale ID
- Salesperson's full name (first and last)
- Their department name
- The sale amount

Sort by sale amount, highest first.

**Keywords:** sales, employee, department, amount

────────────────────────────────────────────────────────────────────────────────

## TEST 32: Recent Project Team Assignments

I need to see who's been assigned to projects in the last 3 years.
For each assignment, show me:
- The project name
- The employee's full name (first and last)
- Their role on the project
- How many hours they're allocated

Sort alphabetically by employee last name and limit to 10 results.

**Keywords:** project, employee, assignment, role
