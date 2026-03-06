#!/usr/bin/env python3
"""
Regression Test Suite for actian-zen
Runs 20 SQL tests directly using actian_zen_adapter
"""

import sys
import os
import json
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))
from actian_zen_adapter import execute_raw_sql, get_zen_schema

# 20 Natural Language SQL Tests (from run_complete_test_suite.py)
REGRESSION_TESTS = [
    {
        "id": 1,
        "name": "Long-Tenure Employees",
        "description": "Show employees working >2 years with ID, name, hire date",
        "sql": """
            SELECT employee_id, first_name, last_name, hire_date
            FROM employees
            WHERE hire_date < '2024-02-03'
            ORDER BY hire_date
        """
    },
    {
        "id": 2,
        "name": "Monthly Sales Summary",
        "description": "2023 sales by month with count and revenue",
        "sql": """
            SELECT YEAR(sale_date) AS year,
                   MONTH(sale_date) AS month,
                   COUNT(*) AS sales_count,
                   SUM(amount) AS total_revenue
            FROM sales
            WHERE YEAR(sale_date) = 2023
            GROUP BY YEAR(sale_date), MONTH(sale_date)
            ORDER BY year, month
        """
    },
    {
        "id": 3,
        "name": "Employee Contact List",
        "description": "Full name uppercase, email, email length for employees with email",
        "sql": """
            SELECT UPPER(first_name + ' ' + last_name) AS full_name,
                   email,
                   LENGTH(email) AS email_length
            FROM employees
            WHERE email IS NOT NULL
            ORDER BY last_name, first_name
        """
    },
    {
        "id": 4,
        "name": "Above-Average Earners",
        "description": "Employees earning more than department average",
        "sql": """
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
        """
    },
    {
        "id": 5,
        "name": "Salary Peer Analysis",
        "description": "Same department employees with salaries within $5000",
        "sql": """
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
        """
    },
    {
        "id": 6,
        "name": "Department Size Filter",
        "description": "Departments with >2 employees showing count, avg salary, total payroll",
        "sql": """
            SELECT d.department_name,
                   COUNT(e.employee_id) AS employee_count,
                   AVG(e.salary) AS avg_salary,
                   SUM(e.salary) AS total_payroll
            FROM departments d
            LEFT JOIN employees e ON d.department_id = e.department_id
            GROUP BY d.department_name
            HAVING COUNT(e.employee_id) > 2
            ORDER BY employee_count DESC
        """
    },
    {
        "id": 7,
        "name": "Department Performance Overview",
        "description": "All departments with employees, sales revenue, revenue per employee",
        "sql": """
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
        """
    },
    {
        "id": 8,
        "name": "Salary Classification",
        "description": "Classify employees into Senior/Mid-level/Junior brackets",
        "sql": """
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
        """
    },
    {
        "id": 9,
        "name": "Product Sales Performance",
        "description": "Sales by product with count, revenue, avg, min, max",
        "sql": """
            SELECT product_name,
                   COUNT(*) AS sales_count,
                   SUM(amount) AS total_revenue,
                   AVG(amount) AS avg_sale,
                   MIN(amount) AS min_sale,
                   MAX(amount) AS max_sale
            FROM sales
            GROUP BY product_name
            ORDER BY total_revenue DESC
        """
    },
    {
        "id": 10,
        "name": "Employee Order by Salary (ROW_NUMBER workaround)",
        "description": "Employees within dept sorted by salary with ranking using correlated subquery",
        "sql": """
            SELECT e1.first_name + ' ' + e1.last_name AS name,
                   d.department_name,
                   e1.salary,
                   (SELECT COUNT(*) + 1 FROM employees e2
                    WHERE e2.department_id = e1.department_id
                    AND e2.salary > e1.salary) AS dept_rank
            FROM employees e1
            JOIN departments d ON e1.department_id = d.department_id
            ORDER BY d.department_name, dept_rank
        """
    },
    {
        "id": 11,
        "name": "Manager's Team Overview",
        "description": "All employees with their manager's name",
        "sql": """
            SELECT e.employee_id,
                   e.first_name + ' ' + e.last_name AS employee_name,
                   m.first_name + ' ' + m.last_name AS manager_name
            FROM employees e
            LEFT JOIN employees m ON e.manager_id = m.employee_id
            ORDER BY manager_name, employee_name
        """
    },
    {
        "id": 12,
        "name": "Recent Hires",
        "description": "Employees hired in last 3 years",
        "sql": """
            SELECT employee_id,
                   first_name + ' ' + last_name AS employee_name,
                   hire_date,
                   department_id
            FROM employees
            WHERE hire_date >= '2023-02-03'
            ORDER BY hire_date DESC
        """
    },
    {
        "id": 13,
        "name": "Sales by Employee",
        "description": "Sales performance per employee with count and revenue",
        "sql": """
            SELECT e.first_name + ' ' + e.last_name AS employee_name,
                   COUNT(s.sale_id) AS sales_count,
                   SUM(s.amount) AS total_revenue
            FROM employees e
            JOIN sales s ON e.employee_id = s.employee_id
            GROUP BY e.first_name, e.last_name
            ORDER BY total_revenue DESC
        """
    },
    {
        "id": 14,
        "name": "Active vs Inactive Comparison",
        "description": "Compare employee groups by status",
        "sql": """
            SELECT status,
                   COUNT(*) AS employee_count,
                   AVG(salary) AS avg_salary,
                   MAX(salary) AS highest_salary
            FROM employees
            GROUP BY status
            HAVING COUNT(*) > 0
            ORDER BY status
        """
    },
    {
        "id": 15,
        "name": "Department Budget Analysis",
        "description": "Departments where budget > payroll",
        "sql": """
            SELECT d.department_name,
                   d.budget,
                   SUM(e.salary) AS total_payroll,
                   d.budget - SUM(e.salary) AS budget_surplus
            FROM departments d
            LEFT JOIN employees e ON d.department_id = e.department_id
            GROUP BY d.department_name, d.budget
            HAVING d.budget > SUM(e.salary)
            ORDER BY budget_surplus DESC
        """
    },
    {
        "id": 16,
        "name": "Sales with Employee Details",
        "description": "Sales with employee info, first 10",
        "sql": """
            SELECT TOP 10 s.sale_id,
                   e.employee_id,
                   e.first_name,
                   e.last_name,
                   s.amount
            FROM sales s
            JOIN employees e ON s.employee_id = e.employee_id
            ORDER BY s.sale_id
        """
    },
    {
        "id": 17,
        "name": "Department Employee Roster",
        "description": "Engineering dept roster with dept name and employees",
        "sql": """
            SELECT d.department_name,
                   e.first_name,
                   e.last_name
            FROM departments d
            LEFT JOIN employees e ON d.department_id = e.department_id
            WHERE d.department_name = 'Engineering'
            ORDER BY e.last_name
        """
    },
    {
        "id": 18,
        "name": "Sales Performance by Department",
        "description": "Sales with employee and department, first 10",
        "sql": """
            SELECT TOP 10 s.sale_id,
                   e.first_name + ' ' + e.last_name AS employee_name,
                   d.department_name,
                   s.amount
            FROM sales s
            JOIN employees e ON s.employee_id = e.employee_id
            JOIN departments d ON e.department_id = d.department_id
            ORDER BY s.sale_id
        """
    },
    {
        "id": 19,
        "name": "Employee Salary Distribution",
        "description": "Count employees in each salary range",
        "sql": """
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
        """
    },
    {
        "id": 20,
        "name": "Cross-Department Sales Analysis",
        "description": "Sales with full context, top 5 by amount",
        "sql": """
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
        """
    }
]


