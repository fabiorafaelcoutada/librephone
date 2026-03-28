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

## 2025-02-18 - [CRITICAL] Fix command injection in bash scripts via eval

**Vulnerability:** Found command injection vulnerability in `images_util.sh` where `eval` was used to parse metadata strings output by a function.
**Learning:** `eval` is inherently unsafe for parsing dynamic strings, especially when they might contain filenames or user input, as it can execute arbitrary shell commands.
**Prevention:** Avoid `eval` for parsing variables. Instead, structure script outputs using a safe delimiter (like `|`) and safely capture/assign them using `IFS='|' read -r` to properly handle variables and prevent command injection.
