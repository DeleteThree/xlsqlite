# Contributing to xlsqlite

Thank you for your interest in contributing to xlsqlite! This document provides guidelines and information for contributors.

---

## 🎯 Ways to Contribute

There are many ways to contribute to xlsqlite:

- **Report bugs** - Found an issue? Let us know!
- **Suggest features** - Have an idea? Share it!
- **Submit pull requests** - Fix bugs or add features
- **Improve documentation** - Help others understand xlsqlite
- **Write tests** - Increase code coverage
- **Share feedback** - Tell us about your experience

---

## 🐛 Reporting Bugs

Before submitting a bug report, please:

1. **Check existing issues** - Your bug may already be reported
2. **Use the latest version** - The bug might be fixed
3. **Provide details** - Help us reproduce the issue

### Bug Report Template

```markdown
**Description:**
Clear description of the bug

**To Reproduce:**
1. Create Excel sheet with data...
2. Enter formula: =SQLITE("...")
3. See error...

**Expected Behavior:**
What should happen

**Actual Behavior:**
What actually happens

**Environment:**
- xlsqlite version:
- Python version:
- Excel version:
- OS: Windows 10 / macOS 13 / etc.

**Error Message:**
```
Paste any error messages here
```

**Sample Data:**
If possible, provide minimal sample data that reproduces the issue
```

---

## 💡 Suggesting Features

We welcome feature suggestions! Please:

1. **Check existing issues** - Someone may have suggested it
2. **Describe the use case** - Why is this feature needed?
3. **Provide examples** - Show how it would work

### Feature Request Template

```markdown
**Feature Description:**
Clear description of the proposed feature

**Use Case:**
Why is this feature valuable? What problem does it solve?

**Proposed Syntax:**
=SQLITE("...")

**Examples:**
Show how users would use this feature

**Alternative Solutions:**
Are there workarounds? Other approaches considered?
```

---

## 🔧 Development Setup

### Prerequisites

- Python 3.8 or higher
- Git
- Microsoft Excel (for testing)
- Virtual environment tool (venv, conda, etc.)

### Setup Steps

1. **Fork the repository**

   Click "Fork" on GitHub to create your own copy

2. **Clone your fork**

   ```bash
   git clone https://github.com/YOUR-USERNAME/xlsqlite.git
   cd xlsqlite
   ```

3. **Create virtual environment**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

4. **Install in development mode**

   ```bash
   pip install -e .[dev]
   ```

5. **Install pre-commit hooks** (optional but recommended)

   ```bash
   pip install pre-commit
   pre-commit install
   ```

6. **Verify setup**

   ```bash
   pytest tests/ -v
   ```

---

## 📝 Code Style

We follow standard Python conventions:

### Style Guidelines

- **PEP 8** - Python style guide
- **Black** - Code formatter (line length: 88)
- **Type hints** - Use type annotations where helpful
- **Docstrings** - Google-style docstrings

### Example

```python
def execute_query(
    conn: sqlite3.Connection,
    query: str,
    params: tuple = ()
) -> ExecutionResult:
    """
    Execute SQL query against in-memory database.

    Args:
        conn: SQLite database connection
        query: SQL query string
        params: Optional query parameters for ? placeholders

    Returns:
        ExecutionResult containing columns, rows, and metadata

    Raises:
        QuerySyntaxError: If SQL syntax is invalid
        ExecutionError: If query execution fails

    Examples:
        >>> result = execute_query(conn, "SELECT * FROM orders")
        >>> result = execute_query(conn, "SELECT * WHERE id=?", (123,))
    """
    # Implementation...
```

### Running Code Formatters

```bash
# Format code with black
black xlsqlite/ tests/

# Check style with flake8
flake8 xlsqlite/ tests/

# Type checking with mypy (optional)
mypy xlsqlite/
```

---

## ✅ Testing

All code contributions should include tests.

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_parser.py -v

# Run with coverage
pytest tests/ --cov=xlsqlite --cov-report=html

# Run specific test
pytest tests/test_parser.py::test_extract_simple_table -v
```

### Writing Tests

- **One test, one assertion** - Keep tests focused
- **Descriptive names** - `test_parser_extracts_sheet_qualified_table()`
- **Arrange-Act-Assert** - Clear test structure
- **Edge cases** - Test boundary conditions

Example:

```python
def test_parser_extracts_simple_table_reference():
    """Parser should extract simple table name from FROM clause."""
    # Arrange
    query = "SELECT * FROM Orders"

    # Act
    refs = extract_table_references(query)

    # Assert
    assert len(refs) == 1
    assert refs[0].original == "Orders"
    assert refs[0].table_name == "Orders"
    assert refs[0].sheet_name is None
