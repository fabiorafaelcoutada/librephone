# Instructions for Agents

This project, **librephone**, aims to reverse engineer Android proprietary blobs to create free replacements. The project is currently in a phase of rapid development and scaling.

## Goal
To analyze, document, and eventually replace proprietary Android binary blobs.

## Current Focus
We are currently focusing on:
1.  **Testing**: Establishing a robust test suite.
2.  **Refactoring**: Improving code structure and quality.
3.  **Portability**: Removing hardcoded paths and making the tool configurable.

## Tasks for Agents

### 1. Testing
- [ ] **Add Tests for `extractor.py`**: Create `tests/test_extractor.py`. This is critical. Mock external commands (`subprocess.run`) and file system operations.
- [ ] **Add Tests for `import_dev.py`**: Create `tests/test_import_dev.py`. Mock database connections (`psycopg`).
- [ ] **Add Tests for `query_dev.py`**: Create `tests/test_query_dev.py`. Mock database queries.
- [ ] **Increase Coverage**: Aim for high code coverage.

### 2. Code Quality & Refactoring
- [ ] **Refactor `Extractor` class**: The `Extractor` class in `librephone/extractor.py` is too large. Split it into smaller, more focused classes (e.g., `Decompressor`, `Mounter`, `Cloner`).
- [ ] **Error Handling**: Replace bare `except: breakpoint()` with proper error handling (try/except specific exceptions) and logging.
- [ ] **Type Hinting**: Add type hints to all functions and classes.
- [ ] **Remove Hardcoded Paths**:
    - `librephone/extractor.py`: `lineage = "/work/Lineage-23.0"`
    - `librephone/query_dev.py`: `self.dbname = "devices"`
    - `librephone/import_dev.py`: `dbname: str = "devices"`
    - Use a configuration file (e.g., `config.yaml` or `.env`) or environment variables.

### 3. Documentation
- [ ] **Update Docstrings**: Ensure all functions have Google-style docstrings.
- [ ] **Generate Documentation**: Set up `mkdocs` to generate API documentation from docstrings.

## Development Setup

### Dependencies
Install dependencies using `pip`:
```bash
pip install -r requirements.txt  # If exists, or manually
pip install python-magic progress pytest psycopg
```

### Running Tests
Run tests using `pytest`:
```bash
pytest
```

### Code Style
- Follow PEP 8.
- Use `black` for formatting.
- Use `ruff` for linting.

## Known Issues
- `DeviceFiles.get_magic` has a bug where it reads only 4 bytes but compares against longer magic numbers (e.g., for PNG).
- `unblob` dependency is commented out but listed in `pyproject.toml`.
