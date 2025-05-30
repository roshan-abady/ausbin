#!/bin/bash

# Author: Roshan Abady
# run_streamlit.sh - Launch AUSBIN - Australian Business Names Streamlit App

# Set script directory and app path
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="/Users/Roshan.Abady/Dev/ausbiz"
STREAMLIT_APP="$PROJECT_DIR/src/streamlit_app.py"
VENV_PATH="$PROJECT_DIR/venv"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
ORANGE='\033[38;5;208m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 AUSBIN - Australian Business Names Streamlit App Launcher${NC}"
echo "=================================================="

# Check if the Streamlit app file exists
if [ ! -f "$STREAMLIT_APP" ]; then
    echo -e "${RED}❌ Error: Streamlit app not found at $STREAMLIT_APP${NC}"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "$VENV_PATH" ]; then
    echo -e "${RED}❌ Error: Virtual environment not found at $VENV_PATH${NC}"
    echo -e "${YELLOW}💡 Please create virtual environment first:${NC}"
    echo "   cd $PROJECT_DIR"
    echo "   python3 -m venv venv"
    echo "   source venv/bin/activate"
    echo "   pip install -r requirements.txt"
    exit 1
fi

# Change to project directory
cd "$PROJECT_DIR" || {
    echo -e "${RED}❌ Error: Cannot change to project directory $PROJECT_DIR${NC}"
    exit 1
}

echo -e "${BLUE}📁 Project Directory: $PROJECT_DIR${NC}"
echo -e "${BLUE}🐍 Virtual Environment: $VENV_PATH${NC}"
echo -e "${BLUE}📱 Streamlit App: $STREAMLIT_APP${NC}"
echo ""

# Activate virtual environment
echo -e "${YELLOW}🔧 Activating virtual environment...${NC}"
source "$VENV_PATH/bin/activate" || {
    echo -e "${RED}❌ Error: Failed to activate virtual environment${NC}"
    exit 1
}

# Verify Python environment
echo -e "${YELLOW}🐍 Checking Python environment...${NC}"
which python
python --version

# Check if required packages are installed
echo -e "${YELLOW}📦 Checking required packages...${NC}"
python -c "
import sys
required_packages = ['streamlit', 'plotly', 'pandas', 'requests']
missing_packages = []

for package in required_packages:
    try:
        __import__(package)
        print(f'✅ {package}')
    except ImportError:
        print(f'❌ {package} - MISSING')
        missing_packages.append(package)

if missing_packages:
    print(f'\\n🚨 Missing packages: {missing_packages}')
    print('💡 Run: pip install -r requirements.txt')
    sys.exit(1)
else:
    print('\\n🎉 All required packages are installed!')
"

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Missing required packages. Please install them first.${NC}"
    exit 1
fi

# Set default port
PORT=${1:-8501}

echo ""
echo -e "${GREEN}🌟 Starting Streamlit app...${NC}"
echo -e "${BLUE}📍 URL: http://localhost:$PORT${NC}"
echo -e "${YELLOW}💡 Press Ctrl+C to stop the server${NC}"
echo ""

# Set PYTHONPATH to include the project directory
echo -e "${BLUE}🔄 Setting PYTHONPATH to include project directory...${NC}"
export PYTHONPATH="$PROJECT_DIR:$PYTHONPATH"
echo -e "${BLUE}📁 PYTHONPATH: $PYTHONPATH${NC}"
echo ""

# Launch Streamlit app
streamlit run "$STREAMLIT_APP" --server.port="$PORT" --server.headless=true --server.runOnSave=true

# Cleanup message
echo ""
echo -e "${YELLOW}👋 Streamlit app stopped${NC}"
