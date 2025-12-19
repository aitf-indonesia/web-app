-- Migration: Fix image_final_path column size
-- Date: 2025-12-19
-- Issue: StringDataRightTruncation error when inserting base64 images
-- 
-- Error: value too long for type character varying(512)
-- Solution: Change image_final_path from VARCHAR(512) to TEXT
--
-- Background:
-- The crawler saves base64-encoded images which can be 50,000+ characters long.
-- The original VARCHAR(512) limit was too small and caused insertion failures.

-- Change column type to TEXT (unlimited length)
ALTER TABLE results ALTER COLUMN image_final_path TYPE TEXT;

-- Verify the change
\d results
