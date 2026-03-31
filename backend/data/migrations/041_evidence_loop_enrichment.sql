-- Migration 041: Evidence Loop Enrichment
-- Goal: Add reasoning and trigger columns to builder_patch_previews.

ALTER TABLE builder_patch_previews ADD COLUMN reasoning TEXT;
ALTER TABLE builder_patch_previews ADD COLUMN trigger TEXT;
