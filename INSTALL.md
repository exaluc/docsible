# Installation & Development Guide

This document explains how to install and develop Docsible using different Python package managers.

## Installation

### Using uv (Recommended - Fast!)

```bash
# Install docsible
uv pip install docsible

# Or install from source
uv pip install -e .

# Install with specific Python version
uv pip install --python 3.11 docsible
```

### Using pip

```bash
# Install from PyPI
pip install docsible

# Or install from source
pip install -e .
```

### Using Poetry (Traditional)

```bash
# Install dependencies
poetry install

# Run docsible
poetry run docsible --help
```

## Python Version Management with pyenv

### Setup pyenv

```bash
# Install Python 3.11 (or any version >=3.10)
pyenv install 3.11.0

# Set local Python version
pyenv local 3.11.0

# Verify Python version
python --version
```

### Use with uv + pyenv

```bash
# Set Python version
pyenv local 3.11.0

# Install docsible with uv
uv pip install -e .

# Run docsible
docsible --help
```

### Use with pip + pyenv

```bash
# Set Python version
pyenv local 3.11.0

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install docsible
pip install -e .

# Run docsible
docsible --help
```

## Development Setup

### Using uv (Fastest)

```bash
# Clone this fork
git clone https://github.com/jier/docsible.git
cd docsible

# Install the project and its development dependency group
uv sync --group dev

# Run tests
uv run pytest tests/

# Run docsible
uv run docsible document role --role tests/fixtures/simple_role --graph
```

### Using pip (Traditional)

```bash
# Clone this fork
git clone https://github.com/jier/docsible.git
cd docsible

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in editable mode
pip install -e .

# For tests, linting, and builds, use the uv development setup above.

# Run docsible
docsible document role --role tests/fixtures/simple_role --graph
```

## Requirements

- **Python**: 3.10 or higher
- **Dependencies**:
  - click >= 8.1.7
  - PyYAML >= 6.0.1
  - Jinja2 >= 3.1.2
  - pydantic >= 2.0.0

## Tool Comparison

| Tool | Speed | Use Case |
|------|-------|----------|
| **uv** | ⚡ Fastest | Modern development, CI/CD |
| **pip** | 🐢 Slower | Traditional, simple setups |

## Supported Python Versions

- Python 3.10
- Python 3.11
- Python 3.12

## Verifying Installation

```bash
# Check version
docsible --version

# Test with help
docsible --help

# Run interactive setup wizard
docsible init
```

## Available Commands

The following commands are available in this release:

| Command | Description |
|---------|-------------|
| `docsible document role` | Generate documentation for an Ansible role |
| `docsible analyze role` | Analyze a role without writing any files |
| `docsible validate role` | Validate a role with exit codes suitable for CI |
| `docsible scan collection` | Scan and document all roles in a collection |
| `docsible suppress` | Manage suppression rules (silence specific warnings) |
| `docsible init` | Interactive setup wizard for configuration |

**Presets:** Use `--preset personal|team|enterprise|consultant` to apply a predefined configuration profile to any command.

## Troubleshooting

### uv command not found

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or with pip
pip install uv
```

### pyenv command not found

```bash
# Install pyenv on macOS/Linux
curl https://pyenv.run | bash

# Or on macOS with Homebrew
brew install pyenv

# Add to shell (add to ~/.bashrc or ~/.zshrc)
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"
```

### Import errors

```bash
# Make sure you're in the right environment
which python
python -c "import docsible; print(docsible.__file__)"

# Reinstall in editable mode
pip install -e .
```

## CI/CD Integration

### Using uv in GitHub Actions

```yaml
- name: Set up Python
  uses: actions/setup-python@v5
  with:
    python-version: '3.11'

- name: Install uv
  run: pip install uv

- name: Check lockfile sync
  run: uv lock --check

- name: Install dependencies
  run: uv sync --locked --group dev

- name: Run docsible
  run: uv run docsible document role --role ./my-role --graph
```

### Using pip in GitHub Actions

```yaml
- name: Set up Python
  uses: actions/setup-python@v5
  with:
    python-version: '3.11'

- name: Install dependencies
  run: pip install -e .

- name: Run docsible
  run: docsible document role --role ./my-role --graph
```

## Building from Source

### Using hatchling (Standard)

```bash
# Install build tool
pip install build

# Build wheel and sdist
python -m build

# Install built wheel
pip install dist/docsible-0.9.0-py3-none-any.whl
```


## Performance Optimization

### Caching System

Docsible includes an intelligent caching system that dramatically improves performance on repeated runs:

**Features:**
- **File-level caching**: YAML files cached by modification time
- **Directory-level caching**: Analysis results cached until files change
- **Automatic invalidation**: Cache updates when files are modified
- **Zero configuration**: Works out of the box

**Performance Improvements:**
- Role loading: **4x faster** (75% reduction)
- Complexity analysis: **14x faster** (93% reduction)
- Pattern analysis: **100-1000x faster** (99% reduction)

**Disable Caching (if needed):**
```bash
# Disable caching via environment variable
export DOCSIBLE_DISABLE_CACHE=1
docsible role --role ./my-role

# Or for a single command
DOCSIBLE_DISABLE_CACHE=1 docsible role --role ./my-role
```

**Cache Management:**
Caches are stored in memory and automatically cleared when:
- Files are modified (detected via mtime)
- Python process exits
- Maximum cache size is reached (LRU eviction)

For advanced caching configuration, see [CACHING_IMPLEMENTATION_GUIDE.md](CACHING_IMPLEMENTATION_GUIDE.md).

## See Also

- [README.md](README.md) - Main documentation
- [CONFIGURATION.md](CONFIGURATION.md) - Project structure configuration
- [CACHING_IMPLEMENTATION_GUIDE.md](CACHING_IMPLEMENTATION_GUIDE.md) - Caching system guide
- [pyproject.toml](pyproject.toml) - Package configuration
