#!/usr/bin/env python3
"""Simple test to verify Zen database connection via ODBC"""
import os
import pyodbc

DSN = os.environ.get("ZEN_DSN", "DEMODATA")
conn_string = f"DSN={DSN}"
print(f"Testing connection with: {conn_string}")
print("-" * 60)

try:
    print("Connecting to database...")
    connection = pyodbc.connect(conn_string)
    print("[OK] Connection successful!")

    print("\nQuerying X$File system table...")
    with connection.cursor() as cur:
        cur.execute("""
            SELECT
                Xf$Name AS table_name,
                Xf$Id AS file_id,
                Xf$Flags AS flags
            FROM X$File
            ORDER BY Xf$Name
        """)

        rows = cur.fetchall()
        all_tables = rows
        if rows:
            print(f"[OK] Query successful! Found {len(rows)} tables (showing first 10):")
            for row in rows[:10]:
                print(f"  - {row.table_name} (ID: {row.file_id}, Flags: {row.flags})")
        else:
            print("  No tables found")

    print("\nQuerying schema (excluding X$ tables by name)...")
    with connection.cursor() as cur:
        cur.execute("""
            SELECT
                F.Xf$Name AS table_name,
                E.Xe$Name AS column_name,
                E.Xe$DataType AS data_type_code
            FROM X$File F
            INNER JOIN X$Field E ON F.Xf$Id = E.Xe$File
            WHERE F.Xf$Name NOT LIKE 'X$%'
            ORDER BY F.Xf$Name, E.Xe$Id
        """)

        filtered_rows = cur.fetchall()
        filtered_tables = set()
        for row in filtered_rows:
            filtered_tables.add(row.table_name.strip())

        print(f"[OK] Filtered query successful!")
        print(f"  User tables only: {len(filtered_tables)}")
        print(f"  Total columns: {len(filtered_rows)}")
        print(f"  System tables excluded: {len(all_tables) - len(filtered_tables)}")

    connection.close()
    print("\n[OK] Test completed successfully!")

except pyodbc.Error as e:
    print(f"\n[FAIL] Connection failed!")
    print(f"Error: {e}")
    print(f"\nPossible issues:")
    print("  1. Actian Zen is not installed")
    print("  2. Zen server is not running")
    print("  3. DEMODATA database does not exist")
    print("  4. ODBC driver 'Pervasive ODBC Interface' is not installed")
    print("  5. Connection string parameters are incorrect")
except Exception as e:
    print(f"\n[FAIL] Unexpected error!")
    print(f"Error: {type(e).__name__}: {e}")
