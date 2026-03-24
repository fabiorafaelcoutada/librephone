## 2025-02-17 - [CRITICAL] Fix Arbitrary Code Execution (ACE) via eval()

**Vulnerability:** Found arbitrary code execution via `eval()` when reading the external file `lineage.dependencies` in `librephone/extractor.py`.
**Learning:** External files such as JSON dependencies should never be parsed using `eval()` due to the severe risk of remote code execution.
**Prevention:** Always use safe and standard parsers like `json.load()` for parsing structured data formats like JSON.

## 2025-02-18 - [CRITICAL] Fix SQL Injection in dynamic columns

**Vulnerability:** Found SQL injection vulnerabilities in `librephone/update_dev.py` (`set_column` and `set_columns`) where the string interpolation of user input variables into SQL queries occurred instead of parameterization.
**Learning:** `psycopg3` requires using explicit parameterized queries with `%s` to prevent SQL Injection. Moreover, when table or column names need to be dynamically specified, they cannot be parameterized with `%s`. String formatting must be used but only after strict validation, e.g., using `isalnum()` to verify the identifier only contains safe characters.
**Prevention:** Always parameterize user inputs as query arguments using `%s`. For dynamic identifier names, sanitize and validate strictly (e.g., `str(column).replace('_', '').isalnum()`) before injecting into the SQL string.

## 2025-02-18 - [CRITICAL] Fix Insecure YAML Deserialization leading to ACE

**Vulnerability:** Discovered the use of `yaml.load(self.file, Loader=yaml.Loader)` in `librephone/yamlfile.py`, which permits the execution of arbitrary Python code embedded in YAML files.
**Learning:** The default `Loader` allows constructing arbitrary Python objects, meaning an attacker could craft a malicious YAML file that executes a remote payload upon parsing.
**Prevention:** Always replace `yaml.load(..., Loader=yaml.Loader)` with the secure `yaml.safe_load(...)` which limits deserialization to simple primitive types.

## 2026-03-24 - [CRITICAL] Fix Command Injection via eval() in Bash
**Vulnerability:** Found arbitrary command execution via `eval` when parsing dynamically generated metadata in `images_util.sh`.
**Learning:** Parsing variables or metadata with `eval` in Bash scripts is extremely dangerous, particularly when the inputs (like filenames) can be manipulated by an attacker.
**Prevention:** Avoid `eval` entirely. Instead, output safe, delimited strings (e.g., using `|` as a delimiter) and safely parse them using `IFS='|' read -r var1 var2 var3 <<< "$output"`.