def run_test(test):
    """Run a single test and return result"""
    sql = test['sql'].strip()
    result = execute_raw_sql(sql)

    if "error" in result:
        return {
            "id": test["id"],
            "name": test["name"],
            "success": False,
            "error": result["error"],
            "row_count": 0
        }

    return {
        "id": test["id"],
        "name": test["name"],
        "success": True,
        "row_count": result.get("row_count", 0),
        "sample": result.get("results", [])[:2]  # First 2 rows only
    }


def main():
    print("=" * 70)
    print("ACTIAN-ZEN REGRESSION TEST SUITE")
    print(f"Time: {datetime.now().isoformat()}")
    print("=" * 70)

    # Check connection
    test_result = execute_raw_sql("SELECT 1 AS test")
    if "error" in test_result:
        print(f"[FAIL] Database connection failed: {test_result['error']}")
        return
    print("[OK] Database connected")

    # Check schema
    schema = get_zen_schema()
    tables = schema.get("tables", [])
    print(f"[OK] Found {len(tables)} tables")

    # Required tables
    required = ["employees", "departments", "sales"]
    missing = [t for t in required if t not in tables]
    if missing:
        print(f"[WARN] Missing tables: {missing}")
        print("       Run setup_test_data.py first")

    print("\n" + "-" * 70)
    print("RUNNING 20 REGRESSION TESTS")
    print("-" * 70)

    results = []
    passed = 0
    failed = 0

    for test in REGRESSION_TESTS:
        print(f"\n[Test {test['id']:2d}/20] {test['name']}")
        print(f"         {test['description']}")

        result = run_test(test)
        results.append(result)

        if result["success"]:
            passed += 1
            print(f"         [OK] {result['row_count']} rows")
        else:
            failed += 1
            error_msg = result['error'][:60] if len(result['error']) > 60 else result['error']
            print(f"         [FAIL] {error_msg}")

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"  Total:  {len(REGRESSION_TESTS)}")
    print(f"  Passed: {passed}")
    print(f"  Failed: {failed}")
    print(f"  Rate:   {passed}/{len(REGRESSION_TESTS)} ({100*passed/len(REGRESSION_TESTS):.1f}%)")

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"results/regression_test_{timestamp}.json"
    os.makedirs("results", exist_ok=True)

    with open(results_file, 'w') as f:
        json.dump({
            "timestamp": timestamp,
            "total": len(REGRESSION_TESTS),
            "passed": passed,
            "failed": failed,
            "rate": f"{100*passed/len(REGRESSION_TESTS):.1f}%",
            "results": results
        }, f, indent=2, default=str)

    print(f"\n[OK] Results saved to {results_file}")

    # List failed tests
    if failed > 0:
        print("\n" + "-" * 70)
        print("FAILED TESTS:")
        print("-" * 70)
        for r in results:
            if not r["success"]:
                print(f"  Test {r['id']}: {r['name']}")
                print(f"    Error: {r['error'][:80]}")


if __name__ == "__main__":
    main()
