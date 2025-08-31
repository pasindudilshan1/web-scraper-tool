#!/usr/bin/env python3
"""
Web Scraper Tool Setup Script
This script helps set up the entire web scraper tool including AWS Lambda and local GUI
"""

import os
import sys
import subprocess
import json
from pathlib import Path

class WebScraperSetup:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.lambda_dir = self.project_root / "lambda"
        self.gui_dir = self.project_root / "gui"
        
    def check_python_version(self):
        """Check if Python 3.8+ is available"""
        if sys.version_info < (3, 8):
            print("❌ Python 3.8+ is required")
            return False
        print("✅ Python version check passed")
        return True
        
    def install_dependencies(self):
        """Install required Python packages"""
        print("📦 Installing dependencies...")
        
        # Install GUI dependencies
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                         check=True, capture_output=True)
            print("✅ Dependencies installed successfully")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install dependencies: {e}")
            return False
            
    def create_directories(self):
        """Create necessary directories"""
        directories = [
            "downloads",
            "logs",
            "tests",
            "docs"
        ]
        
        for directory in directories:
            dir_path = self.project_root / directory
            dir_path.mkdir(exist_ok=True)
            print(f"✅ Created directory: {directory}")
            
    def create_test_files(self):
        """Create test files for validation"""
        test_content = '''
import unittest
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

class TestWebScraper(unittest.TestCase):
    def test_lambda_import(self):
        """Test that Lambda function can be imported"""
        try:
            from lambda.lambda_function import lambda_handler
            self.assertTrue(callable(lambda_handler))
        except ImportError as e:
            self.fail(f"Failed to import lambda_function: {e}")
            
    def test_gui_import(self):
        """Test that GUI can be imported"""
        try:
            from gui.web_scraper_gui import WebScraperGUI
            self.assertTrue(callable(WebScraperGUI))
        except ImportError as e:
            self.fail(f"Failed to import GUI: {e}")

if __name__ == '__main__':
    unittest.main()
'''
        
        test_file = self.project_root / "tests" / "test_web_scraper.py"
        test_file.write_text(test_content)
        print("✅ Created test file")
        
    def create_documentation(self):
        """Create documentation files"""
        readme_content = """# Web Scraper Tool

A comprehensive web scraping solution with AWS Lambda backend and local Tkinter GUI.

## Architecture

- **AWS Lambda Function**: Handles web scraping and data processing
- **Local GUI**: Tkinter-based interface for user interaction
- **CSV Export**: Generates structured CSV files from scraped data

## Features

- 🕷️ **Web Scraping**: Extracts data from any website
- 🧹 **Data Cleaning**: Automatically cleans and structures scraped data
- 📊 **CSV Export**: Generates multiple CSV files with different data views
- 🖥️ **GUI Interface**: Easy-to-use local application
- ⚡ **AWS Lambda**: Scalable serverless backend

## Quick Start

### 1. Setup Local Environment
```bash
python setup.py --local
```

### 2. Deploy AWS Lambda
```bash
cd lambda
./deploy_lambda.sh
```

### 3. Update Configuration
Edit `gui/config.py` with your AWS Lambda endpoint

### 4. Run GUI
```bash
python gui/web_scraper_gui.py
```

## File Structure

```
web-scraper-tool/
├── lambda/              # AWS Lambda function
├── gui/                 # Local GUI application
├── tests/               # Test files
├── docs/               # Documentation
├── downloads/          # Downloaded CSV files
├── requirements.txt    # Python dependencies
└── setup.py           # Setup script
```

## Usage

1. **Start GUI**: Run `python gui/web_scraper_gui.py`
2. **Enter URL**: Paste any website URL
3. **Scrape**: Click "Start Scraping"
4. **Download**: Save CSV files to your computer

## AWS Lambda Setup

1. Create Lambda function in AWS Console
2. Upload `lambda/web-scraper-lambda.zip`
3. Set handler: `lambda_function.lambda_handler`
4. Set runtime: Python 3.11
5. Set timeout: 30 seconds
6. Set memory: 512 MB
7. Create API Gateway trigger

## Support

For issues or questions, please check the documentation in the `docs/` folder.
"""
        
        readme_file = self.project_root / "README.md"
        readme_file.write_text(readme_content)
        print("✅ Created README.md")
        
    def run_setup(self):
        """Run complete setup"""
        print("🚀 Starting Web Scraper Tool Setup...")
        print("=" * 50)
        
        steps = [
            ("Checking Python version", self.check_python_version),
            ("Creating directories", self.create_directories),
            ("Installing dependencies", self.install_dependencies),
            ("Creating test files", self.create_test_files),
            ("Creating documentation", self.create_documentation)
        ]
        
        for step_name, step_func in steps:
            print(f"\n📋 {step_name}...")
            if not step_func():
                print(f"❌ Setup failed at: {step_name}")
                return False
        print("\n" + "=" * 50)
        print("✅ Setup completed successfully!")
        print("\n🎯 Next steps:")
        print("1. Deploy AWS Lambda function (see lambda/deploy_lambda.sh)")
        print("2. Update GUI config with your Lambda endpoint")
        print("3. Run: python gui/web_scraper_gui.py")
        return True

if __name__ == "__main__":
    setup = WebScraperSetup()
    success = setup.run_setup()
    sys.exit(0 if success else 1)