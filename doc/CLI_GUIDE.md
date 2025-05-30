# Author: Roshan Abady
# AUSBIN - Australian Business Names CLI Guide

This guide explains how to use the Command Line Interface (CLI) for the Australian Business Names API toolkit.

## Setup and Environment

Before using the CLI, make sure you have set up and activated the virtual environment:

```bash
# Set up the environment (if not already done)
bash setup.sh

# Activate the virtual environment
source venv/bin/activate

# Alternative: Use the convenience script
source activate.sh
```

## Quick Start

The easiest way to run the CLI tool is to use the provided script:

```bash
# Run with no arguments to see help
./run_cli.sh

# Run specific commands
./run_cli.sh search "ACME" --display barchart
./run_cli.sh stats
./run_cli.sh explore --pattern "PTY"
```

The script automatically:
- Activates the virtual environment
- Sets the correct PYTHONPATH
- Runs the CLI tool with all provided arguments

## CLI Commands

The CLI tool provides several commands for searching and analyzing Australian Business Names data.

### Basic Commands

```bash
# Show help and available commands
python src/cli.py --help

# Search with specific status
python src/cli.py search --status "Registered"

# Find similar business names
python src/cli.py similar "ACME PTY LTD" --limit 10

# Get statistics about the dataset
python src/cli.py stats
```

### Search Command

The search command allows you to find business names based on various criteria:

```bash
# Basic search with default parameters
python src/cli.py search

# Search with status filter
python src/cli.py search --status "Registered"

# Search with name pattern
python src/cli.py search --name "TECH"

# Limit results
python src/cli.py search --limit 20

# Change output format
python src/cli.py search --display table
python src/cli.py search --display json
python src/cli.py search --display chart
```

### Similar Names Search

Find business names similar to a given query:

```bash
# Basic similarity search
python src/cli.py similar "ACME PTY LTD"

# Set similarity threshold (0-100)
python src/cli.py similar "ACME PTY LTD" --threshold 80

# Limit results
python src/cli.py similar "ACME PTY LTD" --limit 5
```

### Statistics and Analysis

```bash
# Get overall statistics
python src/cli.py stats

# Get statistics for a specific field
python src/cli.py stats --field "BN_STATUS"

# Visualize statistics
python src/cli.py stats --display chart
```

## Advanced Usage

### Saving Results

Save search results to a file:

```bash
# Save as CSV
python src/cli.py search --name "TECH" --output results.csv

# Save as JSON
python src/cli.py search --name "TECH" --output results.json --format json
```

### Using SQL Queries

For advanced users, direct SQL queries are supported:

```bash
python src/cli.py sql "SELECT BN_NAME, BN_STATUS FROM \"55ad4b1c-5eeb-44ea-8b29-d410da431be3\" WHERE BN_STATUS = 'Registered' LIMIT 10"
```

## Troubleshooting

If you encounter any issues:

1. Make sure the virtual environment is activated (you should see `(venv)` in your prompt)
2. Check your internet connection as the CLI tool connects to the data.gov.au API
3. For connection issues, verify that the API endpoint is accessible

For more information, refer to the project documentation or submit an issue on the project repository.
