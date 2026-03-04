## 2024-05-24 - [CRITICAL] Fix Arbitrary Code Execution in file parsing
**Vulnerability:** Arbitrary Code Execution via `eval()` when parsing `lineage.dependencies` in `librephone/extractor.py`.
**Learning:** `eval()` was used to parse JSON-formatted string which allows executing arbitrary Python code if the dependency file is manipulated.
**Prevention:** Use standard, secure parsers like `json.load()`/`json.loads()` for parsing JSON files.
