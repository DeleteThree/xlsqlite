# xlsqlite Project Plan

## Executive Summary

**Project Name:** xlsqlite
**Version:** 1.0.0
**License:** BSD 3-Clause
**Purpose:** Create a standalone, easy-to-install Python package that provides a powerful `=SQLITE()` custom function in Microsoft Excel

---

## 1. Project Purpose & Intended Use

### 1.1 Purpose

xlsqlite is a **standalone Excel add-in** that enables users to execute SQL queries directly against Excel data using SQLite syntax. It provides a professional-grade alternative to Excel's built-in lookup functions (VLOOKUP, INDEX/MATCH) and enables advanced data analysis using SQL.

### 1.2 Target Users

**Primary:**
- SQL-savvy Excel users (DBAs, data analysts, business analysts)
- Users who need complex data transformations in Excel
- Teams that work with large Excel datasets

**Not for:**
- Users without SQL knowledge (they should use Excel formulas)
- Users who need real-time database connections (use Power Query)
- Users who need persistent databases (this is in-memory only)

### 1.3 Key Use Cases

1. **Complex JOINs** - Join data across multiple sheets/tables
2. **Window Functions** - Running totals, rankings, moving averages
3. **Aggregations** - GROUP BY with HAVING clauses
4. **CTEs** - Multi-step analytical queries
5. **Data Cleaning** - CASE statements, string manipulation
6. **Reporting** - Dynamic SQL-based reports

### 1.4 Value Proposition

**vs. Excel Formulas:**
- More powerful (JOINs, window functions, CTEs)
- Easier to read and maintain
- Better performance on large datasets

**vs. xlwings SQL:**
- More robust parser (handles Sheet.Table, cross-sheet references)
- Better type inference (INTEGER/REAL/TEXT detection)
- Comprehensive error messages
- Full SQLite feature set
- 336 automated tests

**vs. Power Query:**
- Simpler for SQL users (no M language learning curve)
- Dynamic (recalculates with data changes)
- Lighter weight (no external connections)

---

## 2. Technical Architecture

### 2.1 High-Level Design

```
┌─────────────────────────────────────────────────────────────┐
│                    Excel Spreadsheet                         │
│  User types: =SQLITE("SELECT * FROM Sheet1!A1:D10")        │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                 VBA Wrapper (xlsqlite.xlam)                 │
│  - Intercepts function call                                 │
│  - Calls Python via COM                                     │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              Python COM Server (xlsqlite/server.py)         │
│  - Receives call from Excel                                 │
│  - Keeps Python process alive                               │
│  - Marshals data between Excel and Python                   │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              SQLITE Function (our implementation)            │
│  1. Parser    - Extract table references from SQL           │
│  2. Schema    - Read Excel ranges, infer types              │
│  3. Executor  - Run query in SQLite in-memory DB           │
│  4. Output    - Format results for Excel                    │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    Excel Spreadsheet                         │
│  Results spill into cells as array formula                  │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Component Breakdown

**Component 1: Infrastructure (from xlwings)**
- Purpose: Provide COM server, UDF registration, Excel communication
- Files: `server.py`, `udfs.py`, `main.py`, `_xlwindows.py`, DLLs
- Responsibility: Handle all Excel ↔ Python communication

**Component 2: SQL Engine (our code)**
- Purpose: Parse SQL, execute queries, format results
- Files: `parser.py`, `schema.py`, `executor.py`, `errors.py`, `output.py`
- Responsibility: All SQL processing logic

**Component 3: Excel Add-in (VBA)**
- Purpose: Register UDF with Excel, provide UI
- Files: `xlsqlite.xlam`, `xlsqlite.bas`
- Responsibility: Excel integration point

**Component 4: Installer**
- Purpose: Easy installation for end users
- Files: `setup.py`, `__init__.py`, `addin.py`
- Responsibility: PyPI packaging and add-in registration

### 2.3 Data Flow

**Query Execution Flow:**

1. User enters `=SQLITE("SELECT * FROM Orders WHERE Total > 100")`
2. Excel calls VBA function `SQLITE(query)`
3. VBA calls Python COM server via `Py.CallUDF()`
4. Python COM server routes to `SQLITE()` function
5. **Parser** extracts table reference: `Orders`
6. **Schema** reads Excel range, infers column types
7. **Schema** creates SQLite table in memory, loads data
8. **Executor** runs SQL query against in-memory database
9. **Output** formats results as 2D array
10. Python returns array to VBA
11. VBA returns to Excel
12. Excel displays results as spilling array

**Error Flow:**

1. Any component raises exception
2. **Errors** module normalizes to SQLite-style message
3. Error string returned to Excel
4. Excel displays error in cell (e.g., "Error: no such table: Orders")

---

## 3. Legal & Licensing Requirements

### 3.1 License

**Type:** BSD 3-Clause License (same as xlwings)

**Requirements:**
1. Include original xlwings copyright notice
2. Include BSD license text in all distributions
3. Credit xlwings in README and documentation
4. Do NOT use "xlwings" name to endorse/promote xlsqlite

### 3.2 Copyright Notices

**All files derived from xlwings must include:**

```python
# Original xlwings code Copyright (c) 2014-present, Zoomer Analytics LLC.
# All rights reserved.
# xlsqlite modifications Copyright (c) 2025-present, [Your Name/Organization]
# Licensed under the BSD 3-Clause License (see LICENSE.txt)
```

**Our new files should include:**

```python
# Copyright (c) 2025-present, [Your Name/Organization]
# Part of xlsqlite project
# Licensed under the BSD 3-Clause License (see LICENSE.txt)
```

### 3.3 Attribution

**README.md must include:**

```markdown
## Acknowledgments

