-- Database Setup Script for Real-Time Call Center AI Architecture
-- PostgreSQL script to create the meeting_transcripts table

-- Create database (run this separately if needed)
-- Note: Using shared database 'andela_ai_engineering_bootcamp' for all training weeks
-- CREATE DATABASE andela_ai_engineering_bootcamp;

-- Connect to the database before running this script
-- \c andela_ai_engineering_bootcamp;

-- Create the meeting_transcripts table
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

-- Add a comment to the table
COMMENT ON TABLE meeting_transcripts IS 'Stores real-time transcription chunks from live audio calls with speaker diarization and LLM summaries';

-- Add comments to key columns
COMMENT ON COLUMN meeting_transcripts.call_id IS 'UUID identifying the call/meeting session';
COMMENT ON COLUMN meeting_transcripts.original_text IS 'Raw transcription from ASR (Automatic Speech Recognition)';
COMMENT ON COLUMN meeting_transcripts.cleaned_text IS 'Post-processed and corrected transcript';
COMMENT ON COLUMN meeting_transcripts.speaker IS 'Speaker label from diarization (e.g., Speaker 1, Speaker 2)';
COMMENT ON COLUMN meeting_transcripts.llm_summary IS 'JSON object containing LLM-generated summary, action items, and intent detection';
COMMENT ON COLUMN meeting_transcripts.is_final IS 'Marks whether this is the final processed transcript chunk';
