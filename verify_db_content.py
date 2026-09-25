
import sqlite3
import pandas as pd
import json

DB_PATH = "judicial_ai.db"

def view_database():
    print(f"\n📂 Opening Database: {DB_PATH}")
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 1. Check Tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"\n📊 Found Tables: {[t[0] for t in tables]}")
        
        # 2. View Judgments
        print("\n" + "="*50)
        print("📝 JUDGMENTS TABLE")
        print("="*50)
        df_judgments = pd.read_sql_query("SELECT * FROM judgments", conn)
        if not df_judgments.empty:
            print(df_judgments.to_string(index=False))
        else:
            print("No judgments found.")

        # 3. View Analyses
        print("\n" + "="*50)
        print("🧠 ANALYSES TABLE")
        print("="*50)
        df_analyses = pd.read_sql_query("SELECT id, judgment_id, summary, created_at FROM analyses", conn)
        if not df_analyses.empty:
            # Truncate summary for display
            df_analyses['summary'] = df_analyses['summary'].apply(lambda x: x[:50] + "..." if x else "N/A")
            print(df_analyses.to_string(index=False))
        else:
            print("No analyses found.")
            
        conn.close()
        
    except Exception as e:
        print(f"❌ Error reading database: {e}")

if __name__ == "__main__":
    try:
        # Check if pandas is installed
        import pandas
        view_database()
    except ImportError:
        print("Pandas not installed. Installing...")
        import os
        os.system("pip install pandas")
        view_database()
