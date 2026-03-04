## 2025-02-17 - Arbitrary Code Execution via eval()
**Vulnerability:** `librephone/extractor.py` used `eval()` to parse `lineage.dependencies` files, which allows arbitrary code execution if the file is malicious.
**Learning:** `eval()` was likely used as a shortcut to parse a Python list-like structure (JSON), but it executes any Python code.
**Prevention:** Use safe parsers like `json.load()` for data files. Never use `eval()` on untrusted input.
