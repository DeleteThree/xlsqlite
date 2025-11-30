# xlsqlite

**SQL Query Engine for Microsoft Excel**

Execute powerful SQL queries directly in Excel using the `=SQLITE()` custom function.

[![License](https://img.shields.io/badge/License-BSD%203--Clause-blue.svg)](LICENSE.txt)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![Status](https://img.shields.io/badge/Status-In%20Development-yellow.svg)](https://github.com/DeleteThree/xlsqlite)

---

## 🚀 Features

✅ **Full SQLite Support** - All SQL features: JOINs, CTEs, window functions, subqueries
✅ **Easy Installation** - `pip install xlsqlite` + one command
✅ **Smart Type Inference** - Automatic INTEGER/REAL/TEXT detection
✅ **Comprehensive Errors** - SQLite-style error messages
✅ **Well Tested** - 336+ automated tests
✅ **Cross-Platform** - Windows and macOS
✅ **Independent** - No xlwings dependency for users

---

## 📦 Installation

**Coming Soon!** Once released:

```bash
# Install package
pip install xlsqlite

# Install Excel add-in
xlsqlite addin install
```

Then open Excel and start using `=SQLITE()`.

---

## 💡 Quick Examples

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

## 🎯 Why xlsqlite?

**vs. Excel Formulas:**
- More powerful (JOINs, window functions, CTEs)
- Easier to read and maintain
- Better performance on large datasets

**vs. xlwings SQL:**
- More robust parser (handles Sheet.Table, cross-sheet references)
- Better type inference (INTEGER/REAL/TEXT detection)
- Comprehensive error messages
- Full SQLite feature set
- 336+ automated tests

**vs. Power Query:**
- Simpler for SQL users (no M language learning curve)
- Dynamic (recalculates with data changes)
- Lightweight (no external connections)

---

## 📚 Supported SQL Features

- ✅ SELECT, INSERT, UPDATE, DELETE
- ✅ JOINs (INNER, LEFT, RIGHT, CROSS)
- ✅ Window Functions (ROW_NUMBER, RANK, LAG, LEAD, etc.)
- ✅ CTEs (WITH clauses, including recursive)
- ✅ Subqueries (correlated and uncorrelated)
- ✅ Aggregations (GROUP BY, HAVING)
- ✅ All SQLite built-in functions
- ✅ Parameterized queries with `?` placeholders

---

## 📖 Documentation

**Project Planning:**
- [PLAN.md](PLAN.md) - Complete 8-phase implementation plan
- [CONTRIBUTING.md](CONTRIBUTING.md) - How to contribute

**Coming Soon:**
- User Guide - Complete usage documentation
- API Reference - Function signatures and parameters
- Examples - Real-world query patterns
- FAQ - Common questions

---

## 🛠️ Development Status

**Current Phase:** Planning & Setup
**Target Release:** TBD

### Implementation Plan

- [ ] Phase 1: Project Setup & Fork Preparation (2-3 hours)
- [ ] Phase 2: Rename & Rebrand xlwings → xlsqlite (2-3 hours)
- [ ] Phase 3: Strip Unnecessary Code (1-2 hours)
- [ ] Phase 4: Integrate SQL Implementation (3-4 hours)
- [ ] Phase 5: Testing Infrastructure (2-3 hours)
- [ ] Phase 6: Packaging & Distribution (2-3 hours)
- [ ] Phase 7: Documentation (2-3 hours)
- [ ] Phase 8: End-to-End Testing (3-4 hours)

**Total Estimated Time:** 16-20 hours

See [PLAN.md](PLAN.md) for detailed specifications.

---

## 🏗️ Architecture

```
Excel Cell: =SQLITE("SELECT * FROM Sheet1!A1:D10")
                    ↓
         VBA Wrapper (xlsqlite.xlam)
                    ↓
         Python COM Server
                    ↓
    ┌───────────────┴────────────────┐
    │     SQLITE Function            │
    │  1. Parser - Extract refs      │
    │  2. Schema - Read Excel data   │
    │  3. Executor - Run SQL         │
    │  4. Output - Format results    │
    └────────────────────────────────┘
                    ↓
            Results spill in Excel
```

---

## 🔧 Requirements

- Python 3.8+
- Microsoft Excel 2016+ (Windows/Mac)
- pandas >= 1.0.0
- pywin32 >= 300 (Windows only)

---

## 🤝 Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

**Ways to contribute:**
- Report bugs
- Suggest features
- Submit pull requests
- Improve documentation
- Write tests

---

## 🙏 Acknowledgments

xlsqlite is built upon the infrastructure of [xlwings](https://github.com/xlwings/xlwings),
an excellent Python library for Excel integration created by Zoomer Analytics LLC.

**What we use from xlwings:**
- COM server architecture
- UDF registration system
- Excel communication layer
- VBA wrapper generation

**What we built new:**
- SQL parsing engine
- Query execution logic
- Type inference system
- Error handling
- Test suite (336+ tests)

All xlwings-derived code is used under the BSD 3-Clause License.

---

## 📄 License

BSD 3-Clause License

**Copyright:**
- xlwings components: Copyright (c) 2014-present, Zoomer Analytics LLC
- xlsqlite extensions: Copyright (c) 2025-present, DeleteThree

See [LICENSE.txt](LICENSE.txt) for full license text.

---

## 📬 Contact

- **Issues:** [GitHub Issues](https://github.com/DeleteThree/xlsqlite/issues)
- **Discussions:** [GitHub Discussions](https://github.com/DeleteThree/xlsqlite/discussions)
- **Repository:** [github.com/DeleteThree/xlsqlite](https://github.com/DeleteThree/xlsqlite)

---

## 🗺️ Roadmap

### Version 1.0 (Initial Release)
- Core SQLITE() function
- All SQL features working
- Windows and macOS support
- PyPI distribution
- Complete documentation

### Version 1.1 (Future)
- Named Excel Table support
- Query result caching
- Performance optimizations

### Version 1.2 (Future)
- SQL query builder UI
- Syntax highlighting
- Query history

### Version 2.0 (Future)
- External database connections
- Custom Python UDFs in SQL
- Advanced data transformations

---

## ⭐ Star History

If you find xlsqlite useful, please consider starring the repository!

---

**Built with ❤️ and powered by SQLite**

*Last updated: 2025-01-30*
