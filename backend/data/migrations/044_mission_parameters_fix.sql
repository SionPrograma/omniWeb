-- Migration 044: Mission Parameters Persistence Fix
-- Goal: Ensure governance parameters and operational settings survive restarts.
-- This was a missing column causing save failures in MissionManager.

ALTER TABLE system_missions ADD COLUMN parameters TEXT;
