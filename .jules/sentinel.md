## 2025-02-14 - Arbitrary Code Execution via eval()
**Vulnerability:** Found `eval(fd.read())` used to parse a Python-literal configuration file (`lineage.dependencies`) in `extractor.py`.
**Learning:** Legacy parsing of configuration files might use `eval()` assuming trusted input, but file content can be malicious or compromised.
**Prevention:** Never use `eval()` for parsing data. Use `ast.literal_eval()` for safe parsing of Python literals, or strict parsers like `json.load()` if the format allows.
