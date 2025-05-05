# Spreadsheet Chat Application

A spreadsheet-like application that uses natural language chat interaction to manipulate data. The application allows users to:
- Load CSV files into a SQLite database
- Query data using natural language
- Get AI-generated SQL queries
- View and analyze data

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create a `.env` file with your OpenAI API key:
```
OPENAI_API_KEY=your_api_key_here
```

3. Run the application:
```bash
python src/main.py
```

## Features

- CSV file loading and automatic table creation
- Natural language to SQL query conversion
- Interactive chat interface
- Schema conflict resolution
- Error logging

## Usage

1. Start the application
2. Load a CSV file using the command: `load <filename.csv>`
3. Ask questions about your data in natural language
4. View results and generated SQL queries 