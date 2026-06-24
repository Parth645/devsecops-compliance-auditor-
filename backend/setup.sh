#!/bin/bash

# Setup script for AI-powered Compliance Auditor with Policy Processing
echo "Setting up AI-powered Compliance Auditor with Policy Processing..."

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is required but not installed. Please install Python 3.8+."
    exit 1
fi

echo "Python found: $(python3 --version)"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install all requirements from requirements.txt
echo "Installing all requirements..."
pip install -r requirements.txt

# Install AI/ML dependencies with specific versions
echo "Installing AI/ML dependencies..."
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Download spaCy English model
echo "Downloading spaCy English model..."
python3 -m spacy download en_core_web_sm

# Download NLTK data
echo "Downloading NLTK data..."
python3 -c "
import nltk
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')
nltk.download('vader_lexicon')
"

# Create necessary directories
echo "Creating necessary directories..."
mkdir -p policies
mkdir -p policies/sample_policies
mkdir -p repos
mkdir -p logs

# Set up logging directory
touch logs/compliance_auditor.log

# Make demo script executable
chmod +x demo_enhanced_ai.py

# Test basic functionality
echo "Testing basic functionality..."
python3 -c "
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'ai engine'))

try:
    from policy_processor import PolicyProcessor
    from repository_scanner import RepositoryScanner
    from compliance_analyzer import ComplianceAnalyzer
    print('✓ All AI components imported successfully')
except Exception as e:
    print(f'⚠️  Warning: {e}')
    print('Some AI components may not be available, but basic functionality should work')
"

echo ""
echo "Setup completed successfully!"
echo ""
echo "Next steps:"
echo "1. Run the demo: python3 demo_enhanced_ai.py"
echo "2. Start the API server: python3 main.py"
echo "3. Import your legal policies into the 'policies' folder"
echo "4. Use the API endpoints to scan repositories for compliance"
echo ""
echo "API Documentation available at: http://localhost:8000/docs"
echo "New Endpoints:"
echo "  - POST /policies/import - Import legal policies"
echo "  - POST /scan/repository - Scan repository with AI rules"
echo "  - POST /scan/comprehensive - Full compliance analysis"

echo "Setup complete! To run the server:"
echo "1. Activate the virtual environment: source venv/bin/activate"
echo "2. Run the server: python main.py"
echo "3. Visit http://localhost:8000/docs for API documentation"