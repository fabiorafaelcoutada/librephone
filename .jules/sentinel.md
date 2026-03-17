## 2025-02-17 - [CRITICAL] Fix Arbitrary Code Execution (ACE) via eval()

**Vulnerability:** Found arbitrary code execution via `eval()` when reading the external file `lineage.dependencies` in `librephone/extractor.py`.
**Learning:** External files such as JSON dependencies should never be parsed using `eval()` due to the severe risk of remote code execution.
**Prevention:** Always use safe and standard parsers like `json.load()` for parsing structured data formats like JSON.

## 2025-02-18 - [CRITICAL] Fix SQL Injection in dynamic columns

**Vulnerability:** Found SQL injection vulnerabilities in `librephone/update_dev.py` (`set_column` and `set_columns`) where the string interpolation of user input variables into SQL queries occurred instead of parameterization.
**Learning:** `psycopg3` requires using explicit parameterized queries with `%s` to prevent SQL Injection. Moreover, when table or column names need to be dynamically specified, they cannot be parameterized with `%s`. String formatting must be used but only after strict validation, e.g., using `isalnum()` to verify the identifier only contains safe characters.
**Prevention:** Always parameterize user inputs as query arguments using `%s`. For dynamic identifier names, sanitize and validate strictly (e.g., `str(column).replace('_', '').isalnum()`) before injecting into the SQL string.
