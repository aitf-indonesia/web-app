-- Migration: Change image storage from file path to base64
-- Date: 2025-12-14

-- 1. Alter generated_domains table
-- Change image_path (text) to image_base64 (text)
ALTER TABLE public.generated_domains 
RENAME COLUMN image_path TO image_base64;

COMMENT ON COLUMN public.generated_domains.image_base64 IS 'Base64 encoded screenshot image';

-- 2. Alter object_detection table  
-- Change image_detected_path (varchar(512)) to image_detected_base64 (text)
ALTER TABLE public.object_detection 
RENAME COLUMN image_detected_path TO image_detected_base64;

ALTER TABLE public.object_detection 
ALTER COLUMN image_detected_base64 TYPE text;

COMMENT ON COLUMN public.object_detection.image_detected_base64 IS 'Base64 encoded detected object image';

-- Note: Existing data will need to be converted from file paths to base64
-- This can be done via a separate data migration script if needed