xlsqlite is built upon the infrastructure of [xlwings](https://github.com/xlwings/xlwings),
an excellent Python library for Excel integration created by Zoomer Analytics LLC.

The COM server, UDF registration system, and Excel communication layer are derived from
xlwings and are used under the BSD 3-Clause License.

The SQL parsing, execution, and data handling components are original work developed
specifically for xlsqlite.
```

---

## 4. Implementation Plan

### 4.1 Phase 1: Project Setup & Fork Preparation

**Duration:** 2-3 hours

**Tasks:**

1. **Create Project Structure**
   ```
   xlsqllite/
   ├── LICENSE.txt
   ├── README.md
   ├── PLAN.md (this file)
   ├── setup.py
   ├── MANIFEST.in
   ├── .gitignore
   ├── requirements.txt
   ├── xlsqlite/
   │   ├── __init__.py
   │   └── (to be populated)
   ├── tests/
   │   └── (copy from C:\Claudish\SQLiteExcel\)
   └── docs/
       ├── USAGE.md
       └── API.md
   ```

2. **Clone Essential xlwings Files**

   From xlwings repository (https://github.com/xlwings/xlwings), extract:

   **Core Infrastructure (REQUIRED):**
   - `xlwings/server.py` → `xlsqlite/server.py`
   - `xlwings/udfs.py` → `xlsqlite/udfs.py`
   - `xlwings/main.py` → `xlsqlite/main.py` (heavily modified)
   - `xlwings/_xlwindows.py` → `xlsqlite/_xlwindows.py`
   - `xlwings/_xlmac.py` → `xlsqlite/_xlmac.py` (Mac support)
   - `xlwings/conversion/` → `xlsqlite/conversion/` (type converters)
   - `xlwings/utils.py` → `xlsqlite/utils.py`

   **Add-in Files (REQUIRED):**
   - `xlwings/addin/xlwings.xlam` → `xlsqlite/addin/xlsqlite.xlam`
   - `xlwings/addin/xlwings.bas` → `xlsqlite/addin/xlsqlite.bas`

   **DLL Files (REQUIRED for Windows):**
   - `xlwings/xlwings32-<version>.dll` → `xlsqlite/xlsqlite32-1.0.0.dll`
   - `xlwings/xlwings64-<version>.dll` → `xlsqlite/xlsqlite64-1.0.0.dll`

   **DO NOT COPY (not needed):**
   - `xlwings/rest/` - REST API server
   - `xlwings/pro/` - PRO features
   - `xlwings/ext/` - Extensions (we'll create our own)
   - `xlwings/_xloffice.py` - Office.js support
   - `xlwings/quickstart.py` - Project templates
   - Documentation, tests, examples folders

3. **Create LICENSE.txt**

   Copy BSD 3-Clause license text, include both xlwings and xlsqlite copyrights.

4. **Create .gitignore**
   ```
   __pycache__/
   *.py[cod]
   *$py.class
   *.so
   .Python
   build/
   develop-eggs/
   dist/
   downloads/
   eggs/
   .eggs/
   lib/
   lib64/
   parts/
   sdist/
   var/
   wheels/
   *.egg-info/
   .installed.cfg
   *.egg
   .pytest_cache/
   .coverage
   htmlcov/
   .vscode/
   .idea/
   *.xlsm
   ~$*.xl*
   ```

**Deliverable:** Clean project structure with xlwings infrastructure files copied and ready for modification.

---

### 4.2 Phase 2: Rename & Rebrand

**Duration:** 2-3 hours

**Tasks:**

1. **Global Rename: xlwings → xlsqlite**

   In ALL copied files, replace:
   - Package name: `xlwings` → `xlsqlite`
   - Import statements: `import xlwings` → `import xlsqlite`
   - Module references: `xlwings.` → `xlsqlite.`
   - DLL names: `xlwings32.dll` → `xlsqlite32.dll`
   - VBA module names: `xlwings` → `xlsqlite`
   - Add-in names: `xlwings.xlam` → `xlsqlite.xlam`
   - Registry keys: `xlwings` → `xlsqlite`
   - GUID generation: Create new GUIDs (don't reuse xlwings GUIDs)

2. **Update VBA Code**

   In `xlsqlite.xlam` and `xlsqlite.bas`:
   - Rename all `xlwings*` functions to `xlsqlite*`
   - Update DLL paths to point to `xlsqlite32.dll` / `xlsqlite64.dll`
   - Update Python server GUID (generate new one)
   - Update add-in title and description

3. **Update Python Server**

   In `server.py`:
   - Generate new COM CLSID (using `pythoncom.CreateGuid()`)
   - Update registration: `xlwings` → `xlsqlite`
   - Update server name in logs

4. **Update DLL References**

   Rename physical DLL files and update all references in code.

**Validation:**
- Search entire codebase for "xlwings" - should only appear in:
  - Comments (crediting original)
  - LICENSE.txt
  - README.md acknowledgments
- No functional code should reference "xlwings"

**Deliverable:** Fully rebranded xlsqlite infrastructure with no xlwings dependencies.

---

### 4.3 Phase 3: Strip Unnecessary Code

**Duration:** 1-2 hours

**Tasks:**

1. **Remove from main.py**

   Keep only:
   - `Book` class (minimal - for reading ranges)
   - `Sheet` class (minimal - for accessing ranges)
   - `Range` class (for reading/writing data)
   - Data conversion utilities

   Remove:
   - `App` class
   - Chart, Picture, Shape classes
   - Macro, Name classes
   - All REST API code
   - All Office.js code

2. **Remove Unused Modules**

   Delete these files entirely:
   - `rest/` folder
   - `pro/` folder (if accidentally copied)
   - `quickstart.py`
   - Any `_xloffice.py` references

3. **Simplify udfs.py**

   Keep only:
   - `@func` decorator
   - `@arg` decorator
   - `@ret` decorator
   - UDF registration logic
   - VBA wrapper generation

   Remove:
   - Advanced decorator features we don't need
   - Complexity we won't use

4. **Simplify server.py**

   Keep only:
   - COM server registration
   - UDF call routing
   - Basic error handling

   Remove:
   - REST API endpoints
   - Advanced server features

**Validation:**
- Package size should be ~20-30% of original xlwings
- Only essential Excel communication code remains
- All imports resolve correctly

**Deliverable:** Lean xlsqlite package with only essential infrastructure.

---

### 4.4 Phase 4: Integrate Our SQL Implementation

**Duration:** 3-4 hours

**Tasks:**

1. **Copy Our Modules**

   From `C:\Claudish\SQLiteExcel\`, copy to `xlsqlite/ext/sqlite/`:

   ```
   xlsqlite/ext/sqlite/
   ├── __init__.py        # Main SQLITE() function
   ├── parser.py          # SQL parser (existing)
   ├── schema.py          # Schema builder (needs modification)
   ├── executor.py        # Query executor (existing)
   ├── errors.py          # Error handlers (existing)
   └── output.py          # Output formatter (existing)
   ```

2. **Create Main SQLITE Function**

   In `xlsqlite/ext/sqlite/__init__.py`:

   ```python
   """
   xlsqlite SQL Extension

   Provides the SQLITE() user-defined function for Excel.
   """

   from xlsqlite import func, arg, ret
   import pandas as pd
   from typing import Any

   from .main import _execute_sqlite
   from .errors import SQLiteExcelError, format_error_for_excel


   @func
   @arg('query', doc='SQL query string')
   @arg('params', ndim=0, doc='Optional query parameters')
   @ret(expand='table')
   def SQLITE(query: str, *params: Any):
       """
       Execute SQL query against Excel data.

       Args:
           query: SQL query string (SQLite dialect)
           *params: Optional parameters for ? placeholders

       Returns:
           Results as 2D array (spills in Excel)

       Examples:
           =SQLITE("SELECT * FROM Sheet1!A1:D10")
           =SQLITE("SELECT * FROM Orders WHERE Total > 100")
           =SQLITE("SELECT * FROM Orders WHERE CustomerID = ?", A1)

       Supported:
           - JOINs (INNER, LEFT, RIGHT, CROSS)
           - Window functions (ROW_NUMBER, RANK, etc.)
           - CTEs (WITH clauses)
           - Aggregations (GROUP BY, HAVING)
           - Subqueries
           - All SQLite functions
       """
       try:
           result = _execute_sqlite(query, params)
           # Convert DataFrame to 2D list for Excel
           if isinstance(result, pd.DataFrame):
               # Include headers as first row
               return [list(result.columns)] + result.values.tolist()
           else:
               # Error or message
               return [[str(result)]]
       except SQLiteExcelError as e:
           return [[str(e)]]
       except Exception as e:
           return [[format_error_for_excel(e)]]
   ```

3. **Modify schema.py for xlsqlite**

   Replace `resolve_reference()` function to use xlsqlite instead of xl():

   ```python
   def resolve_reference(ref: TableReference) -> pd.DataFrame:
       """
       Resolve Excel reference using xlsqlite.

       This replaces the xl() function from Python in Excel.
       Uses xlsqlite's Range reading capabilities.
       """
       import xlsqlite as xls

       try:
           # Get the calling workbook
           wb = xls.Book.caller()
       except Exception:
           # Fallback: try to get active workbook
           wb = xls.books.active

       if wb is None:
           raise RangeResolutionError(
               ref.original,
               "Cannot access Excel workbook"
           )

       # Build Excel reference string
       if ref.is_named_table:
           # Named table reference
           if ref.sheet_name:
               # Sheet-qualified: Sheet1.Table1
               sheet = wb.sheets[ref.sheet_name]
               # Try to find named table
               try:
                   # Check if it's an Excel Table object
                   table = sheet.tables[ref.table_name]
                   range_obj = table.range
               except:
                   # Maybe it's just a named range
                   range_str = f"{ref.sheet_name}!{ref.table_name}"
                   range_obj = wb.names[range_str].refers_to_range
           else:
               # Simple table name
               try:
                   # Search all sheets for this table
                   for sheet in wb.sheets:
                       try:
                           table = sheet.tables[ref.table_name]
                           range_obj = table.range
                           break
                       except:
                           continue
                   else:
                       # Not found as table, try as named range
                       range_obj = wb.names[ref.table_name].refers_to_range
               except:
                   raise RangeResolutionError(
                       ref.original,
                       f"Table or named range '{ref.table_name}' not found"
                   )
       else:
           # Range reference
           if ref.sheet_name:
               # Cross-sheet: Sheet2!A1:B10
               sheet = wb.sheets[ref.sheet_name]
               range_obj = sheet.range(ref.range_ref)
           else:
               # Simple range on active sheet: A1:M100
               sheet = wb.sheets.active
               range_obj = sheet.range(ref.range_ref)

       # Read range as DataFrame with headers
       try:
           df = range_obj.options(pd.DataFrame, header=True).value
       except Exception as e:
           raise RangeResolutionError(
               ref.original,
               f"Failed to read range: {str(e)}"
           )

       # Validate
       if df is None:
           raise RangeResolutionError(
               ref.original,
               "Range returned no data"
           )

       if not isinstance(df, pd.DataFrame):
           raise RangeResolutionError(
               ref.original,
               f"Expected DataFrame, got {type(df).__name__}"
           )

       if len(df) == 0:
           raise EmptyRangeError(ref.original)

       if len(df.columns) == 0:
           raise RangeResolutionError(
               ref.original,
               "Range has no columns"
           )

       return df
   ```

4. **Create main.py Wrapper**

   In `xlsqlite/ext/sqlite/main.py`:

   Copy the `_execute_sqlite()` function from `C:\Claudish\SQLiteExcel\main.py`
   with minimal modifications (just import paths).

5. **Update Import Paths**

   In all our SQL modules (`parser.py`, `schema.py`, etc.):
   - Change relative imports to use `xlsqlite.ext.sqlite`
   - Ensure all cross-module imports work

**Validation:**
- All imports resolve
- No circular dependencies
- `from xlsqlite.ext.sqlite import SQLITE` works

**Deliverable:** Fully integrated SQLITE() function using our superior implementation.

---

### 4.5 Phase 5: Testing Infrastructure

**Duration:** 2-3 hours

**Tasks:**

1. **Copy Test Suite**

   From `C:\Claudish\SQLiteExcel\`, copy all test files to `xlsqlite/tests/`:
   ```
   tests/
   ├── __init__.py
   ├── conftest.py
   ├── test_parser_basic.py (18 tests)
   ├── test_parser_edge_cases.py (15 tests)
   ├── test_schema.py (65 tests)
   ├── test_executor.py (41 tests)
   ├── test_errors.py (71 tests)
   ├── test_output.py (51 tests)
   ├── test_integration.py (63 tests)
   └── test_xl_integration.py (12 tests - needs modification)
   ```

2. **Update Test Imports**

   In all test files, update imports:
   ```python
   # OLD:
   from parser import extract_table_references
   from schema import resolve_reference

   # NEW:
   from xlsqlite.ext.sqlite.parser import extract_table_references
   from xlsqlite.ext.sqlite.schema import resolve_reference
   ```

3. **Modify xl_integration Tests**

   Replace xl() mocking with xlsqlite mocking:
   ```python
   # Create mock xlsqlite environment
   class MockWorkbook:
       def __init__(self, data):
           self.data = data
           self.sheets = MockSheets(data)

   class MockRange:
       def __init__(self, df):
           self.df = df

       def options(self, target, header=True):
           return MockOptions(self.df)

   # ... etc
   ```

4. **Create Test Runner Script**

   `run_tests.py`:
   ```python
   #!/usr/bin/env python
   import sys
   import pytest

   if __name__ == '__main__':
       args = [
           'tests/',
           '-v',
           '--tb=short',
           '--cov=xlsqlite',
           '--cov-report=html',
           '--cov-report=term'
       ]
       sys.exit(pytest.main(args))
   ```

5. **Create CI/CD Configuration**

   `.github/workflows/tests.yml`:
   ```yaml
   name: Tests

   on: [push, pull_request]

   jobs:
     test:
       runs-on: ${{ matrix.os }}
       strategy:
         matrix:
           os: [windows-latest, macos-latest]
           python-version: [3.8, 3.9, '3.10', '3.11']

       steps:
       - uses: actions/checkout@v2
       - name: Set up Python
         uses: actions/setup-python@v2
         with:
           python-version: ${{ matrix.python-version }}
       - name: Install dependencies
         run: |
           pip install -e .
           pip install pytest pytest-cov
       - name: Run tests
         run: pytest tests/ -v
   ```

**Validation:**
- All 336 tests pass with new import paths
- Coverage report generates successfully
- No import errors

**Deliverable:** Complete test suite running against xlsqlite package.

---

### 4.6 Phase 6: Packaging & Distribution

**Duration:** 2-3 hours

**Tasks:**

1. **Create setup.py**

   ```python
   from setuptools import setup, find_packages
   import os

   # Read long description from README
   with open('README.md', 'r', encoding='utf-8') as f:
       long_description = f.read()

   # Read version from __init__.py
   version = {}
   with open('xlsqlite/__init__.py', 'r') as f:
       for line in f:
           if line.startswith('__version__'):
               exec(line, version)

   setup(
       name='xlsqlite',
       version=version['__version__'],
       description='SQL query engine for Microsoft Excel',
       long_description=long_description,
       long_description_content_type='text/markdown',
       author='[Your Name]',
       author_email='[your.email@example.com]',
       url='https://github.com/[yourusername]/xlsqlite',
       license='BSD 3-Clause',
       packages=find_packages(),
       include_package_data=True,
       install_requires=[
           'pandas>=1.0.0',
           'pywin32>=300; platform_system=="Windows"',
           'appscript>=1.1.0; platform_system=="Darwin"',
           'psutil>=2.0.0',
       ],
       extras_require={
           'dev': [
               'pytest>=6.0',
               'pytest-cov>=2.0',
               'black>=22.0',
               'flake8>=4.0',
           ],
       },
       python_requires='>=3.8',
       entry_points={
           'console_scripts': [
               'xlsqlite=xlsqlite.cli:main',
           ],
       },
       classifiers=[
           'Development Status :: 4 - Beta',
           'Intended Audience :: Developers',
           'Intended Audience :: Financial and Insurance Industry',
           'Intended Audience :: Science/Research',
           'License :: OSI Approved :: BSD License',
           'Operating System :: Microsoft :: Windows',
           'Operating System :: MacOS :: MacOS X',
           'Programming Language :: Python',
           'Programming Language :: Python :: 3',
           'Programming Language :: Python :: 3.8',
           'Programming Language :: Python :: 3.9',
           'Programming Language :: Python :: 3.10',
           'Programming Language :: Python :: 3.11',
           'Topic :: Office/Business :: Financial :: Spreadsheet',
           'Topic :: Database',
       ],
       keywords='excel sql sqlite pandas data-analysis',
   )
   ```

2. **Create MANIFEST.in**

   ```
   include LICENSE.txt
   include README.md
   include requirements.txt
   recursive-include xlsqlite/addin *.xlam *.bas
   recursive-include xlsqlite *.dll
   exclude tests/*
   exclude docs/*
   exclude examples/*
   ```

3. **Create requirements.txt**

   ```
   pandas>=1.0.0
   pywin32>=300; platform_system=="Windows"
   appscript>=1.1.0; platform_system=="Darwin"
   psutil>=2.0.0
   ```

4. **Create CLI Module**

   `xlsqlite/cli.py`:
   ```python
   """
   Command-line interface for xlsqlite.
   """
   import argparse
   import sys
   from .addin import install_addin, remove_addin

   def main():
       parser = argparse.ArgumentParser(
           description='xlsqlite - SQL for Excel'
       )
       subparsers = parser.add_subparsers(dest='command')

       # addin install
       install_parser = subparsers.add_parser(
           'addin',
           help='Manage Excel add-in'
       )
       install_parser.add_argument(
           'action',
           choices=['install', 'remove', 'status'],
           help='Add-in action'
       )

       args = parser.parse_args()

       if args.command == 'addin':
           if args.action == 'install':
               install_addin()
               print("✓ xlsqlite add-in installed successfully")
               print("  Open Excel and type =SQLITE(...) to use")
           elif args.action == 'remove':
               remove_addin()
               print("✓ xlsqlite add-in removed")
           elif args.action == 'status':
               # Check if installed
               from .addin import is_installed
               if is_installed():
                   print("✓ xlsqlite add-in is installed")
               else:
                   print("✗ xlsqlite add-in is not installed")
                   print("  Run: xlsqlite addin install")
       else:
           parser.print_help()

   if __name__ == '__main__':
       main()
   ```

5. **Create Add-in Installer**

   `xlsqlite/addin.py`:
   ```python
   """
   Excel add-in installation utilities.
   """
   import os
   import sys
   import shutil
   from pathlib import Path

   def get_addin_dir():
       """Get Excel add-in directory."""
       if sys.platform == 'win32':
           import winreg
           key = winreg.OpenKey(
               winreg.HKEY_CURRENT_USER,
               r'Software\Microsoft\Office\Excel\Addins'
           )
           # Return standard add-in path
           return Path(os.environ['APPDATA']) / 'Microsoft' / 'AddIns'
       elif sys.platform == 'darwin':
           # Mac
           return Path.home() / 'Library' / 'Application Support' / 'Microsoft' / 'Office' / 'User Content' / 'Addins'
       else:
           raise NotImplementedError('Unsupported platform')

   def install_addin():
       """Install xlsqlite Excel add-in."""
       # Get source and destination
       src_dir = Path(__file__).parent / 'addin'
       dst_dir = get_addin_dir()

       # Ensure destination exists
       dst_dir.mkdir(parents=True, exist_ok=True)

       # Copy .xlam file
       src_xlam = src_dir / 'xlsqlite.xlam'
       dst_xlam = dst_dir / 'xlsqlite.xlam'

       shutil.copy2(src_xlam, dst_xlam)

       # Register COM server
       if sys.platform == 'win32':
           import win32com.server.register
           # Register our COM server
           # (implementation depends on server.py structure)
           pass

   def remove_addin():
       """Remove xlsqlite Excel add-in."""
       dst_dir = get_addin_dir()
       dst_xlam = dst_dir / 'xlsqlite.xlam'

       if dst_xlam.exists():
           dst_xlam.unlink()

       # Unregister COM server
       if sys.platform == 'win32':
           # Unregister COM server
           pass

   def is_installed():
       """Check if add-in is installed."""
       dst_dir = get_addin_dir()
       dst_xlam = dst_dir / 'xlsqlite.xlam'
       return dst_xlam.exists()
   ```

6. **Update xlsqlite/__init__.py**

   ```python
   """
   xlsqlite - SQL Query Engine for Excel

   Built upon xlwings infrastructure.
   Original xlwings code Copyright (c) 2014-present, Zoomer Analytics LLC.
   xlsqlite modifications Copyright (c) 2025-present, [Your Name]

   Licensed under the BSD 3-Clause License.
   """

   __version__ = '1.0.0'

   # Import main classes for API
   from .main import Book, Sheet, Range
   from .udfs import func, arg, ret

   # Import SQLITE function
   from .ext.sqlite import SQLITE

   __all__ = [
       'Book',
       'Sheet',
       'Range',
       'func',
       'arg',
       'ret',
       'SQLITE',
       '__version__',
   ]
   ```

**Validation:**
- `python setup.py check` passes
- `pip install -e .` works locally
- All dependencies install correctly
- CLI command `xlsqlite` is available

**Deliverable:** Installable Python package ready for PyPI.

---

### 4.7 Phase 7: Documentation

**Duration:** 2-3 hours

**Tasks:**

1. **Create README.md**

   (See separate section below for full content)

   Key sections:
   - Project description
   - Installation instructions
   - Quick start examples
   - Features list
   - Acknowledgments to xlwings
   - License information

2. **Create USAGE.md**

   Copy and adapt `C:\Claudish\SQLiteExcel\EXCEL_USAGE.md`
   Update for xlsqlite specifics (no "Python in Excel" references)

3. **Create API.md**

   Document the SQLITE() function signature:
   - Parameters
   - Return values
   - Examples
   - Error handling

4. **Create CONTRIBUTING.md**

   Guidelines for:
   - Reporting bugs
   - Submitting pull requests
   - Code style
   - Running tests

5. **Create CHANGELOG.md**

   ```markdown
   # Changelog

   ## [1.0.0] - 2025-01-XX

   ### Added
   - Initial release of xlsqlite
   - SQLITE() user-defined function for Excel
   - Support for all SQLite SQL features
   - Comprehensive error handling
   - 336 automated tests

   ### Acknowledgments
   - Built upon xlwings infrastructure by Zoomer Analytics LLC
   ```

**Deliverable:** Complete documentation suite.

---

### 4.8 Phase 8: End-to-End Testing

**Duration:** 3-4 hours

**Tasks:**

1. **Unit Tests**

   Run full test suite:
   ```bash
   pytest tests/ -v --cov=xlsqlite --cov-report=html
   ```

   Success criteria:
   - All 336+ tests pass
   - Code coverage > 80%
   - No import errors

2. **Installation Test**

   Test on clean environment:
   ```bash
   # Create virtual environment
   python -m venv test_env
   source test_env/bin/activate  # or test_env\Scripts\activate on Windows

   # Install from source
   pip install -e .

   # Verify CLI
   xlsqlite addin install
   ```

3. **Excel Integration Test**

   **Test Workbook:** Create `test_workbook.xlsx`

   **Sheet1: Orders**
   | OrderID | CustomerID | Total | Date |
   |---------|------------|-------|------|
   | 1 | 101 | 150.50 | 2024-01-15 |
   | 2 | 102 | 200.00 | 2024-01-16 |
   | 3 | 101 | 75.25 | 2024-01-17 |

   **Sheet2: Customers**
   | CustomerID | Name | City |
   |------------|------|------|
   | 101 | Alice | NYC |
   | 102 | Bob | LA |

   **Test Cases:**

   1. Basic SELECT:
      ```
      =SQLITE("SELECT * FROM Sheet1!A1:D4")
      ```
      Expected: 3 rows with all data

   2. WHERE clause:
      ```
      =SQLITE("SELECT * FROM Sheet1!A1:D4 WHERE Total > 100")
      ```
      Expected: 2 rows (orders 1 and 2)

   3. JOIN:
      ```
      =SQLITE("SELECT o.OrderID, c.Name, o.Total FROM Sheet1!A1:D4 o JOIN Sheet2!A1:C3 c ON o.CustomerID = c.CustomerID")
      ```
      Expected: 3 rows with customer names

   4. Aggregation:
      ```
      =SQLITE("SELECT CustomerID, SUM(Total) as TotalSpent FROM Sheet1!A1:D4 GROUP BY CustomerID")
      ```
      Expected: 2 rows with totals per customer

   5. Window function:
      ```
      =SQLITE("SELECT *, ROW_NUMBER() OVER (ORDER BY Total DESC) as Rank FROM Sheet1!A1:D4")
      ```
      Expected: 3 rows with ranking

   6. Error handling:
      ```
      =SQLITE("SELECT * FROM NonExistent")
      ```
      Expected: "Error: no such table: NonExistent"

   7. Parameterized query (if cell B10 = 101):
      ```
      =SQLITE("SELECT * FROM Sheet1!A1:D4 WHERE CustomerID = ?", B10)
      ```
      Expected: 2 rows for customer 101

4. **Performance Test**

   Create large dataset (10,000 rows) and test:
   - Query execution time < 5 seconds
   - Memory usage reasonable
   - No crashes or hangs

5. **Cross-Platform Test**

   Test on:
   - Windows 10/11 with Excel 2016/2019/365
   - macOS with Excel 2019/365 (if possible)

**Validation:**
- All test cases pass
- No errors in Excel
- Results spill correctly
- Error messages display properly
- Performance acceptable

**Deliverable:** Verified, working xlsqlite add-in.

---

## 5. File Structure (Final)

```
xlsqllite/
├── LICENSE.txt                      # BSD 3-Clause
├── README.md                        # Main documentation
├── PLAN.md                          # This file
├── CHANGELOG.md                     # Version history
├── CONTRIBUTING.md                  # Contribution guidelines
├── MANIFEST.in                      # Package manifest
├── setup.py                         # Installation script
├── requirements.txt                 # Dependencies
├── .gitignore                       # Git ignore rules
├── .github/
│   └── workflows/
│       └── tests.yml                # CI/CD
├── xlsqlite/
│   ├── __init__.py                  # Package init (exports SQLITE)
│   ├── server.py                    # COM server (from xlwings)
│   ├── udfs.py                      # UDF decorators (from xlwings)
│   ├── main.py                      # Excel integration (from xlwings, stripped)
│   ├── _xlwindows.py                # Windows COM (from xlwings)
│   ├── _xlmac.py                    # Mac support (from xlwings)
│   ├── utils.py                     # Utilities (from xlwings)
│   ├── cli.py                       # Command-line interface
│   ├── addin.py                     # Add-in installer
│   ├── conversion/                  # Type converters (from xlwings)
│   │   ├── __init__.py
│   │   ├── framework.py
│   │   └── standard.py
│   ├── addin/                       # Excel add-in files
│   │   ├── xlsqlite.xlam            # Excel add-in (VBA)
│   │   └── xlsqlite.bas             # VBA module
│   ├── dlls/                        # COM DLLs
│   │   ├── xlsqlite32-1.0.0.dll     # 32-bit Windows
│   │   └── xlsqlite64-1.0.0.dll     # 64-bit Windows
│   └── ext/
│       └── sqlite/                  # Our SQL implementation
│           ├── __init__.py          # SQLITE() function
│           ├── main.py              # Main execution wrapper
│           ├── parser.py            # SQL parser (our code)
│           ├── schema.py            # Schema builder (our code, modified)
│           ├── executor.py          # Query executor (our code)
│           ├── errors.py            # Error handling (our code)
│           └── output.py            # Output formatter (our code)
├── tests/                           # All our tests (336+)
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_parser_basic.py
│   ├── test_parser_edge_cases.py
│   ├── test_schema.py
│   ├── test_executor.py
│   ├── test_errors.py
│   ├── test_output.py
│   ├── test_integration.py
│   └── test_excel_integration.py    # New: test with real Excel
├── docs/
│   ├── USAGE.md                     # User guide
│   ├── API.md                       # API reference
│   └── EXAMPLES.md                  # Example queries
└── examples/
    ├── basic_queries.xlsx           # Example workbook
    └── advanced_queries.xlsx        # Advanced examples
```

---

## 6. README.md Content

```markdown
# xlsqlite

**SQL Query Engine for Microsoft Excel**

Execute powerful SQL queries directly in Excel using the `=SQLITE()` custom function.

[![Tests](https://github.com/[user]/xlsqlite/workflows/Tests/badge.svg)](https://github.com/[user]/xlsqlite/actions)
[![PyPI version](https://badge.fury.io/py/xlsqlite.svg)](https://badge.fury.io/py/xlsqlite)
[![License](https://img.shields.io/badge/License-BSD%203--Clause-blue.svg)](LICENSE.txt)

---

## Features

✅ **Full SQLite Support** - All SQL features: JOINs, CTEs, window functions, subqueries
✅ **Easy Installation** - `pip install xlsqlite` + one command
✅ **Smart Type Inference** - Automatic INTEGER/REAL/TEXT detection
✅ **Comprehensive Errors** - SQLite-style error messages
✅ **Well Tested** - 336 automated tests
✅ **Cross-Platform** - Windows and macOS

---

## Installation

```bash
# Install package
pip install xlsqlite

# Install Excel add-in
xlsqlite addin install
```

That's it! Open Excel and start using `=SQLITE()`.

---

## Quick Start

### Basic Query

```excel
=SQLITE("SELECT * FROM Sheet1!A1:D10")
```

### JOIN Across Sheets

```excel
=SQLITE("
    SELECT o.OrderID, c.Name, o.Total
    FROM Sheet1!A1:D100 o
    JOIN Sheet2!A1:C50 c ON o.CustomerID = c.CustomerID
    WHERE o.Total > 1000
")
```

### Window Functions

```excel
=SQLITE("
    SELECT *,
           ROW_NUMBER() OVER (PARTITION BY Category ORDER BY Sales DESC) as Rank
    FROM Sheet1!A1:E1000
")
```

### Parameterized Queries

```excel
=SQLITE("SELECT * FROM Orders WHERE CustomerID = ?", A1)
```

---

## Supported SQL Features

- ✅ SELECT, INSERT, UPDATE, DELETE
- ✅ JOINs (INNER, LEFT, RIGHT, CROSS)
- ✅ Window Functions (ROW_NUMBER, RANK, LAG, LEAD, etc.)
- ✅ CTEs (WITH clauses, including recursive)
- ✅ Subqueries (correlated and uncorrelated)
- ✅ Aggregations (GROUP BY, HAVING)
- ✅ All SQLite built-in functions
- ✅ Parameterized queries with `?` placeholders

---

## Documentation

- [User Guide](docs/USAGE.md) - Complete usage documentation
- [API Reference](docs/API.md) - Function signatures and parameters
- [Examples](docs/EXAMPLES.md) - Real-world query examples
- [FAQ](docs/FAQ.md) - Common questions

---

## Examples

See the `examples/` folder for Excel workbooks with:
- Basic queries
- Advanced JOINs
- Window functions
- Data analysis patterns

---

## Requirements

- Python 3.8+
- Microsoft Excel 2016 or later (Windows/Mac)
- pandas >= 1.0.0

---

## Development

```bash
# Clone repository
git clone https://github.com/[user]/xlsqlite.git
cd xlsqlite

# Install in development mode
pip install -e .[dev]

# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=xlsqlite --cov-report=html
```

---

## Acknowledgments

xlsqlite is built upon the infrastructure of [xlwings](https://github.com/xlwings/xlwings),
an excellent Python library for Excel integration created by Zoomer Analytics LLC.

The COM server, UDF registration system, and Excel communication layer are derived from
xlwings and are used under the BSD 3-Clause License.

The SQL parsing, query execution, and data handling components are original work developed
specifically for xlsqlite.

---

## License

BSD 3-Clause License

Copyright (c) 2014-present, Zoomer Analytics LLC (xlwings components)
Copyright (c) 2025-present, [Your Name] (xlsqlite extensions)

See [LICENSE.txt](LICENSE.txt) for full license text.

---

## Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## Support

- **Issues**: [GitHub Issues](https://github.com/[user]/xlsqlite/issues)
- **Discussions**: [GitHub Discussions](https://github.com/[user]/xlsqlite/discussions)
- **Email**: [your.email@example.com]

---

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history.
```

---

## 7. Success Criteria

### 7.1 Functional Requirements

- ✅ User can install with `pip install xlsqlite`
- ✅ User can type `=SQLITE()` in Excel and it works
- ✅ All SQL features work (JOINs, CTEs, window functions)
- ✅ Error messages are clear and helpful
- ✅ Results spill correctly in Excel
- ✅ Handles large datasets (10k+ rows)
- ✅ Works on Windows and macOS

### 7.2 Quality Requirements

- ✅ All 336+ tests pass
- ✅ Code coverage > 80%
- ✅ No memory leaks
- ✅ Performance: queries complete in < 5 seconds for 10k rows
- ✅ Documentation complete and clear
- ✅ Proper error handling (no crashes)

### 7.3 Legal Requirements

- ✅ BSD 3-Clause license properly applied
- ✅ xlwings attribution in all required places
- ✅ No use of "xlwings" name for endorsement
- ✅ All copyright notices correct

### 7.4 Distribution Requirements

- ✅ Package builds successfully (`python setup.py sdist bdist_wheel`)
- ✅ Package installs from PyPI
- ✅ CLI commands work (`xlsqlite addin install`)
- ✅ Add-in registers with Excel
- ✅ No xlwings dependency for end users

---

## 8. Timeline

**Total Estimated Time:** 16-20 hours

| Phase | Duration | Tasks |
|-------|----------|-------|
| 1. Setup | 2-3 hrs | Project structure, fork xlwings |
| 2. Rename | 2-3 hrs | Rebrand to xlsqlite |
| 3. Strip | 1-2 hrs | Remove unused code |
| 4. Integrate | 3-4 hrs | Add our SQL implementation |
| 5. Testing | 2-3 hrs | Test infrastructure |
| 6. Package | 2-3 hrs | setup.py, distribution |
| 7. Docs | 2-3 hrs | README, guides |
| 8. E2E Test | 3-4 hrs | End-to-end validation |

**Target Completion:** Can be done in 2-3 focused work days

---

## 9. Risks & Mitigation

### 9.1 Risk: COM Server Issues

**Risk:** COM registration fails on some Windows versions
**Mitigation:**
- Test on multiple Windows versions
- Provide detailed troubleshooting guide
- Include fallback installation method

### 9.2 Risk: Excel Version Compatibility

**Risk:** Different Excel versions behave differently
**Mitigation:**
- Test on Excel 2016, 2019, 365
- Document known issues
- Provide version-specific workarounds

### 9.3 Risk: License Compliance

**Risk:** Improper use of xlwings code
**Mitigation:**
- BSD license is permissive - low risk
- Proper attribution in all files
- Legal review if needed

### 9.4 Risk: Performance Issues

**Risk:** Slow with large datasets
**Mitigation:**
- Benchmark with 10k, 100k, 1M rows
- Optimize critical paths
- Document performance limits
- Consider chunking for very large datasets

### 9.5 Risk: Breaking Changes in xlwings

**Risk:** xlwings updates break our fork
**Mitigation:**
- Pin to specific xlwings version for initial fork
- Minimal dependencies on xlwings internals
- Clear documentation of which xlwings version we forked

---

## 10. Post-Launch

### 10.1 Distribution

- Publish to PyPI
- Create GitHub releases
- Add to conda-forge (optional)

### 10.2 Marketing

- Blog post announcement
- Reddit posts (r/excel, r/python)
- Tweet announcement
- Submit to awesome-excel lists

### 10.3 Maintenance

- Monitor GitHub issues
- Respond to user questions
- Plan feature roadmap
- Regular dependency updates

---

## 11. Future Enhancements

**Version 1.1:**
- Named table support (Excel Table objects)
- Better named range handling
- Query result caching

**Version 1.2:**
- SQL query builder UI
- Syntax highlighting
- Query history

**Version 2.0:**
- Multiple simultaneous queries
- Connection to external databases
- Custom Python UDFs in SQL

---

## Appendix A: Key Files from xlwings to Extract

**Must Have (Core Infrastructure):**

1. `xlwings/server.py` - COM server implementation
2. `xlwings/udfs.py` - UDF decorator system
3. `xlwings/main.py` - Book, Sheet, Range classes (strip to essentials)
4. `xlwings/_xlwindows.py` - Windows COM interface
5. `xlwings/_xlmac.py` - macOS interface
6. `xlwings/conversion/` - Type conversion framework
7. `xlwings/utils.py` - Utility functions
8. `xlwings/addin/xlwings.xlam` - Excel add-in template
9. `xlwings/addin/xlwings.bas` - VBA code
10. DLL files

**Study but Don't Copy (Reference Only):**

- `xlwings/ext/sql.py` - To understand their approach
- `xlwings/rest/` - REST API (we don't need)
- `xlwings/quickstart.py` - Project templates (we don't need)

---

## Appendix B: Important Constants

**Python Version Support:** 3.8+
**Excel Version Support:** 2016+
**SQLite Version:** Whatever's in Python (3.35+)
**Pandas Version:** 1.0.0+
**pywin32 Version:** 300+ (Windows only)

**Performance Targets:**
- 10k rows: < 5 seconds
- 100k rows: < 30 seconds
- Memory: < 500MB for typical queries

**Excel Limits:**
- Max rows: 1,048,576
- Max columns: 16,384
- We'll warn at 100k rows, error at Excel limits

---

## Appendix C: Testing Checklist

**Before Release:**

- [ ] All 336+ unit tests pass
- [ ] Integration tests pass
- [ ] Excel integration tests pass (all 7 test cases)
- [ ] Installation works on clean environment
- [ ] CLI commands work
- [ ] Add-in installs successfully
- [ ] =SQLITE() works in Excel
- [ ] Error messages display correctly
- [ ] Performance acceptable on large datasets
- [ ] Works on Windows 10/11
- [ ] Works on macOS (if possible)
- [ ] Documentation complete
- [ ] License files correct
- [ ] PyPI package builds
- [ ] No import errors
- [ ] No circular dependencies

---

## Appendix D: Contact Information

**Project Maintainer:** [Your Name]
**Email:** [your.email@example.com]
**GitHub:** https://github.com/[username]/xlsqlite
**Issues:** https://github.com/[username]/xlsqlite/issues

---

*End of Plan*

---

**Next Steps:**

1. Review this plan
2. Set up development environment
3. Begin Phase 1: Project Setup
4. Execute phases sequentially
5. Test thoroughly
6. Launch!

Good luck building xlsqlite! 🚀
