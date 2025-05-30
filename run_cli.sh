#!/bin/bash
# Author: Roshan Abady
# run_cli.sh - Script to run the CLI tool with proper environment settings
# AUSBIN - Australian Business Names CLI Launcher

# Set script directory and app path
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="/Users/Roshan.Abady/Dev/ausbiz"
CLI_APP="$PROJECT_DIR/src/cli.py"
VENV_PATH="$PROJECT_DIR/venv"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
ORANGE='\033[38;5;208m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 AUSBIN - Australian Business Names CLI Launcher${NC}"
echo "=================================================="

# Check if the CLI app file exists
if [ ! -f "$CLI_APP" ]; then
    echo -e "${RED}❌ Error: CLI app not found at $CLI_APP${NC}"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "$VENV_PATH" ]; then
    echo -e "${YELLOW}⚠️ Virtual environment not found. Running setup first...${NC}"
    bash "$PROJECT_DIR/setup.sh"
    
    # Check again if venv was created
    if [ ! -d "$VENV_PATH" ]; then
        echo -e "${RED}❌ Failed to create virtual environment. Please check setup.sh for errors.${NC}"
        exit 1
    fi
fi

# Change to project directory
cd "$PROJECT_DIR" || {
    echo -e "${RED}❌ Error: Cannot change to project directory $PROJECT_DIR${NC}"
    exit 1
}

# Activate virtual environment
echo -e "${YELLOW}🔧 Activating virtual environment...${NC}"
source "$VENV_PATH/bin/activate" || {
    echo -e "${RED}❌ Error: Failed to activate virtual environment${NC}"
    exit 1
}

# Set PYTHONPATH to include the project directory
echo -e "${BLUE}🔄 Setting PYTHONPATH to include project directory...${NC}"
export PYTHONPATH="$PROJECT_DIR:$PYTHONPATH"

# Run the CLI app with all arguments passed to this script
echo -e "${GREEN}🚀 Running CLI app...${NC}"
python "$CLI_APP" "$@"

# Show command help if no arguments provided
if [ $# -eq 0 ]; then
    echo -e "${YELLOW}💡 Tip: You can specify commands, e.g.:${NC}"
    echo -e "   ./run_cli.sh search \"ACME\" --display barchart"
    echo -e "   ./run_cli.sh stats"
    echo -e "   ./run_cli.sh --help"
    echo ""
    echo -e "${BLUE}📘 For more details, see CLI_GUIDE.md${NC}"
    echo -e "${ORANGE}  For the best User experience, use the Streamlit app:${NC}"
    echo -e "  ./run_streamlit.sh                # Run the Streamlit web app"
fi

# Deactivate virtual environment
deactivate
