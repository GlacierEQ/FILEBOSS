-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create pages table with vector support
CREATE TABLE IF NOT EXISTS pages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  url TEXT NOT NULL,
  html_content TEXT,
  text_content TEXT,
  embedding vector(1536),
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- Add URL index
CREATE INDEX IF NOT EXISTS idx_pages_url ON pages (url);

-- Enable Row Level Security
ALTER TABLE pages ENABLE ROW LEVEL SECURITY;

-- Create RLS policies
CREATE POLICY "Allow anonymous SELECT" ON pages
  FOR SELECT
  TO anon
  USING (true);

CREATE POLICY "Allow authenticated INSERT/UPDATE" ON pages
  FOR ALL
  TO authenticated
  USING (true)
  WITH CHECK (true);

-- Function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS supabase\migrations
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
supabase\migrations LANGUAGE plpgsql;

-- Trigger to update the updated_at timestamp
CREATE TRIGGER update_pages_updated_at
BEFORE UPDATE ON pages
FOR EACH ROW
EXECUTE FUNCTION update_updated_at();

-- Function to generate embeddings (will be called from Edge Functions)
CREATE OR REPLACE FUNCTION generate_embedding()
RETURNS VOID AS supabase\migrations
BEGIN
  -- This is a placeholder - actual implementation will be in Edge Functions
  RAISE NOTICE 'Generating embeddings for new pages...';
END;
supabase\migrations LANGUAGE plpgsql;
