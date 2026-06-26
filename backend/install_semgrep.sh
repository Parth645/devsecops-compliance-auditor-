#!/bin/bash

echo "=========================================="
echo "Semgrep Installation Script"
echo "=========================================="
echo ""

# Check if pip is available
if ! command -v pip &> /dev/null; then
    echo "❌ pip not found. Please install Python and pip first."
    exit 1
fi

echo "📦 Installing Semgrep..."
pip install semgrep

# Verify installation
if command -v semgrep &> /dev/null; then
    echo ""
    echo "✅ Semgrep installed successfully!"
    echo ""
    semgrep --version
    echo ""
    echo "🎉 You're ready to use Semgrep!"
    echo ""
    echo "Next steps:"
    echo "  1. Run test: python test_semgrep.py"
    echo "  2. Run full scan: python test_real_scan.py"
    echo "  3. Read docs: cat SEMGREP_INTEGRATION.md"
else
    echo ""
    echo "❌ Installation failed. Try manual installation:"
    echo "   pip install semgrep"
    echo ""
    echo "Or using Homebrew (macOS):"
    echo "   brew install semgrep"
    exit 1
fi
