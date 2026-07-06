#!/bin/bash

# Setup script for job application automation

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_info "Setting up job application automation environment..."

# Check Python
if ! command -v python3 &> /dev/null; then
    print_error "Python3 is not installed. Please install Python3 first."
    exit 1
fi

print_info "Python3 found: $(python3 --version)"

# Check pip
if ! command -v pip3 &> /dev/null; then
    print_error "pip3 is not installed. Please install pip3 first."
    exit 1
fi

print_info "pip3 found: $(pip3 --version)"

# Install Python dependencies
print_info "Installing Python dependencies..."
pip3 install -r requirements.txt

# Check Chrome browser
if command -v google-chrome &> /dev/null; then
    print_info "Chrome browser found: $(google-chrome --version)"
elif command -v chromium-browser &> /dev/null; then
    print_info "Chromium browser found: $(chromium-browser --version)"
else
    print_warning "Chrome/Chromium browser not found. Please install Chrome browser."
    print_info "On Ubuntu/Debian: sudo apt install google-chrome-stable"
    print_info "Or visit: https://www.google.com/chrome/"
fi

# Make scripts executable
chmod +x *.sh
chmod +x *.py

print_info "Running basic tests..."
python3 test_mokahr_automation.py

if [ $? -eq 0 ]; then
    print_info "✅ Setup completed successfully!"
    echo ""
    print_info "Next steps:"
    echo "1. Edit job_config_template.json with your personal information"
    echo "2. Test with: ./run_job_application.sh --test"
    echo "3. Run automation: ./run_job_application.sh -u 'URL' -f 'resume.pdf'"
else
    print_error "❌ Setup failed. Please check the errors above."
    exit 1
fi