# Enhanced Web Scraper Tool

## Overview
This project is a powerful web scraping tool with a modern GUI, designed to extract comprehensive data from any website, including SEO, structured data, and content analysis. It leverages an AWS Lambda function for scalable scraping and provides easy CSV downloads for all extracted data.

---

## Features
- Extracts headings, links, images, tables, meta tags, social media, contact info, forms, lists, and more
- SEO analysis and content breakdown
- Download individual or all data files as CSV
- Responsive GUI with scrollable download section
- Uses AWS Lambda for backend scraping (Python)

---

## Prerequisites
- Python 3.10 or newer
- Tkinter (usually included with Python)
- Required Python packages (see `requirements.txt`)
- AWS account (for Lambda deployment)

---

## Setup Instructions

### 1. Clone the Repository
```
git clone <your-repo-url>
cd web-scraper-tool
```

### 2. Install Python Dependencies
Create a virtual environment (recommended):
```
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

### 3. AWS Lambda Function
- The Lambda function code is in `lambda/lambda_function.py`.
- You can deploy it using the AWS Console or AWS CLI.
- Make sure to set the handler to `lambda_function.lambda_handler`.
- Required packages for Lambda are in `lambda/requairments.txt` (install them in your Lambda environment).
- Set up an API Gateway to expose the Lambda as an HTTP endpoint.
- Update the endpoint URL in `gui/web_scraper_gui.py` (see `self.lambda_endpoint`).

#### Example Lambda Deployment (AWS CLI)
```
# Zip deployment package
cd lambda
zip -r deployment.zip lambda_function.py ...

# Create Lambda function
aws lambda create-function --function-name web-scraper-lambda \
  --runtime python3.10 --role <your-iam-role-arn> \
  --handler lambda_function.lambda_handler \
  --zip-file fileb://deployment.zip

# Set up API Gateway and link to Lambda
```

---

## Running the GUI
1. Activate your Python environment.
2. Run the GUI:
```
python gui/web_scraper_gui.py
```

---

## Usage
- Enter a website URL and click "Start Advanced Scraping".
- Wait for progress to complete.
- Download individual CSV files or all at once.
- Analyze results in the GUI tabs.

---

## Troubleshooting
- If scraping fails, check your Lambda logs in AWS CloudWatch.
- Ensure your Lambda endpoint is correct and accessible.
- Make sure all required Python packages are installed.
- For GUI display issues, ensure your screen size is at least 1280x900.

---

## Folder Structure
```
web-scraper-tool/
├── gui/
│   └── web_scraper_gui.py
├── lambda/
│   └── lambda_function.py
│   └── requairments.txt
├── requirements.txt
├── setup.py
└── ...
```

---

## License
MIT License

---

## Contact
For questions or support, open an issue or contact the maintainer.
