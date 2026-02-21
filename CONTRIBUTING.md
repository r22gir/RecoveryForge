# Contributing to RecoveryForge

Thank you for your interest in contributing to RecoveryForge! This document provides guidelines and instructions for contributing.

## Code of Conduct

Please be respectful and constructive in all interactions. We're building a tool to help people, so let's maintain a positive community.

## How to Contribute

### Reporting Bugs

1. Check if the bug has already been reported in [Issues](https://github.com/r22gir/RecoveryForge/issues)
2. If not, create a new issue with:
   - Clear title and description
   - Steps to reproduce
   - Expected vs actual behavior
   - System information (OS, Python version, etc.)
   - Log files if available

### Suggesting Features

1. Check [Discussions](https://github.com/r22gir/RecoveryForge/discussions) for similar suggestions
2. Create a new discussion or issue describing:
   - The problem you're trying to solve
   - Your proposed solution
   - Any alternatives you've considered
   - Why this would be useful to others

### Contributing Code

#### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/r22gir/RecoveryForge.git
cd RecoveryForge

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install development dependencies
pip install -r requirements-dev.txt
pip install -r requirements.txt

# Install pre-commit hooks (if available)
pre-commit install
```

#### Making Changes

1. **Fork the repository** on GitHub
2. **Create a branch** for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make your changes** following our style guide
4. **Write tests** for new functionality
5. **Run tests** to ensure nothing breaks:
   ```bash
   pytest tests/
   ```
6. **Format code** using Black:
   ```bash
   black src/ tests/
   ```
7. **Check linting**:
   ```bash
   flake8 src/ tests/
   mypy src/
   ```
8. **Commit changes**:
   ```bash
   git commit -m "feat: add new feature description"
   ```
9. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```
10. **Create Pull Request** on GitHub

#### Commit Message Format

We follow conventional commits:

- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `style:` - Code style changes (formatting, etc.)
- `refactor:` - Code refactoring
- `test:` - Adding or updating tests
- `chore:` - Maintenance tasks

Examples:
```
feat: add fuzzy file matching with ssdeep
fix: correct hash calculation for large files
docs: update installation instructions for Windows
```

#### Code Style Guidelines

**Python:**
- Follow PEP 8
- Use Black for formatting (line length: 100)
- Use type hints where possible
- Write docstrings for all public functions/classes
- Keep functions focused and small

**Docstring Format:**
```python
def function_name(param1: str, param2: int) -> bool:
    """
    Brief description of function.
    
    Longer description if needed with more details about what
    the function does and any important notes.
    
    Args:
        param1: Description of first parameter
        param2: Description of second parameter
        
    Returns:
        Description of return value
        
    Raises:
        ExceptionType: When this exception is raised
    """
    pass
```

**UI Code:**
- Keep UI logic separate from business logic
- Use Qt best practices
- Maintain consistent styling with existing code
- Test UI changes on multiple screen sizes

#### Testing Guidelines

- Write unit tests for all new functions
- Write integration tests for workflows
- Aim for 80%+ code coverage
- Test edge cases and error conditions
- Mock external dependencies (file system, hardware)

Example test:
```python
def test_file_signature_detection():
    """Test that JPEG files are correctly identified."""
    db = FileSignatureDatabase()
    jpeg_header = bytes([0xFF, 0xD8, 0xFF, 0xE0])
    
    sig = db.identify_file(jpeg_header)
    
    assert sig is not None
    assert sig.extension == "jpg"
    assert sig.mime_type == "image/jpeg"
```

### Documentation

#### Documentation Requirements

- Update README.md if adding user-facing features
- Update docs/ for detailed feature documentation
- Add docstrings to all public APIs
- Include examples for complex features
- Update CHANGELOG.md

#### Writing Documentation

- Use clear, simple language
- Include code examples
- Add screenshots for UI features
- Explain the "why" not just the "how"
- Keep it up to date with code changes

### Pull Request Process

1. **Ensure CI passes** - All tests and checks must pass
2. **Update documentation** - Include relevant docs updates
3. **Add tests** - New features need tests
4. **Request review** - At least one maintainer review required
5. **Address feedback** - Make requested changes promptly
6. **Keep it focused** - One feature/fix per PR
7. **Rebase if needed** - Keep history clean

#### PR Checklist

- [ ] Code follows style guidelines
- [ ] Tests added and passing
- [ ] Documentation updated
- [ ] Commit messages are clear
- [ ] No merge conflicts
- [ ] CI/CD checks pass
- [ ] Reviewed by maintainer

## Development Tips

### Running Specific Tests

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_core.py

# Run specific test
pytest tests/test_core.py::test_file_signature_database

# Run with coverage
pytest --cov=src/recoveryforge tests/
```

### Debugging

```bash
# Run with verbose logging
python -m src.recoveryforge --log-level DEBUG

# Run specific module
python -c "from recoveryforge.core import DiskScanner; s = DiskScanner(); print(s.scan_drives())"
```

### Performance Testing

```bash
# Profile code
python -m cProfile -o profile.stats script.py
python -c "import pstats; p = pstats.Stats('profile.stats'); p.sort_stats('cumtime'); p.print_stats(20)"

# Memory profiling
python -m memory_profiler script.py
```

## Project Structure

```
RecoveryForge/
├── src/recoveryforge/      # Main package
│   ├── core/              # Core recovery engine
│   ├── ui/                # User interface
│   ├── analysis/          # Content analysis
│   ├── intelligence/      # Smart features
│   ├── tools/             # Utilities and tools
│   └── utils/             # Helper functions
├── tests/                 # Test suite
├── docs/                  # Documentation
├── config/                # Configuration files
├── examples/              # Example scripts
└── assets/                # Icons and resources
```

## Getting Help

- **Questions**: Use [GitHub Discussions](https://github.com/r22gir/RecoveryForge/discussions)
- **Bugs**: File an [Issue](https://github.com/r22gir/RecoveryForge/issues)
- **Chat**: Join our community chat (link if available)

## Recognition

Contributors will be:
- Listed in CONTRIBUTORS.md
- Mentioned in release notes
- Thanked in the README

Thank you for contributing to RecoveryForge! 🎉
