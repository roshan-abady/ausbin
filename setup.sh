#!/bin/bash
# Author: Roshan Abady
# setup.sh - Fixed paths
# AUSBIN - Australian Business Names CLI Tool (Python 3)

echo "🚀 AUSBIN - Australian Business Names CLI Tool (Python 3)..."

# Check Python 3 installation
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Display Python version
echo "Using Python version:"
python3 --version

# Create virtual environment with Python 3
echo "Creating Python 3 virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

# Upgrade pip
echo "Upgrading pip..."
python -m pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
python -m pip install -r requirements.txt

# Create tests directory if it doesn't exist
mkdir -p tests
touch tests/__init__.py

# Run unit tests
echo "Running unit tests..."
python -m pytest tests/ -v --cov=. --cov-report=html

# Run integration tests (correct path)
echo "Running integration tests..."
python tests/integration_test.py

# Test CLI functionality
echo "Testing CLI functionality..."
python cli.py --help

echo "✅ Setup complete!"
echo ""
echo "⚠️  IMPORTANT: The virtual environment needs to be activated in your current shell."
echo "   To activate it, run one of these commands:"
echo "   source activate.sh          # Recommended: provides helpful information"
echo "   source venv/bin/activate    # Standard activation"
echo ""
echo "   After activation, you'll see (venv) in your prompt, indicating the environment is active."
echo ""
echo "Usage examples (run these after activating the virtual environment):"
echo "  python tests/integration_test.py  # Run integration tests"
echo "  python -m pytest tests/ -v       # Run unit tests"
echo "  python cli.py search --help       # CLI help"
echo "  python cli.py search --status 'Registered' --display chart"
echo "  python cli.py similar 'ACME PTY LTD' --limit 10"
ORANGE='\033[38;5;208m'
echo -e "${ORANGE}  For the best User experience, use the Streamlit app:${NC}"
echo "  ./run_streamlit.sh                # Run the Streamlit web app"
echo ""