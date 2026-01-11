-- Migration: Create events table
-- Description: Add events table with relationship to pages

CREATE TABLE IF NOT EXISTS events (
    event_id SERIAL PRIMARY KEY,
    page_id INTEGER NOT NULL REFERENCES pages(page_id) ON DELETE CASCADE,
    
    -- iCalendar fields
    uid TEXT,
    dtstamp TEXT,
    dtstart TEXT,
    dtend TEXT,
    duration TEXT,
    summary TEXT,
    description TEXT,
    location TEXT,
    url TEXT,
    geo TEXT,
    categories JSONB,
    status TEXT,
    transp TEXT,
    sequence INTEGER,
    created TEXT,
    last_modified TEXT,
    organizer TEXT,
    attendees JSONB,
    attach JSONB,
    classification TEXT,
    priority INTEGER,
    rrule TEXT,
    rdate JSONB,
    exdate JSONB,
    recurrence_id TEXT,
    tzid TEXT,
    alarms JSONB,
    
    -- Raw and backward-compatible fields
    raw TEXT,
    title TEXT,
    start TEXT,
    
    -- Metadata fields
    extracted_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    extraction_version TEXT,
    is_valid BOOLEAN DEFAULT false NOT NULL,
    content_hash TEXT
);

-- Indexes for events table
CREATE INDEX IF NOT EXISTS idx_events_page_id ON events(page_id);
CREATE INDEX IF NOT EXISTS idx_events_dtstart ON events(dtstart);
CREATE INDEX IF NOT EXISTS idx_events_start ON events(start);
CREATE INDEX IF NOT EXISTS idx_events_title ON events(title);
CREATE INDEX IF NOT EXISTS idx_events_content_hash ON events(content_hash);
CREATE INDEX IF NOT EXISTS idx_events_is_valid ON events(is_valid);
CREATE INDEX IF NOT EXISTS idx_events_extracted_at ON events(extracted_at);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to automatically update updated_at
CREATE TRIGGER update_events_updated_at BEFORE UPDATE ON events
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
