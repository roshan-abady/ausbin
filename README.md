# Australian Business Names API Toolkit

A Python toolkit for accessing and analyzing Australian Business Names registry data.

## Getting Started

### Initial Setup

Run the setup script to install dependencies:

```bash
bash setup.sh
```

This will:
- Create a Python virtual environment in the `venv` directory
- Install all required dependencies from `requirements.txt`
- Run tests to verify the installation

### Activating the Virtual Environment

After running the setup script, you need to activate the virtual environment in your current shell. Choose one of the following options:

#### Option 1: Source the activation script (recommended)

```bash
source activate.sh
```

This will activate the virtual environment and provide helpful information. You'll see `(venv)` in your prompt indicating the environment is active.

#### Option 2: Activate manually

```bash
source venv/bin/activate  # On Windows: source venv\Scripts\activate
```

### Deactivating the Virtual Environment

When you're done working with the toolkit, deactivate the virtual environment:

```bash
deactivate
```

## Documentation

This toolkit provides two main interfaces:

### Command Line Interface (CLI)

For details on using the CLI tool, see [CLI Guide](CLI_GUIDE.md).

```bash
# Example CLI command:
./run_cli.sh search --status 'Registered' --display chart
```

### Streamlit Web Application

For details on running and using the Streamlit web application, see [Streamlit Guide](STREAMLIT_GUIDE.md).

```bash
# Run the Streamlit web app:
./run_streamlit.sh

# Run with a custom port:
./run_streamlit.sh 8502
```

## Usage Examples

Once the virtual environment is activated, you can use the following commands:

```bash
# Run tests
python -m pytest tests/ -v

# Run integration tests
python tests/integration_test.py
```

## Development

### Project Structure

- `src/` - Source code
- `tests/` - Unit and integration tests
- `venv/` - Virtual environment (created by setup.sh)

### Running Tests

```bash
python -m pytest tests/ -v --cov=. --cov-report=html
```

This will run all tests and generate a coverage report in the `htmlcov/` directory.

### Code Quality Checks

The project includes several code quality tools:

```bash
# Check formatting with Black
python -m black . --check

# Run linting with Flake8
python -m flake8 .

# Type checking with MyPy
python -m mypy . --ignore-missing-imports
```
