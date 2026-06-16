-- ============================================================
-- Anonymous Mental Health Support Chat — MySQL database setup
--
-- Run this once before starting the app:
--    mysql -u root -p < schema.sql
--
-- It creates the `support_chat` database and a dedicated user
-- with the password used in `.env.example`. Change the password
-- in production!
-- ============================================================

-- Create the database (utf8mb4 lets us store emoji avatars cleanly).
CREATE DATABASE IF NOT EXISTS support_chat
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

-- Create a dedicated app user. Change the password before deploying!
CREATE USER IF NOT EXISTS 'support_chat'@'localhost' IDENTIFIED BY 'support_chat_pass';
CREATE USER IF NOT EXISTS 'support_chat'@'%' IDENTIFIED BY 'support_chat_pass';

-- Grant only the privileges the app needs.
GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, ALTER, INDEX, REFERENCES
    ON support_chat.* TO 'support_chat'@'localhost';
GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, ALTER, INDEX, REFERENCES
    ON support_chat.* TO 'support_chat'@'%';

FLUSH PRIVILEGES;

-- The actual tables (users, messages) are created automatically by
-- SQLAlchemy on first run via `db.create_all()` — no DDL needed here.

SELECT 'Database ready ✅' AS status;
