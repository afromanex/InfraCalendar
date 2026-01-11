-- Migrations table to track applied migrations
CREATE TABLE IF NOT EXISTS migrations (
    id SERIAL PRIMARY KEY,
    filename TEXT NOT NULL,
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    CONSTRAINT migrations_filename_key UNIQUE (filename)
);

-- Pages table to store crawled web pages
CREATE TABLE IF NOT EXISTS pages (
    page_id SERIAL PRIMARY KEY,
    page_url TEXT NOT NULL,
    page_content TEXT,
    http_status INTEGER,
    fetched_at TIMESTAMP WITH TIME ZONE,
    config_id INTEGER,
    plain_text TEXT,
    CONSTRAINT pages_page_url_key UNIQUE (page_url)
);

-- Indexes for pages table
CREATE INDEX IF NOT EXISTS idx_pages_config ON pages(config_id);
CREATE INDEX IF NOT EXISTS idx_pages_url ON pages(page_url);
CREATE INDEX IF NOT EXISTS idx_pages_plain_text ON pages USING gin(to_tsvector('english', COALESCE(plain_text, '')));
