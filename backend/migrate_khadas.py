
import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def migrate_khadas():
    conn = psycopg2.connect("postgresql://user:password@192.168.1.49:5434/arxiv_db")
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()

    print("Checking and adding missing columns to 'papers'...")
    cols_to_add = [
        ("is_downloaded", "BOOLEAN DEFAULT FALSE"),
        ("extracted_abstract", "TEXT"),
        ("extracted_introduction", "TEXT"),
        ("abstract_embedding", "VECTOR(768)"), # Khadas uses 768 for old compat, but we might want 3072 later
        ("introduction_embedding", "VECTOR(768)")
    ]
    
    for col, ctype in cols_to_add:
        try:
            cur.execute(f"ALTER TABLE papers ADD COLUMN {col} {ctype};")
            print(f"Added column {col} to papers.")
        except Exception as e:
            if "already exists" in str(e):
                print(f"Column {col} already exists.")
            else:
                print(f"Error adding {col}: {e}")

    print("Checking and adding missing columns to 'user_library'...")
    try:
        cur.execute("ALTER TABLE user_library ADD COLUMN list_name VARCHAR(255) DEFAULT 'Main';")
        print("Added column list_name to user_library.")
    except Exception as e:
        if "already exists" in str(e):
            print("Column list_name already exists.")
        else:
            print(f"Error adding list_name: {e}")

    print("Creating new tables for multi-embedding support...")
    try:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS prompt_templates (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                template_text TEXT NOT NULL,
                version_tag VARCHAR(50),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(name, version_tag)
            );
        """)
        print("Created table prompt_templates.")
    except Exception as e:
        print(f"Error creating prompt_templates: {e}")

    try:
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS paper_embeddings (
                id SERIAL PRIMARY KEY,
                paper_id INTEGER REFERENCES papers(id) ON DELETE CASCADE,
                prompt_template_id INTEGER REFERENCES prompt_templates(id),
                embedding VECTOR(3072) NOT NULL,
                embedding_config JSONB NOT NULL, 
                embedding_metadata JSONB NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                modified_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """)
        print("Created table paper_embeddings.")
    except Exception as e:
        print(f"Error creating paper_embeddings: {e}")

    cur.close()
    conn.close()
    print("Migration complete.")

if __name__ == "__main__":
    migrate_khadas()
