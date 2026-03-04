## 2024-05-01 - [Arbitrary Code Execution in Dependency Parsing]
**Vulnerability:** Extractor used `eval()` to parse `.dependencies` files, which could execute arbitrary python code if an attacker provides a malicious `.dependencies` file.
**Learning:** `.dependencies` files in this codebase (like `lineage.dependencies`) contain Python literals rather than standard valid JSON, making `json.load()` unsuitable.
**Prevention:** Always use `ast.literal_eval()` instead of `eval()` when parsing strings containing python literals to prevent arbitrary code execution, while strictly avoiding `eval()`.
