import pandas as pd
import sqlite3
import os

def ingest_structured_data(csv_path, db_path):
    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} not found.")
        return
        
    print(f"Loading {csv_path}...")
    df = pd.read_csv(csv_path)
    
    # We will rename columns to be more SQL friendly before inserting
    # Title, Year, Genre, budget, opening weekend, worldwide gross, Rotten Tomatoes score
    df.columns = ["title", "year", "genre", "budget", "opening_weekend", "worldwide_gross", "rotten_tomatoes_score"]
    
    # Ensure directory exists if there is a dirname
    db_dir = os.path.dirname(db_path)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
    
    print(f"Connecting to SQLite DB at {db_path}...")
    conn = sqlite3.connect(db_path)
    
    print("Writing to 'movies' table...")
    # overwrite if exists
    df.to_sql('movies', conn, if_exists='replace', index=False)
    
    # Verify
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM movies")
    count = cursor.fetchone()[0]
    
    conn.close()
    
    print(f"Successfully ingested {count} rows into the 'movies' table.")

if __name__ == "__main__":
    CSV_PATH = os.path.join("..", "dataset", "movies_structured.csv")
    DB_PATH = "database.db"
    
    # Change to data directory so relative paths work from the script location
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    ingest_structured_data(CSV_PATH, DB_PATH)
