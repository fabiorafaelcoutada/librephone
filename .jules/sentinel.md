## 2025-05-24 - Arbitrary Code Execution via `eval()`

**Vulnerability:** The application used `eval()` to parse `lineage.dependencies` files, which are externally controllable.
**Learning:** Never trust file content, even if it looks like configuration. Python's `eval()` executes arbitrary code.
**Prevention:** Always use safe parsers like `json.load()` for data serialization formats.
