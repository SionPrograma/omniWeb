-- OMNI_MODE_PERSISTENCE_V1.2: Persistent User Mode
ALTER TABLE users ADD COLUMN mode TEXT;

-- Seed existing users with their default modes based on V1.0 rules
UPDATE users SET mode = 'CREATOR' WHERE username = 'admin' OR role = 'creator';
UPDATE users SET mode = 'ADMIN' WHERE role = 'admin' AND username != 'admin';
UPDATE users SET mode = 'TESTER' WHERE role = 'tester';
UPDATE users SET mode = 'PUBLIC' WHERE mode IS NULL;