```

### Test Organization

```
tests/
├── test_parser_basic.py       # Basic parser tests
├── test_parser_edge_cases.py  # Edge case tests
├── test_schema.py              # Schema builder tests
├── test_executor.py            # Query executor tests
├── test_errors.py              # Error handling tests
├── test_output.py              # Output formatting tests
├── test_integration.py         # End-to-end integration tests
└── conftest.py                 # Shared fixtures
```

---

## 🔀 Pull Request Process

### Before Submitting

1. **Create a branch** for your changes
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** following code style guidelines

3. **Write/update tests** to cover your changes

4. **Run tests** to ensure everything passes
   ```bash
   pytest tests/ -v
   ```

5. **Update documentation** if needed

6. **Commit your changes** with clear messages
   ```bash
   git commit -m "Add feature: description of change"
   ```

### Commit Message Guidelines

Follow conventional commits format:

```
type(scope): brief description

Longer description if needed

Examples:
- feat(parser): add support for CTE parsing
- fix(schema): handle NULL values in type inference
- docs(readme): update installation instructions
- test(executor): add tests for window functions
```

**Types:**
- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation changes
- `test` - Adding or updating tests
- `refactor` - Code refactoring
- `perf` - Performance improvements
- `chore` - Maintenance tasks

### Submitting Pull Request

1. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

2. **Create pull request** on GitHub

3. **Fill out PR template** with:
   - Description of changes
   - Related issue (if any)
   - Testing performed
   - Screenshots (if UI changes)

4. **Wait for review** - Maintainers will review your PR

5. **Address feedback** - Make requested changes

6. **Merge** - Once approved, your PR will be merged!

### PR Checklist

- [ ] Code follows style guidelines
- [ ] Tests added/updated and passing
- [ ] Documentation updated
- [ ] Commit messages are clear
- [ ] No breaking changes (or clearly documented)
- [ ] PR description is complete

---

## 📁 Project Structure

Understanding the codebase structure:

```
xlsqlite/
├── xlsqlite/               # Main package
│   ├── __init__.py        # Package entry point
│   ├── server.py          # COM server (from xlwings)
│   ├── udfs.py            # UDF decorators (from xlwings)
│   ├── main.py            # Excel integration (from xlwings)
│   ├── addin/             # Excel add-in files
│   └── ext/
│       └── sqlite/        # Our SQL implementation
│           ├── __init__.py    # SQLITE() function
│           ├── parser.py      # SQL parser
│           ├── schema.py      # Schema builder
│           ├── executor.py    # Query executor
│           ├── errors.py      # Error handling
│           └── output.py      # Output formatter
├── tests/                 # Test suite
├── docs/                  # Documentation
├── examples/              # Example workbooks
└── setup.py               # Package configuration
```

### Key Modules

**Infrastructure (from xlwings):**
- `server.py` - Python COM server that Excel communicates with
- `udfs.py` - Decorators for registering UDFs
- `main.py` - Excel object model (Book, Sheet, Range)

**SQL Engine (our code):**
- `parser.py` - Extracts table references from SQL
- `schema.py` - Reads Excel data, infers types
- `executor.py` - Runs queries in SQLite
- `errors.py` - Formats error messages
- `output.py` - Formats results for Excel

---

## 🏗️ Development Workflow

### Typical Development Cycle

1. **Pick an issue** or create one
2. **Create branch** for your work
3. **Write failing test** (TDD approach)
4. **Implement feature** to pass test
5. **Run full test suite** to ensure no regressions
6. **Update documentation** as needed
7. **Commit and push** changes
8. **Create pull request** for review

### Testing in Excel

For changes that affect Excel integration:

1. **Install in development mode**
   ```bash
   pip install -e .
   xlsqlite addin install
   ```

2. **Create test workbook** with sample data

3. **Test function** in Excel
   ```excel
   =SQLITE("SELECT * FROM A1:D10")
   ```

4. **Verify results** match expectations

5. **Test error cases** to ensure proper error display

---

## 🤔 Questions?

- **Check existing issues** - Your question may be answered
- **Ask in Discussions** - [GitHub Discussions](https://github.com/DeleteThree/xlsqlite/discussions)
- **Open an issue** - For specific problems

---

## 📜 Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inclusive environment for all contributors.

### Expected Behavior

- Be respectful and constructive
- Welcome newcomers and help them learn
- Focus on what's best for the project
- Show empathy towards other contributors

### Unacceptable Behavior

- Harassment or discrimination
- Trolling or insulting comments
- Personal or political attacks
- Publishing others' private information

### Enforcement

Violations may result in temporary or permanent ban from the project.

---

## 🙏 Recognition

Contributors will be recognized in:
- README.md contributors section
- Release notes
- GitHub contributors page

Thank you for contributing to xlsqlite! 🎉

---

*Last updated: 2025-01-30*
