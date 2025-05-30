#!/bin/bash
# Author: Roshan Abady
# activate.sh - Activates the virtual environment for the current shell session
# AUSBIN - Australian Business Names Virtual Environment Activator
# NOTE: This script must be sourced, not executed: source activate.sh

# Add colors for better readability
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
ORANGE='\033[38;5;208m'
NC='\033[0m' # No Color

# Detect if the script is being sourced or executed
(return 0 2>/dev/null) && SOURCED=1 || SOURCED=0

if [ $SOURCED -eq 0 ]; then
    echo -e "${RED}❌ ERROR: This script must be sourced, not executed.${NC}"
    echo -e "   Please run it using: ${YELLOW}source activate.sh${NC}"
    echo -e "   This ensures the virtual environment remains active in your current shell."
    exit 1
fi

# Get script directory and set paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PATH="$SCRIPT_DIR/venv"

# Check if virtual environment exists
if [ ! -d "$VENV_PATH" ]; then
    echo -e "${YELLOW}⚠️ Virtual environment not found. Running setup first...${NC}"
    bash setup.sh
    
    # Check again if venv was created
    if [ ! -d "$VENV_PATH" ]; then
        echo -e "${RED}❌ Failed to create virtual environment. Please check setup.sh for errors.${NC}"
        return 1
    fi
fi

# Activate the virtual environment in the current shell
echo -e "${BLUE}🔄 Activating virtual environment...${NC}"
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    source "$VENV_PATH/Scripts/activate"
else
    source "$VENV_PATH/bin/activate"
fi

# Verify activation
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo -e "${RED}❌ Failed to activate virtual environment.${NC}"
    return 1
fi

# Set PYTHONPATH to include project directory
export PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH"

# Success message with clear visual indicator
echo -e "${GREEN}✅ Virtual environment activated! $(python --version)${NC}"
echo -e "${GREEN}🟢 Your prompt should now show (venv) to indicate the active environment${NC}"
echo ""
echo -e "${BLUE}📋 Available commands:${NC}"
echo "  python -m pytest tests/          # Run all tests"
echo "  python run_tests.py              # Run all tests (alternative)"
echo "  python src/cli.py --help         # Show CLI help"
echo -e "${ORANGE}  For the best User experience, use the Streamlit app:${NC}"
echo -e "  ./run_streamlit.sh                # Run the Streamlit web app"
echo ""
echo -e "${YELLOW}💡 To deactivate the virtual environment, type: deactivate${NC}"
