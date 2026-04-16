import sqlite3
import os
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

            conn = sqlite3.connect(self.db_path)
            
            # Use pandas to nicely format the tabular output for the LLM
            df = pd.read_sql_query(sql_query, conn)
            conn.close()
            
            if df.empty:
                return "Query executed successfully but returned no results."
                
            # TRUNCATION OPTIMIZATION: Max 10 rows returned to prevent LLM context 8k limit overflow 
            if len(df) > 10:
                df = df.head(10)
                return df.to_markdown(index=False) + "\n\n...(Output truncated to first 10 rows for brevity limit)."
                
            return df.to_markdown(index=False)
            
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
