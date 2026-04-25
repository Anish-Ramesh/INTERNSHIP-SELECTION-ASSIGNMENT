import sqlite3
import os
import re
import pandas as pd

class QueryDataTool:
    def __init__(self, db_path=None):
        if db_path is None:
            self.db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "database.db")
        else:
            self.db_path = db_path

    def query(self, sql_query: str) -> str:
        """
        Use this tool to execute read-only SQLite queries against structured box-office data.
        
        The database contains a table named 'movies' with the following schema:
        - title (TEXT)
        - year (INTEGER or TEXT)
        - genre (TEXT)
        - budget (TEXT)
        - opening_weekend (REAL)
        - worldwide_gross (REAL)
        - rotten_tomatoes_score (REAL)
        
        TRUNCATION RULES:
        - By default, only the first 10 rows are displayed to conserve context.
        - If you explicitly need more results to fulfill a user's request (e.g., 'List 30 movies'), you MUST include a 'LIMIT X' clause in your SQL.
        - The absolute maximum display limit is 50 rows.
        
        DO NOT use this tool to search for textual reviews, narratives, or real-time web facts.
        Always return the primary key or row identifiers to cite the data row in the db.
        
        Args:
            sql_query (str): A valid SQLite SELECT query.
            
        Returns:
            str: Tabular results in string format or an error message.
        """
        try:
            if not os.path.exists(self.db_path):
                return f"Error: Database not found at {self.db_path}"
                
            # Prevent destructive operations basic check
            if any(forbidden in sql_query.upper() for forbidden in ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE"]):
                return "Error: Only SELECT queries are permitted."

            # Determine requested limit from the query string
            requested_limit = 10
            limit_match = re.search(r'LIMIT\s+(\d+)', sql_query, re.IGNORECASE)
            if limit_match:
                requested_limit = min(int(limit_match.group(1)), 50)

            conn = sqlite3.connect(self.db_path)
            
            # Use pandas to nicely format the tabular output for the LLM
            df = pd.read_sql_query(sql_query, conn)
            conn.close()
            
            if df.empty:
                return "Query executed successfully but returned no results."
                
            # TRUNCATION OPTIMIZATION
            total_rows = len(df)
            
            # Use the requested limit or default to 10 if not specified
            display_limit = requested_limit if limit_match else 10
            
            # Inject Corpus Discovery Hint
            from tools.search_docs import get_available_titles
            inventory = get_available_titles()
            inventory_hint = f"\n\n[LOCAL CORPUS INVENTORY]: {inventory}\n(Note: These movies have detailed unstructured reviews available. Use search_docs for these.)"

            if total_rows > display_limit:
                hidden_rows = total_rows - display_limit
                df = df.head(display_limit)
                results_markdown = df.to_markdown(index=False)
                return f"{results_markdown}\n\n*Result: {total_rows} rows found ({display_limit} shown, {hidden_rows} hidden for brevity).* \n[ADVICE]: If you need more than {display_limit} rows, use 'OFFSET' to paginate or refine your query.{inventory_hint}"
                 
            return df.to_markdown(index=False) + f"\n\n*Result: {total_rows} rows found (End of dataset reached).*{inventory_hint}"
            
        except Exception as e:
            return f"Error executing SQL query: {str(e)}"

# Convenience wrapper
_query_tool_instance = None
def query_data(sql_query: str) -> str:
    """
    Structured query execution over the movies database.
    Use this to answer questions requiring precise numerical extraction, comparisons, structured filtering, or aggregations (e.g. box office gross, ratings).
    """
    global _query_tool_instance
    if _query_tool_instance is None:
        _query_tool_instance = QueryDataTool()
    return _query_tool_instance.query(sql_query)
