# Author: Roshan Abady
# AUSBIN - Australian Business Names Streamlit Guide

This guide explains how to use the Streamlit web application for exploring the Australian Business Names registry.

## Setup and Environment

Before running the Streamlit app, make sure you have set up the environment:

```bash
# Set up the environment (if not already done)
bash setup.sh

# Activate the virtual environment
source venv/bin/activate
```

## Running the Streamlit App

There are two ways to run the Streamlit application:

### Option 1: Using the run_streamlit.sh script (Recommended)

This script sets up everything correctly and provides helpful feedback:

```bash
# Run with default port (8501)
./run_streamlit.sh

# Run with custom port
./run_streamlit.sh 8502
```

### Option 2: Running directly with Streamlit

If you have the virtual environment activated:

```bash
# First set the Python path
export PYTHONPATH=$PYTHONPATH:/Users/Roshan.Abady/Dev/ausbiz

# Then run the app
streamlit run src/streamlit_app.py
```

## Accessing the Web Application

Once running, the Streamlit app can be accessed at:
- Local URL: http://localhost:8501
- Network URL: http://your-ip-address:8501 (accessible from other devices on your network)

## Features of the Web Application

### Search Business Names

The app provides an interactive interface to:
- Search by business name
- Filter by registration status
- Set result limits
- View results in different formats (table, charts)

### Visualization and Analytics

- View distributions of business statuses
- Analyze registration trends over time
- Explore geographic distributions
- Generate word clouds of common business name terms

### Export Options

- Download search results as CSV
- Save visualizations as images

## Troubleshooting Common Issues

### The app shows an import error

This can happen if the environment isn't properly set up. The app may show errors like:

```
ImportError: attempted relative import with no known parent package
```

Use the provided script which correctly sets the PYTHONPATH:

```bash
./run_streamlit.sh
```

If you need to run the app directly with streamlit, make sure to set the PYTHONPATH first:

```bash
export PYTHONPATH="/Users/Roshan.Abady/Dev/ausbiz:$PYTHONPATH"
streamlit run src/streamlit_app.py
```

### The app can't connect to the API

- Check your internet connection
- Verify that the API endpoint is accessible
- The app has built-in retry mechanisms but persistent connection issues may indicate API downtime

### The app is slow to load data

- Consider using filters to reduce the result set
- For large queries, the app implements caching to improve performance on subsequent runs

## Additional Resources

For more information on using Streamlit apps or the Business Names API:
- Streamlit Documentation: https://docs.streamlit.io/
- data.gov.au API Documentation: https://data.gov.au/data/api/

If you encounter issues not covered here, please refer to the project documentation or submit an issue on the project repository.
