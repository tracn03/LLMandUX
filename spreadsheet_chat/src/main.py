import os
import sqlite3
import pandas as pd
from openai import OpenAI
from dotenv import load_dotenv
import logging
from typing import Optional, Dict, List
import re

# Set up logging
logging.basicConfig(
    filename='error_log.txt',
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class SpreadsheetChat:
    def __init__(self):
        load_dotenv()
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.conn = sqlite3.connect(':memory:')
        self.cursor = self.conn.cursor()
        self.tables: Dict[str, pd.DataFrame] = {}

    def load_csv(self, filename: str) -> bool:
        """Load a CSV file into SQLite database."""
        try:
            # Read CSV file
            df = pd.read_csv(filename)
            table_name = os.path.splitext(os.path.basename(filename))[0]
            
            # Check if table exists
            self.cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
            if self.cursor.fetchone():
                choice = input(f"Table '{table_name}' already exists. Overwrite (o), Rename (r), or Skip (s)? ")
                if choice.lower() == 'r':
                    table_name = input("Enter new table name: ")
                elif choice.lower() == 's':
                    return False
            
            # Store DataFrame and create table
            self.tables[table_name] = df
            df.to_sql(table_name, self.conn, if_exists='replace', index=False)
            return True
            
        except Exception as e:
            logging.error(f"Error loading CSV file {filename}: {str(e)}")
            return False

    def get_schema(self) -> str:
        """Get schema information for all tables."""
        schema = []
        for table_name in self.tables.keys():
            self.cursor.execute(f"PRAGMA table_info({table_name})")
            columns = self.cursor.fetchall()
            column_info = [f"{col[1]} ({col[2]})" for col in columns]
            schema.append(f"{table_name} ({', '.join(column_info)})")
        return "\n".join(schema)

    def generate_sql(self, query: str) -> Optional[str]:
        """Generate SQL query from natural language using OpenAI."""
        try:
            schema = self.get_schema()
            prompt = f"""You are an AI assistant tasked with converting user queries into SQL statements. 
            The database uses SQLite and contains the following tables:
            {schema}
            
            User Query: "{query}"
            
            Your task is to:
            1. Generate a SQL query that accurately answers the user's question.
            2. Ensure the SQL is compatible with SQLite syntax.
            3. Provide a short comment explaining what the query does.
            
            Output Format:
            - SQL Query
            - Explanation
            """
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a SQL expert assistant."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logging.error(f"Error generating SQL: {str(e)}")
            return None

    def execute_query(self, sql: str) -> Optional[pd.DataFrame]:
        """Execute SQL query and return results as DataFrame."""
        try:
            return pd.read_sql_query(sql, self.conn)
        except Exception as e:
            logging.error(f"Error executing query: {str(e)}")
            return None

    def chat_interface(self):
        """Main chat interface loop."""
        print("Welcome to Spreadsheet Chat!")
        print("Available commands:")
        print("- load <filename.csv>: Load a CSV file")
        print("- list: List all loaded tables")
        print("- exit: Exit the application")
        print("Or ask a question about your data in natural language")
        
        while True:
            user_input = input("\nWhat would you like to do? ").strip()
            
            if user_input.lower() == 'exit':
                break
            elif user_input.lower() == 'list':
                print("\nLoaded tables:")
                for table in self.tables.keys():
                    print(f"- {table}")
            elif user_input.startswith('load '):
                filename = user_input[5:].strip()
                if self.load_csv(filename):
                    print(f"Successfully loaded {filename}")
                else:
                    print(f"Failed to load {filename}")
            else:
                # Generate and execute SQL query
                response = self.generate_sql(user_input)
                if response:
                    print("\nGenerated SQL and Explanation:")
                    print(response)
                    
                    # Extract SQL query from response
                    sql_match = re.search(r'SELECT.*?(?=Explanation|$)', response, re.DOTALL)
                    if sql_match:
                        sql = sql_match.group(0).strip()
                        results = self.execute_query(sql)
                        if results is not None:
                            print("\nQuery Results:")
                            print(results)
                else:
                    print("Sorry, I couldn't generate a valid SQL query for your question.")

    def __del__(self):
        """Clean up resources."""
        self.conn.close()

if __name__ == "__main__":
    app = SpreadsheetChat()
    app.chat_interface() 