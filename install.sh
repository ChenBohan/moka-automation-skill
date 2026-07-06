#!/bin/bash

# Mokahr Automation Skill Installation Script
# Mokahr自动化技能安装脚本

echo "🤖 Installing Mokahr Automation Skill..."
echo "======================================"

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SKILL_DIR"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is required but not installed"
    exit 1
fi

echo "✅ Python3 found: $(python3 --version)"

# Install Python dependencies
echo "📦 Installing Python dependencies..."
if [ -f "requirements.txt" ]; then
    pip3 install -r requirements.txt
    echo "✅ Python dependencies installed"
else
    echo "⚠️  requirements.txt not found"
fi

# Make scripts executable
echo "🔧 Setting up executable permissions..."
chmod +x skill_manager.py
chmod +x scripts/*.sh
chmod +x core/*.py
chmod +x utils/*.py

echo "✅ Permissions set"

# Run setup script if exists
if [ -f "scripts/setup.sh" ]; then
    echo "⚙️  Running setup script..."
    bash scripts/setup.sh
fi

# Create symlink for easy access
SYMLINK_PATH="/usr/local/bin/mokahr-skill"
if [ ! -f "$SYMLINK_PATH" ] && [ -w "/usr/local/bin" ]; then
    echo "🔗 Creating system symlink..."
    sudo ln -sf "$SKILL_DIR/skill_manager.py" "$SYMLINK_PATH"
    echo "✅ You can now use 'mokahr-skill' command globally"
fi

# Verify installation
echo "🧪 Verifying installation..."
python3 skill_manager.py info > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ Installation verified successfully!"
else
    echo "⚠️  Installation verification failed"
fi

echo ""
echo "🎉 Installation Complete!"
echo "========================"
echo ""
echo "📋 Quick Start:"
echo "  python3 skill_manager.py info      # Show skill information"
echo "  python3 skill_manager.py install   # Install dependencies"
echo "  python3 skill_manager.py run       # Run automation"
echo ""
echo "📚 Documentation: docs/USER_GUIDE_FINAL.md"
echo "🔧 Configuration: configs/"
echo ""
echo "Ready to automate mokahr.com job applications! 🚀"