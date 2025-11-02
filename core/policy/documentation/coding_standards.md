# Coding Standards

Common standards for code style and documentation.

- Style
  - Follow PEP 8 for Python where applicable
  - Use snake_case for files and identifiers (see naming_standards.md)

- Docstrings
  - Provide docstrings for public functions and modules (Google or NumPy style)
  - Include purpose, params, returns, raises, and examples if helpful

- Linting and Formatting
  - Enable linters (flake8/ruff) and formatters (black) in CI
  - Keep configuration at repo root (pyproject.toml/setup.cfg) when added

- Type Hints
  - Use typing for public APIs; run mypy/pyright where feasible

- Testing
  - Co-locate unit tests mirroring module names; follow test_<module>.py
  - Prefer pure functions to simplify testing
