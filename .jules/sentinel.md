## 2025-02-17 - [CRITICAL] Fix Arbitrary Code Execution (ACE) via eval()

**Vulnerability:** Found arbitrary code execution via `eval()` when reading the external file `lineage.dependencies` in `librephone/extractor.py`.
**Learning:** External files such as JSON dependencies should never be parsed using `eval()` due to the severe risk of remote code execution.
**Prevention:** Always use safe and standard parsers like `json.load()` for parsing structured data formats like JSON.

## 2025-02-18 - [CRITICAL] Fix SQL Injection via Dynamic Column Names
**Vulnerability:** Found SQL injection via unparameterized dynamic column names in `UPDATE` queries within `update_dev.py`.
**Learning:** When using dynamic column names in `psycopg` 3 queries, the column names cannot be parameterized. They must be strictly validated (e.g., using `.isalnum()`) before string interpolation to prevent SQL injection.
**Prevention:** Always validate dynamic identifiers and continue using `%s` placeholders for query values.
