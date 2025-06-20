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
