## 2025-02-17 - [CRITICAL] Fix Arbitrary Code Execution (ACE) via eval()

**Vulnerability:** Found arbitrary code execution via `eval()` when reading the external file `lineage.dependencies` in `librephone/extractor.py`.
**Learning:** External files such as JSON dependencies should never be parsed using `eval()` due to the severe risk of remote code execution.
**Prevention:** Always use safe and standard parsers like `json.load()` for parsing structured data formats like JSON.
## 2025-02-18 - [CRITICAL] Fix Arbitrary Code Execution (ACE) via yaml.load()
**Vulnerability:** Found arbitrary code execution vulnerability via `yaml.load()` using `yaml.Loader` when parsing configuration files in `librephone/yamlfile.py`.
**Learning:** `yaml.load()` with the default `Loader` can instantiate arbitrary Python objects, leading to Remote Code Execution (RCE) if a malicious YAML file is processed.
**Prevention:** Always use `yaml.safe_load()` which restricts parsing to standard YAML tags like dicts, lists, strings, and integers, eliminating the execution risk.
