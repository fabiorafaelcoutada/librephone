## 2025-01-22 - [CRITICAL] Prevent Arbitrary Code Execution (ACE) via `eval()`

**Vulnerability:** Arbitrary Code Execution (ACE) via `eval()` parsing of `lineage.dependencies` files. The project was using `eval(fd.read())` to parse the external JSON-like `lineage.dependencies` files.
**Learning:** `eval()` executes the passed string as arbitrary Python code, leaving the application extremely vulnerable to executing malicious code if an attacker can manipulate the dependency files.
**Prevention:** Always use safe and appropriate parsers like `json.load()` to parse external configuration or dependency files. Never use `eval()` on untrusted input data.
