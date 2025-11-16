# Testing Documentation

## Overview

AIBooks includes comprehensive testing infrastructure to ensure code quality and reliability.

## Test Suite

### Basic Tests (No Dependencies Required)

Run basic functionality tests without installing all dependencies:

```bash
python3 scripts/test_basic.py
```

Tests include:
- ✅ Import validation
- ✅ Format detection (PDF, EPUB, DOCX, TXT)
- ✅ Text cleaning (hyphenation, whitespace)
- ✅ Content hashing (SHA-256)

### Full Test Suite (Requires Dependencies)

Install test dependencies:

```bash
pip install -r requirements-dev.txt
```

Run full test suite:

```bash
pytest tests/ -v
```

Test coverage:

```bash
pytest tests/ -v --cov=aibooks --cov-report=html
open htmlcov/index.html
```

## Test Files

### `tests/test_database.py`

Tests for database models and operations:
- Document creation and queries
- GenAI usage logging
- Agent learning storage
- Duplicate relationships
- Content hash uniqueness

### `tests/test_parsers.py`

Tests for document parsing:
- Format detection (extension, content, MIME type)
- Metadata fusion from multiple sources
- Filename metadata extraction
- Text cleaning operations

### `tests/test_agents.py`

Tests for the 6 intelligent agents:
- Format Strategist decision-making
- Metadata Intelligence quality assessment
- Text Quality analysis
- Cost Optimizer budget management
- Failure Recovery strategies
- (Pipeline Evolution tested via integration)

### `tests/test_utils.py`

Tests for utility functions:
- Content hashing
- File hashing
- Hash consistency and uniqueness

## Validation Scripts

### `scripts/validate.sh`

Comprehensive validation covering:
1. Python syntax checking
2. Basic functionality tests
3. Common issue detection
4. Project structure verification

Run with:

```bash
bash scripts/validate.sh
```

### `scripts/test_basic.py`

Lightweight test runner that works without full dependencies:

```bash
python3 scripts/test_basic.py
```

## Continuous Integration

GitHub Actions workflow (`.github/workflows/test.yml`) runs on:
- Every push to `main` or `develop`
- Every pull request to `main`

Tests run on:
- Ubuntu Latest
- macOS Latest
- Python 3.10, 3.11, 3.12

## Test Results

Current test status:

```
✅ Basic Tests: 4/4 PASSED
✅ Syntax Check: All files valid
✅ Project Structure: All required files present
⚠️  TODO Comments: 2 found
```

## Writing Tests

### Adding a New Test

1. Create test file in `tests/` directory
2. Import required modules
3. Use pytest fixtures for database sessions
4. Follow naming convention: `test_*.py`

Example:

```python
import pytest
from aibooks.your_module import YourClass

def test_your_function():
    """Test your function."""
    result = YourClass().your_method()
    assert result == expected_value
```

### Using Fixtures

Database fixture example:

```python
@pytest.fixture
def test_db():
    """Create temporary test database."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = init_database(str(db_path))
        yield db
```

## Manual Testing

### Test Document Ingestion

```bash
# Create test document
echo "This is a test document." > test.txt

# Ingest
aibooks ingest test.txt

# Check output
ls output/txt/
ls output/md/
ls output/json/

# View stats
aibooks stats
```

### Test CLI Commands

```bash
# Help
aibooks --help
aibooks ingest --help

# Init
aibooks init

# Stats
aibooks stats

# Evolution
aibooks evolve
```

## Known Issues

1. **Dependencies**: Some tests require full dependency installation
2. **Docling**: Parser tests require Docling to be installed
3. **LLM APIs**: Cost tracking tests need API keys (can be mocked)

## Future Improvements

- [ ] Integration tests for full pipeline
- [ ] Mock LLM API calls in tests
- [ ] Performance benchmarks
- [ ] Load testing for batch processing
- [ ] Docker-based test environment

## Troubleshooting

### ModuleNotFoundError

```bash
# Ensure dependencies installed
pip install -r requirements-dev.txt

# Ensure you're in project root
cd /path/to/AIBooks

# Check Python path
python3 -c "import sys; print(sys.path)"
```

### Test Failures

```bash
# Run specific test
pytest tests/test_database.py::test_create_document -v

# Run with debugging
pytest tests/ -v -s

# Show full traceback
pytest tests/ --tb=long
```

## Coverage Goals

- **Target**: 80%+ code coverage
- **Current**: Basic functionality covered
- **Priority**: Core pipeline and agent logic

Run coverage report:

```bash
pytest --cov=aibooks --cov-report=term-missing
```

---

**For issues or questions, please open a GitHub issue.**
