CREATE EXTENSION IF NOT EXISTS vector;

DROP TABLE IF EXISTS chunks;

-- Create chunks table for storing article chunks and embeddings
CREATE TABLE IF NOT EXISTS chunks (
  chunk_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  chunk_text TEXT NOT NULL,
  chunk_embedding vector(1536) NOT NULL,
  entity_names TEXT[] NOT NULL DEFAULT '{}',
  article_id text NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create HNSW index for efficient vector similarity search

CREATE INDEX IF NOT EXISTS chunks_embedding_hnsw_idx 
ON chunks USING hnsw (chunk_embedding vector_cosine_ops);

-- Optional: Create index on entity_names for filtering
CREATE INDEX IF NOT EXISTS chunks_entity_names_idx 
ON chunks USING GIN (entity_names);

-- Comment on table and columns
COMMENT ON TABLE chunks IS 'Stores chunked article text with embeddings for RAG system';
COMMENT ON COLUMN chunks.chunk_id IS 'Unique identifier for each chunk';
COMMENT ON COLUMN chunks.chunk_text IS 'The actual text content of the article chunk';
COMMENT ON COLUMN chunks.chunk_embedding IS 'OpenAI embedding vector (1536 dimensions)';
COMMENT ON COLUMN chunks.entity_names IS 'Array of company/entity names mentioned in chunk';
COMMENT ON COLUMN chunks.article_id IS 'Identifier for the source article';
COMMENT ON COLUMN chunks.created_at IS 'Timestamp when chunk was created';