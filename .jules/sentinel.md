## 2025-02-17 - [CRITICAL] Fix Arbitrary Code Execution (ACE) via eval()

**Vulnerability:** Found arbitrary code execution via `eval()` when reading the external file `lineage.dependencies` in `librephone/extractor.py`.
**Learning:** External files such as JSON dependencies should never be parsed using `eval()` due to the severe risk of remote code execution.
**Prevention:** Always use safe and standard parsers like `json.load()` for parsing structured data formats like JSON.

## 2025-02-17 - [CRITICAL] Fix SQL Injection via User Input
**Vulnerability:** Found SQL injection via string formatting (`f"UPDATE devices SET {column} = '{value}'"`) when executing database queries in `librephone/update_dev.py`.
**Learning:** Using raw Python formatting (like f-strings) or string concatenation to pass variables to SQL engine ignores necessary escaping and opens up a vector for SQL injection.
**Prevention:** Always use parameterized queries (e.g., passing `%s` and a tuple of parameters to `cursor.execute()`). Ensure dynamic column names are strictly validated against alphanumerics if they cannot be parameterized.
