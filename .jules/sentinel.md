## 2025-02-17 - [CRITICAL] Fix Arbitrary Code Execution (ACE) via eval()

**Vulnerability:** Found arbitrary code execution via `eval()` when reading the external file `lineage.dependencies` in `librephone/extractor.py`.
**Learning:** External files such as JSON dependencies should never be parsed using `eval()` due to the severe risk of remote code execution.
**Prevention:** Always use safe and standard parsers like `json.load()` for parsing structured data formats like JSON.
## 2023-10-27 - [CRITICAL] Fix SQL injection in device update queries
**Vulnerability:** Found an SQL injection vulnerability via unsafe f-string formatting when building dynamic queries in `librephone/update_dev.py`.
**Learning:** `psycopg3` natively supports parameterized query structures natively. In dynamic query scenarios involving table fields or columns, one should securely compose queries using `psycopg.sql.SQL` instead of vulnerable string concatenations.
**Prevention:** Use strictly safe format parameterizations mapping `psycopg.sql.Identifier` to safely escape schema or database fields and parameter bounds with standard positional (%s) interpolation.
