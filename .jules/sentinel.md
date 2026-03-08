## 2025-02-17 - [CRITICAL] Fix Arbitrary Code Execution (ACE) via eval()

**Vulnerability:** Found arbitrary code execution via `eval()` when reading the external file `lineage.dependencies` in `librephone/extractor.py`.
**Learning:** External files such as JSON dependencies should never be parsed using `eval()` due to the severe risk of remote code execution.
**Prevention:** Always use safe and standard parsers like `json.load()` for parsing structured data formats like JSON.

## 2025-02-18 - [HIGH] Fix SQL Injection via unparameterized strings
**Vulnerability:** Found SQL injection vulnerabilities in `update_dev.py` where column names and values were formatted into SQL query strings dynamically.
**Learning:** `psycopg3` does not support parameterization of identifiers like column names, requiring manual validation logic before execution.
**Prevention:** Ensure explicit string checks (like `.isalnum()`) for parameter names being interpolated into query formats, while using `%s` arguments for column values.

## 2025-02-18 - [HIGH] Fix SQL Injection via unparameterized strings
**Vulnerability:** Found SQL injection vulnerabilities in `update_dev.py` where column names and values were formatted into SQL query strings dynamically.
**Learning:** `psycopg3` does not support parameterization of identifiers like column names, requiring manual validation logic before execution.
**Prevention:** Ensure explicit string checks (like `.isalnum()`) for parameter names being interpolated into query formats, while using `%s` arguments for column values.
