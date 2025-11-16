# Contributing to AIBooks

Thank you for your interest in contributing to AIBooks! This document provides guidelines for contributing.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/yourusername/AIBooks.git`
3. Create a branch: `git checkout -b feature/your-feature`
4. Make your changes
5. Run tests: `pytest`
6. Commit: `git commit -m "Add your feature"`
7. Push: `git push origin feature/your-feature`
8. Create a Pull Request

## Development Setup

```bash
# Install in development mode
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Run tests
pytest

# Run type checking
mypy src/

# Format code
black src/
ruff check src/
```

## Code Style

- Follow PEP 8
- Use Black for formatting (line length: 100)
- Use type hints
- Write docstrings for all public functions

## Testing

- Write tests for new features
- Maintain test coverage above 80%
- Run tests before submitting PR

## Pull Request Guidelines

- Clear description of changes
- Reference related issues
- Include tests
- Update documentation if needed

## Questions?

Open an issue or contact the maintainers.
