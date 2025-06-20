# Blog Post Generator

A Flask web application that helps generate blog posts from scientific papers using PubMed queries and AI-powered summarization.

## Features

- Query PubMed for scientific papers from specific journals and date ranges
- Rank papers based on relevance to RNA markers and related keywords
- Upload PDF papers and generate AI-powered blog post summaries
- Interactive web interface for easy use

## Prerequisites

- Python 3.7 or higher
- Anthropic API key (for PDF summarization feature)

## Installation

1. Clone the repository

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

3. Get your Anthropic API key:
   - Visit [Anthropic Console](https://console.anthropic.com/)
   - Create an account and generate an API key
   - Keep this key secure and don't share it

## Usage

1. Run the application:
```bash
python3 app.py
```

2. When prompted, enter your Anthropic API key. The key will be hidden as you type for security.

3. Open your web browser and navigate to `http://localhost:5000`

4. Use the web interface to:
   - Query PubMed for papers
   - Rank papers by relevance
   - Upload PDFs for AI-powered summarization

## Security

- **API Key Security**: The application prompts for your API key when it starts, ensuring it's never stored in the code or committed to version control
- **Input Validation**: All user inputs are validated to prevent security issues
- **No Persistent Storage**: API keys are only stored in memory during runtime

## File Structure

- `app.py` - Main Flask application with PubMed query and ranking functionality
- `summarizer.py` - PDF processing and AI summarization logic
- `templates/` - HTML templates for the web interface
- `requirements.txt` - Python dependencies
- `.gitignore` - Prevents sensitive files from being committed

## API Key Management

The application uses the `getpass` module to securely prompt for your API key:
- The key is hidden as you type
- It's only stored in memory during runtime
- It's never written to disk or logged
- You'll need to enter it each time you start the application

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Ensure no API keys or sensitive data are committed
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 
