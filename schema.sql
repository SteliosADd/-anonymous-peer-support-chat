-- ============================================================
-- MindSpace — MySQL database setup
--
-- Run this once before starting the app:
--    mysql -u root -p < schema.sql
--
-- It creates the `mindspace` database and a dedicated user with
-- the password used in `.env.example`. Change the password in
-- production!
-- ============================================================

-- Create the database (utf8mb4 lets us store emoji avatars cleanly).
CREATE DATABASE IF NOT EXISTS mindspace
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

-- Create a dedicated app user. Change the password before deploying!
CREATE USER IF NOT EXISTS 'mindspace'@'localhost' IDENTIFIED BY 'mindspace_pass';
CREATE USER IF NOT EXISTS 'mindspace'@'%' IDENTIFIED BY 'mindspace_pass';

-- Grant only the privileges the app needs.
GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, ALTER, INDEX, REFERENCES
    ON mindspace.* TO 'mindspace'@'localhost';
GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, ALTER, INDEX, REFERENCES
    ON mindspace.* TO 'mindspace'@'%';

FLUSH PRIVILEGES;

-- The actual tables (users, messages) are created automatically by
-- SQLAlchemy on first run via `db.create_all()` — no DDL needed here.

SELECT 'MindSpace database ready ✅' AS status;
