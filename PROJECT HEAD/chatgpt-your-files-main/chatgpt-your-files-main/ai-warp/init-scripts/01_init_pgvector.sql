-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create pages table with vector support
CREATE TABLE IF NOT EXISTS pages (
  id SERIAL PRIMARY KEY,
  url TEXT NOT NULL,
  html_content TEXT,
  text_content TEXT,
  embedding vector(1536),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create index on the embedding column for faster similarity search
CREATE INDEX IF NOT EXISTS idx_pages_embedding ON pages USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Create a function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS init-scripts
BEGIN
  NEW.updated_at = CURRENT_TIMESTAMP;
  RETURN NEW;
END;
init-scripts LANGUAGE plpgsql;

-- Create a trigger to automatically update updated_at
CREATE TRIGGER update_pages_updated_at
BEFORE UPDATE ON pages
FOR EACH ROW
EXECUTE FUNCTION update_updated_at();
