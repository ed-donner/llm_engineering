"""
Database Setup Script for Real-Time Call Center AI Architecture

This script creates the PostgreSQL database and the meeting_transcripts table
for the live audio-to-text transcription system.
"""

import os
import psycopg2
from dotenv import load_dotenv

load_dotenv(override=True)

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'andela_ai_engineering_bootcamp')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD')

# SQL to create the meeting_transcripts table
CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS meeting_transcripts (
    id SERIAL PRIMARY KEY,                       -- Unique identifier
    call_id UUID NOT NULL,                       -- Associated call or meeting ID
    title VARCHAR(255),                          -- Meeting title or subject
    original_text TEXT,                          -- Raw audio converted text (initial ASR output)
    cleaned_text TEXT,                           -- Post-processed / corrected transcript
    speaker VARCHAR(100),                        -- Speaker label (Speaker 1, Speaker 2, etc.)
    chunk_index INT,                             -- Sequence number for partial transcripts
    start_time TIMESTAMP,                        -- Start timestamp of this chunk
    end_time TIMESTAMP,                          -- End timestamp of this chunk
    duration_seconds FLOAT,                       -- Duration of this chunk (end_time - start_time)
    transcribed_at TIMESTAMP DEFAULT NOW(),      -- When transcription occurred
    llm_summary JSONB,                           -- Optional: LLM summary / action items for this chunk
    is_final BOOLEAN DEFAULT FALSE,              -- Marks final transcript after full processing
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_call_id ON meeting_transcripts(call_id);
CREATE INDEX IF NOT EXISTS idx_transcribed_at ON meeting_transcripts(transcribed_at);
CREATE INDEX IF NOT EXISTS idx_speaker ON meeting_transcripts(speaker);
CREATE INDEX IF NOT EXISTS idx_chunk_index ON meeting_transcripts(call_id, chunk_index);
"""


def create_table():
    """Create the meeting_transcripts table."""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        cursor = conn.cursor()
        
        # Execute the table creation SQL
        cursor.execute(CREATE_TABLE_SQL)
        conn.commit()
        
        print("✅ Table 'meeting_transcripts' created successfully.")
        print("✅ Indexes created successfully.")
        
        # Verify table creation
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'meeting_transcripts'
            ORDER BY ordinal_position;
        """)
        
        columns = cursor.fetchall()
        print("\n📋 Table structure:")
        for col_name, col_type in columns:
            print(f"   - {col_name}: {col_type}")
        
        cursor.close()
        conn.close()
        
    except psycopg2.Error as e:
        print(f"❌ Error creating table: {e}")
        raise


def main():
    """Main function to set up the database."""
    print("🚀 Setting up database for Real-Time Call Center AI Architecture...\n")
    
    try:
        # Create table (database already exists)
        create_table()
        
        print("\n✨ Database setup completed successfully!")
        print("\n📝 Next steps:")
        print("   1. Configure your environment variables (.env file)")
        print("   2. Start the FastAPI server")
        print("   3. Start the streaming processing workers")
        print("   4. Launch the React frontend")
        
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        print("\n💡 Make sure PostgreSQL is running and credentials are correct.")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
