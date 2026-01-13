-- Change config_id from INTEGER to TEXT to store config names instead of numeric IDs
-- Clear existing data first since we're changing the data type and semantic meaning
DELETE FROM pages;

-- Now alter the column type
ALTER TABLE pages ALTER COLUMN config_id TYPE TEXT;
