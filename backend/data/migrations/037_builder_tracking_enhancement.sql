-- Migration 037: Builder Tracking Enhancement
-- Goal: Add current_submodule and last_update columns for better execution visibility.

ALTER TABLE builder_tasks ADD COLUMN current_submodule TEXT;
ALTER TABLE builder_tasks ADD COLUMN last_update REAL;

ALTER TABLE builder_modules ADD COLUMN current_submodule TEXT;
ALTER TABLE builder_modules ADD COLUMN last_update REAL;
