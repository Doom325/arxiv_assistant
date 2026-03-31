from sqlalchemy import create_engine, text
from config import settings

def migrate():
    print("🚀 Starting multi-embedding schema migration...")
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as conn:
        # Create prompt_templates table
        print("Creating prompt_templates table...")
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS prompt_templates (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                template_text TEXT NOT NULL,
                version_tag VARCHAR(50),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(name, version_tag)
            );
        """))
        
        # Create paper_embeddings table with vector(3072) and JSONB constraints
        print("Creating paper_embeddings table...")
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS paper_embeddings (
                id SERIAL PRIMARY KEY,
                paper_id INTEGER REFERENCES papers(id) ON DELETE CASCADE,
                prompt_template_id INTEGER REFERENCES prompt_templates(id),
                embedding VECTOR(3072) NOT NULL,
                embedding_config JSONB NOT NULL,
                embedding_metadata JSONB NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                modified_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                
                CONSTRAINT check_embedding_config_keys CHECK (
                    embedding_config ? 'purpose'
                ),
                CONSTRAINT check_metadata_keys CHECK (
                    embedding_metadata ? 'source_model'
                )
            );
        """))
        
        # Create indices
        print("Creating indices...")
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_paper_embeddings_paper_id ON paper_embeddings(paper_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_paper_embeddings_prompt_id ON paper_embeddings(prompt_template_id);"))
        
        conn.commit()
    print("✅ Migration complete!")

if __name__ == "__main__":
    migrate()
